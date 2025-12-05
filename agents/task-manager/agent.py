"""
Task Manager Agent - Traduce obiettivi in task concreti.
Usa la Lambda POST per memorizzare task nel database.
Usa Bedrock AgentCore con Strands Agents.
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.context import RequestContext
from strands import Agent, function_tool
import json
import os
import logging
from typing import Dict, Any, List
import sys
from datetime import datetime, timedelta

# Add parent directory to path for gateway_client import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from gateway_client import get_gateway_client

# Setup logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize BedrockAgentCore app
app = BedrockAgentCoreApp()


# Tool per salvare task nel database tramite Gateway
@function_tool
def save_tasks_to_database(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Salva task nel database DynamoDB tramite AgentCore Gateway.
    
    Args:
        tasks: Lista di task da salvare. Ogni task deve avere:
            - title (required): Titolo del task
            - description: Descrizione dettagliata
            - due_date: Scadenza (formato YYYY-MM-DD)
            - priority: low, medium, high, urgent
            - category: work, learning, health, personal, general
            - tags: lista di tag
    
    Returns:
        Risultato dell'operazione con numero di task creati
    """
    try:
        # Get Gateway client from environment variables
        gateway = get_gateway_client()
        
        # Call save_task tool through Gateway
        # The Gateway target will invoke the Lambda POST function
        result = gateway.call_tool(
            tool_name="save_task",
            arguments={'tasks': tasks}
        )
        
        logger.info(f"✅ Saved {result.get('created_count', 0)} tasks via Gateway")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error saving tasks via Gateway: {e}")
        return {"error": str(e), "created_count": 0}


# Create Strands Agent
agent = Agent(
    model="anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[save_tasks_to_database],
    system_prompt="""Sei un Task Manager intelligente che decompone obiettivi in task actionable.
    
    Il tuo compito è:
    1. Ricevere obiettivi dall'utente in linguaggio naturale
    2. Analizzare l'obiettivo e decomporlo in task SMART:
       - Specific: chiaro e specifico
       - Measurable: misurabile
       - Achievable: raggiungibile
       - Relevant: rilevante
       - Time-bound: con scadenza
    3. Per ogni task, definire:
       - title: titolo chiaro e conciso (max 100 caratteri)
       - description: descrizione dettagliata con steps concreti
       - due_date: scadenza realistica (formato YYYY-MM-DD)
       - priority: low, medium, high, urgent (considera la sequenza e dipendenze)
       - category: work, learning, health, personal, general
       - tags: 1-3 tag rilevanti (es: python, fitness, project)
    4. Usare il tool save_tasks_to_database per salvare tutti i task
    5. Confermare all'utente i task creati in formato friendly
    
    ESEMPI DI DECOMPOSIZIONE:
    
    📘 Obiettivo: "Imparare Python entro 3 mesi"
    Task:
    1. Setup ambiente Python (settimana 1)
       - Installare Python, VS Code, creare primo script
       - Priority: high, Category: learning
    2. Completare corso base (mese 1)
       - Studiare variabili, funzioni, loop, liste
       - Priority: high, Category: learning
    3. Progetto pratico (mese 2)
       - Sviluppare app CLI o script automation
       - Priority: medium, Category: learning
    4. Review e consolidamento (mese 3)
       - Rivedere concetti, ottimizzare progetto
       - Priority: medium, Category: learning
    
    💪 Obiettivo: "Andare in palestra 3 volte a settimana"
    Task:
    1. Iscriversi in palestra (settimana 1)
    2. Prima settimana: 2 allenamenti leggeri
    3. Seconda settimana: 3 allenamenti con trainer
    4. Mese 1: mantenere routine 3x/settimana
    
    📱 Obiettivo: "Sviluppare app mobile"
    Task:
    1. Planning e wireframe (settimana 1)
    2. Setup progetto React Native (settimana 1)
    3. Sviluppo MVP (4 settimane)
    4. Testing beta (2 settimane)
    5. Deploy store (settimana 8)
    
    LINEE GUIDA:
    - Crea 3-6 task per obiettivo (non troppi, non troppo pochi)
    - Dividi obiettivi grandi in milestone intermedie
    - Assegna scadenze realistiche e progressive
    - I primi task devono essere "quick wins" per motivare
    - Usa priority per indicare l'ordine di esecuzione
    - Sii specifico nelle descrizioni (no generici "studiare X")
    
    Dopo aver salvato i task, conferma con un messaggio motivante in italiano!
    """
)


@app.entrypoint
def invoke(payload: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
    """
    Entrypoint per BedrockAgentCore Task Manager.
    """
    try:
        objective = payload.get("prompt") or payload.get("objective", "")
        user_id = payload.get("user_id", "unknown")
        session_id = context.session_id or f"task-{user_id}"
        
        logger.info(f"Processing objective from user {user_id}: {objective}")
        
        # Invoca agente Strands
        result = agent(objective)
        
        return {
            "result": result.message,
            "user_id": user_id,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error in task manager: {e}", exc_info=True)
        return {
            "error": str(e),
            "result": "Mi dispiace, non sono riuscito a creare i task. Riprova con un obiettivo più chiaro."
        }


if __name__ == "__main__":
    # Avvia server locale per testing
    app.run()
