"""
Daily Briefing Agent - Genera riassunto giornaliero degli impegni.
Legge task dal database (GET) e email da Outlook (tramite MCP).
Usa Bedrock AgentCore con Strands Agents.
Usa AgentCore Gateway per accesso sicuro alle Lambda.
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.context import RequestContext
from strands import Agent, function_tool
import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import sys
import requests

# Add parent directory to path for gateway_client import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from gateway_client import get_gateway_client

# Setup logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize BedrockAgentCore app
app = BedrockAgentCoreApp()

# Environment variables
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL')
MCP_API_KEY = os.environ.get('MCP_API_KEY')


# Tools per Daily Briefing
@function_tool
def get_tasks_from_database(date_filter: str = "today", status: str = "pending,in_progress") -> List[Dict[str, Any]]:
    """
    Recupera task dal database DynamoDB tramite AgentCore Gateway.
    
    Args:
        date_filter: Filtro temporale - today, tomorrow, week, month
        status: Status dei task (comma-separated) - pending, in_progress, completed
    
    Returns:
        Lista di task con tutti i dettagli
    """
    try:
        # Get Gateway client from environment variables
        gateway = get_gateway_client()
        
        # Call get_tasks tool through Gateway
        # The Gateway target will invoke the Lambda GET function
        result = gateway.call_tool(
            tool_name="get_tasks",
            arguments={
                'due_date': date_filter,
                'status': status,
                'limit': '50'
            }
        )
        
        tasks = result.get('tasks', [])
        logger.info(f"✅ Retrieved {len(tasks)} tasks via Gateway")
        return tasks
        
    except Exception as e:
        logger.error(f"❌ Error fetching tasks via Gateway: {e}")
        return []


@function_tool
def get_emails_from_outlook(max_results: int = 10, only_unread: bool = True) -> List[Dict[str, Any]]:
    """
    Recupera email importanti da Outlook tramite MCP server.
    
    Args:
        max_results: Numero massimo di email da recuperare
        only_unread: Se True, recupera solo email non lette
    
    Returns:
        Lista di email con subject, sender, data
    """
    try:
        if not MCP_SERVER_URL or not MCP_API_KEY:
            logger.warning("MCP server not configured")
            return []
        
        headers = {
            'Authorization': f'Bearer {MCP_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'tool': 'outlook_get_emails',
            'parameters': {
                'folder': 'inbox',
                'max_results': max_results,
                'filter': {'isRead': not only_unread}
            }
        }
        
        response = requests.post(
            f'{MCP_SERVER_URL}/tools/invoke',
            json=payload,
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        emails = data.get('result', {}).get('emails', [])
        
        logger.info(f"Retrieved {len(emails)} emails")
        return emails
        
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return []


# Create Strands Agent
agent = Agent(
    model="anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[get_tasks_from_database, get_emails_from_outlook],
    system_prompt="""Sei un Daily Briefing Agent che genera riassunti giornalieri professionali.
    
    Il tuo compito è:
    1. Usare get_tasks_from_database per recuperare task del giorno
    2. Usare get_emails_from_outlook per recuperare email importanti
    3. Analizzare task ed email per identificare priorità e urgenze
    4. Generare un briefing conciso e actionable in formato Markdown
    
    STRUTTURA BRIEFING:
    
    🌅 **Briefing - [Data]**
    _{data completa formattata}_
    
    📋 **Task in Programma:** ({numero} task)
    
    🔴 **Urgente/Alta Priorità:**
    • {titolo task} - ⏰ Scadenza: {due_date}
      📝 {breve descrizione o note importanti}
    
    🟢 **Normale:**
    • {titolo task}
    • {titolo task}
    
    📧 **Email Importanti:** ({numero} non lette)
    • {subject} - 👤 {sender name}
    • {subject} - 👤 {sender name}
    
    💡 **Suggerimenti:**
    • [Suggerimenti intelligenti basati su carico lavoro, scadenze, ecc]
    
    ---
    _Comandi utili:_
    • /tasks - Vedi tutti i task
    • /add <obiettivo> - Aggiungi nuovi task
    
    LINEE GUIDA:
    - Ordina task per priorità (urgent/high prima)
    - Per task urgenti, mostra anche la scadenza
    - Raggruppa task simili se possibile
    - Se ci sono troppe email (>5), mostra solo le più importanti
    - Fornisci suggerimenti actionable:
      * "⚠️ Hai {N} task urgenti, considera di riprogrammarne alcuni"
      * "✨ Giornata leggera! Buon momento per pianificare nuovi obiettivi"
      * "📅 Scadenza importante tra {X} giorni: {task}"
      * "💪 Ottimo lavoro! Hai completato {N} task questa settimana"
    - Se non ci sono task, incoraggia l'utente a pianificare
    - Se non ci sono email, menzionalo brevemente
    - Usa emoji per rendere più leggibile (ma non esagerare)
    - Tono professionale ma amichevole
    - Lingua: italiano
    
    Il briefing deve essere CONCISO ma COMPLETO. Max 15-20 righe.
    """
)


@app.entrypoint
def invoke(payload: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
    """
    Entrypoint per BedrockAgentCore Daily Briefing.
    """
    try:
        prompt = payload.get("prompt") or "Dammi il briefing di oggi"
        user_id = payload.get("user_id", "unknown")
        date_filter = payload.get("date_filter", "today")
        session_id = context.session_id or f"briefing-{user_id}"
        
        logger.info(f"Generating briefing for user {user_id}")
        
        # Invoca agente Strands
        result = agent(prompt)
        
        return {
            "result": result.message,
            "user_id": user_id,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error in daily briefing: {e}", exc_info=True)
        return {
            "error": str(e),
            "result": "Mi dispiace, non sono riuscito a generare il briefing. Riprova più tardi."
        }


if __name__ == "__main__":
    # Avvia server locale per testing
    app.run()
