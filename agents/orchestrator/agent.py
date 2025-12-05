"""
Orchestrator Agent - Agente principale che coordina gli altri agenti.
Riceve messaggi da Telegram e invoca l'agente appropriato.
Usa Bedrock AgentCore con Strands Agents.
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.context import RequestContext
from strands import Agent, function_tool
import json
import os
import logging
from typing import Dict, Any
import boto3
import uuid

# Setup logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize BedrockAgentCore app
app = BedrockAgentCoreApp()

# Short-term memory: in-memory session storage (conversation history)
# In production, use DynamoDB or AgentCore Memory
sessions = {}

# AWS clients for invoking other agents
agent_core_client = boto3.client('bedrock-agentcore')

# Environment variables - ARNs degli altri agenti
TASK_MANAGER_AGENT_ARN = os.environ.get('TASK_MANAGER_AGENT_ARN')
DAILY_BRIEFING_AGENT_ARN = os.environ.get('DAILY_BRIEFING_AGENT_ARN')


# Define tools per invocare gli altri agenti
@function_tool
def invoke_task_manager(objective: str, user_id: str) -> Dict[str, Any]:
    """
    Invoca il Task Manager Agent per creare task da obiettivi.
    
    Args:
        objective: L'obiettivo dell'utente da trasformare in task
        user_id: ID dell'utente
    
    Returns:
        Risposta con task creati
    """
    try:
        payload = json.dumps({
            "objective": objective,
            "user_id": user_id
        }).encode()
        
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=TASK_MANAGER_AGENT_ARN,
            runtimeSessionId=str(uuid.uuid4()),
            payload=payload,
            qualifier="DEFAULT"
        )
        
        content = []
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        
        result = json.loads(''.join(content))
        logger.info(f"Task Manager response: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error invoking Task Manager: {e}")
        return {"error": str(e), "message": "Errore nel creare task"}


@function_tool
def invoke_daily_briefing(user_id: str, date_filter: str = "today") -> Dict[str, Any]:
    """
    Invoca il Daily Briefing Agent per riassunto giornaliero.
    
    Args:
        user_id: ID dell'utente
        date_filter: Filtro temporale (today, tomorrow, week)
    
    Returns:
        Briefing con task ed email
    """
    try:
        payload = json.dumps({
            "user_id": user_id,
            "date_filter": date_filter
        }).encode()
        
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=DAILY_BRIEFING_AGENT_ARN,
            runtimeSessionId=str(uuid.uuid4()),
            payload=payload,
            qualifier="DEFAULT"
        )
        
        content = []
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        
        result = json.loads(''.join(content))
        logger.info(f"Daily Briefing response: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error invoking Daily Briefing: {e}")
        return {"error": str(e), "message": "Errore nel generare briefing"}


# Create Strands Agent con tools
agent = Agent(
    model="anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[invoke_task_manager, invoke_daily_briefing],
    system_prompt="""Sei l'Orchestrator, un assistente personale intelligente.
    
    Il tuo compito è:
    1. Analizzare le richieste dell'utente
    2. Decidere quale agente invocare:
       - invoke_task_manager: quando l'utente vuole creare task o descrive obiettivi
         (es: "voglio imparare Python", "devo fare...", "obiettivo: ...")
       - invoke_daily_briefing: quando l'utente chiede briefing o informazioni sui suoi impegni
         (es: "/briefing", "cosa devo fare oggi", "mostrami gli impegni")
    3. Fornire risposte chiare e amichevoli
    
    Per comandi semplici:
    - /start -> Messaggio di benvenuto
    - /help -> Lista comandi disponibili
    - Messaggi generali -> Risposta amichevole con suggerimenti
    
    Comunica sempre in italiano in modo conciso e amichevole.
    """
)


@app.entrypoint
def invoke(payload: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
    """
    Entrypoint per BedrockAgentCore con session management.
    Riceve messaggi e mantiene la storia della conversazione.
    """
    try:
        # Estrai messaggio e user_id dal payload
        message = payload.get("prompt") or payload.get("message", "")
        user_id = payload.get("user_id", "unknown")
        
        # Get session ID from context (provided by AgentCore Runtime)
        session_id = context.session_id or f"user-{user_id}"
        
        logger.info(f"Processing message from user {user_id}, session {session_id}: {message}")
        
        # Initialize session if new (short-term memory)
        if session_id not in sessions:
            sessions[session_id] = {
                "messages": [],
                "count": 0,
                "user_id": user_id
            }
        
        # Add message to session history
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": message
        })
        sessions[session_id]["count"] += 1
        
        # Build context-aware prompt with conversation history
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in sessions[session_id]["messages"][-5:]  # Last 5 messages
        ])
        
        context_message = f"""Conversazione precedente:
{history_text}

Nuovo messaggio utente: {message}"""
        
        # Invoca agente Strands con contesto
        result = agent(context_message)
        
        # Save assistant response to session
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": result.message
        })
        
        return {
            "result": result.message,
            "user_id": user_id,
            "session_id": session_id,
            "message_count": sessions[session_id]["count"]
        }
        
    except Exception as e:
        logger.error(f"Error in orchestrator: {e}", exc_info=True)
        return {
            "error": str(e),
            "result": "Mi dispiace, si è verificato un errore. Riprova."
        }


if __name__ == "__main__":
    # Avvia server locale per testing
    app.run()
