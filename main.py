import os
import smtplib
from email.message import EmailMessage
import asyncio
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    trace,
    function_tool,
    OpenAIChatCompletionsModel,
    input_guardrail,
    GuardrailFunctionOutput
)
from agents.exceptions import InputGuardrailTripwireTriggered
from guardrails import GuardrailAgent

@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Envoyer un e-mail avec l'objet et le corps HTML donnés à tous les prospects """
    mailtrap_username = os.getenv('MAILTRAP_USERNAME')
    mailtrap_password = os.getenv('MAILTRAP_PASSWORD')

    if not mailtrap_username or not mailtrap_password:
        return {"status": "error", "message": "Identifiants Mailtrap non configurés dans le .env"}

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "sales@complai.com"
    msg['To'] = "ceo@example.com"
    msg.set_content("Veuillez utiliser un client mail supportant le HTML pour lire ce message.")
    msg.add_alternative(html_body, subtype='html')

    try:
        with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
            server.starttls()
            server.login(mailtrap_username, mailtrap_password)
            server.send_message(msg)
        return {"status": "success", "message": "Email envoyé vers Mailtrap avec succès"}
    except Exception as e:
        return {"status": "error", "message": f"Erreur lors de l'envoi : {str(e)}"}




async def main():
    load_dotenv(override=True)

    openai_api_key = os.getenv('OPENAI_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    mailtrap_username = os.getenv('MAILTRAP_USERNAME')

    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")

    if google_api_key:
        print(f"Google API Key exists and begins {google_api_key[:2]}")
    else:
        print("Google API Key not set (and this is optional)")

    if mailtrap_username:
        print(f"Mailtrap Credentials exist (Username: {mailtrap_username})")
    else:
        print("Mailtrap Credentials not set (L'envoi des e-mails va échouer)")

    instructions1 = (
        "Vous êtes un agent de vente travaillant pour ComplAI, "
        "une entreprise qui fournit un outil SaaS pour assurer la conformité SOC2 et préparer les audits, propulsé par l'IA. "
        "Vous rédigez des e-mails de démarchage professionnels et sérieux."
    )

    instructions2 = (
        "Vous êtes un agent de vente plein d'humour et captivant travaillant pour ComplAI, "
        "une entreprise qui fournit un outil SaaS pour assurer la conformité SOC2 et préparer les audits, propulsé par l'IA. "
        "Vous rédigez des e-mails de démarchage pleins d'esprit et engageants qui ont de grandes chances d'obtenir une réponse."
    )

    instructions3 = (
        "Vous êtes un agent de vente très occupé travaillant pour ComplAI, "
        "une entreprise qui fournit un outil SaaS pour assurer la conformité SOC2 et préparer les audits, propulsé par l'IA. "
        "Vous rédigez des e-mails de démarchage concis et allant droit au but."
    )

    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)

    gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash-lite", openai_client=gemini_client)

    sales_agent1 = Agent(name="Gemini Sales Agent", instructions=instructions1, model=gemini_model)
    sales_agent2 = Agent(name="Gemini Sales Agent", instructions=instructions2, model=gemini_model)
    sales_agent3 = Agent(name="Gemini Sales Agent", instructions=instructions3, model=gemini_model)

    description = "Rédiger un e-mail de démarchage commercial"

    tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
    tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
    tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)

    subject_instructions = (
        "Vous savez rédiger un objet pour un e-mail de démarchage commercial. "
        "On vous donne un message et vous devez écrire un objet d'e-mail qui a de grandes chances d'obtenir une réponse."
    )

    html_instructions = (
        "Vous savez convertir le corps d'un e-mail texte en un corps d'e-mail HTML. "
        "On vous donne un corps d'e-mail au format texte qui pourrait contenir du markdown "
        "et vous devez le convertir en HTML avec une mise en page et un design simples, clairs et attrayants."
    )

    subject_writer = Agent(name="Email subject writer", instructions=subject_instructions, model="gpt-4o-mini")
    subject_tool = subject_writer.as_tool(tool_name="subject_writer",
                                          tool_description="Rédiger un objet pour un e-mail de démarchage commercial")

    html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model="gpt-4o-mini")
    html_tool = html_converter.as_tool(tool_name="html_converter",
                                       tool_description="Convertir le corps d'un e-mail texte en HTML")

    email_tools = [subject_tool, html_tool, send_html_email]

    instructions = (
        "Vous êtes un formatteur et expéditeur d'e-mails. Vous recevez le corps d'un e-mail à envoyer. "
        "Vous utilisez d'abord l'outil subject_writer pour rédiger un objet pour l'e-mail, puis vous utilisez l'outil html_converter pour convertir le corps en HTML. "
        "Enfin, vous utilisez l'outil send_html_email pour envoyer l'e-mail avec l'objet et le corps HTML."
    )

    emailer_agent = Agent(
        name="Email Manager",
        instructions=instructions,
        tools=email_tools,
        model="gpt-4o-mini",
        handoff_description="Convertir un e-mail en HTML et l'envoyer"
    )

    tools = [tool1, tool2, tool3]
    handoffs = [emailer_agent]

    sales_manager_instructions = """
Vous êtes un directeur des ventes chez ComplAI. Votre objectif est de trouver le meilleur e-mail de démarchage commercial en utilisant les outils sales_agent.

Suivez ces étapes attentivement :
1. Générer des brouillons : Utilisez les trois outils sales_agent pour générer trois brouillons d'e-mails différents. Ne continuez pas tant que les trois brouillons ne sont pas prêts.

2. Évaluer et Sélectionner : Examinez les brouillons et choisissez le meilleur e-mail en utilisant votre jugement pour déterminer lequel est le plus efficace.
Vous pouvez utiliser les outils plusieurs fois si vous n'êtes pas satisfait des résultats du premier essai.

3. Passage de relais pour l'envoi : Transmettez UNIQUEMENT le brouillon d'e-mail gagnant à l'agent 'Email Manager'. L'Email Manager se chargera du formatage et de l'envoi.

Règles cruciales :
- Vous devez utiliser les outils sales agent pour générer les brouillons — ne les écrivez pas vous-même.
- Vous devez transférer exactement UN SEUL e-mail à l'Email Manager — jamais plus d'un.
"""

    message1 = "Envoyez un e-mail de démarchage commercial adressé à Cher PDG de la part d'Alice"

    careful_sales_manager = GuardrailAgent(
        config=Path("guardrails_config.json"),
        name="Sales Manager",
        instructions=sales_manager_instructions,
        tools=tools,
        handoffs=[emailer_agent],
        model="gpt-4o-mini"
    )

    print(f"\n--- Running Protected Automated SDR with message: {message1} ---")
    with trace("Protected Automated SDR"):
        try:
            result1 = await Runner.run(careful_sales_manager, message1, max_turns=25)
            print("Result:", result1)
        except InputGuardrailTripwireTriggered as exc:
            print("Message bloqué par le guardrail de nom (InputGuardrailTripwireTriggered). L'exécution continue.")

    message2 = "Envoyez un e-mail de démarchage commercial adressé à Cher PDG de la part du Directeur du Développement Commercial"

    print(f"\n--- Running Protected Automated SDR with message: {message2} ---")
    with trace("Protected Automated SDR"):
        try:
            result2 = await Runner.run(careful_sales_manager, message2, max_turns=25)
            print("Result:", result2)
        except InputGuardrailTripwireTriggered as exc:
            print("Message bloqué par le guardrail de nom (InputGuardrailTripwireTriggered). L'exécution continue.")


if __name__ == "__main__":
    asyncio.run(main())
