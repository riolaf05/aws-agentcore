"""
Orchestrator Agent - Coordina l'esecuzione di altri agenti specializzati.
Usa invoke_agent_runtime per delegare task specifici ad agenti dedicati.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from bedrock_agentcore.memory import MemoryClient

from hooks.short_memory_hook import ShortMemoryHook
from hooks.long_term_memory_hook import LongTermMemoryHook

from strands import Agent, tool
from strands.models import BedrockModel
import boto3
from hooks.memory import MemoryConfig, retrieve_memories_for_actor

DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Inizializza la configurazione della memoria e il client
memory_config = MemoryConfig()
memory_client = MemoryClient()

# Initialize Bedrock AgentCore client
agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# ARN degli agenti disponibili
AGENTS = {
    "task-writer": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/taskwriter-v5ts2W9Ghp",
    "task-reader": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/task_reader-aEBvIeHdvC",  
    "researcher": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/researcher-hGVInWG4SS",   
    "calculator": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/calculator-lgV0vpGtcq"
}

# Istanza agente verra creata in modo lazy quando necessario
agent = None

@tool
def retrieve_memories(query: str) -> List[Dict[str, Any]]:
    """Recupera i ricordi dal client della memoria usando una sintassi simile ad AWS CLI.
    
    Args:
        query: La query di ricerca per trovare ricordi rilevanti.
        
    Returns:
        Una lista di ricordi recuperati dal client della memoria.
    """
    actor_id = agent.state.get("actor_id")
    return retrieve_memories_for_actor(
        memory_id=memory_config.memory_id,
        actor_id=actor_id,
        search_query=query,
        memory_client=memory_client
    )

@tool
def invoke_agent(agent_name: str, prompt: str) -> str:
    """Invoca un agente specializzato con un prompt specifico.
    
    Args:
        agent_name: Nome dell'agente da invocare. Valori: task-writer, task-reader, researcher, calculator
        prompt: Il prompt da inviare all'agente
        
    Returns:
        La risposta dell'agente invocato
    """
    agent_arn = AGENTS.get(agent_name)
    
    if not agent_arn:
        logger.error(f"Agente '{agent_name}' non trovato")
        return f"Errore: Agente '{agent_name}' non disponibile. Agenti disponibili: {', '.join(AGENTS.keys())}"
    
    logger.info(f"Invocando agente '{agent_name}' con ARN: {agent_arn}")
    logger.debug(f"Prompt: {prompt}")
    
    try:
        # Genera session ID univoco
        session_id = str(uuid.uuid4())
        
        # Prepara payload
        payload_data = json.dumps({"prompt": prompt}).encode('utf-8')
        
        # Invoca l'agente
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,
            payload=payload_data
        )
        
        logger.info(f"Risposta ricevuta da '{agent_name}', contentType: {response.get('contentType')}")
        
        # Processa la risposta
        if "text/event-stream" in response.get("contentType", ""):
            # Handle streaming response
            content = []
            for line in response["response"].iter_lines(chunk_size=1024):
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    content.append(line_str)
            
            result = "\n".join(content)
            logger.debug(f"Risposta streaming da '{agent_name}': {result[:200]}...")
            return result
            
        elif response.get("contentType") == "application/json":
            # Handle standard JSON response
            content = []
            for chunk in response.get("response", []):
                content.append(chunk.decode('utf-8'))
            
            result_data = json.loads(''.join(content))
            
            # Gestisci sia dict che str
            if isinstance(result_data, dict):
                result = result_data.get('result', str(result_data))
            else:
                result = str(result_data)
            
            logger.debug(f"Risposta JSON da '{agent_name}': {result[:200]}...")
            return result
        
        else:
            # Raw response
            logger.warning(f"ContentType non gestito: {response.get('contentType')}")
            return str(response)
            
    except Exception as e:
        logger.error(f"Errore invocando agente '{agent_name}': {e}", exc_info=True)
        return f"Errore nell'invocazione dell'agente '{agent_name}': {str(e)}"


SYSTEM_PROMPT = """Sei un orchestratore intelligente che coordina diversi agenti specializzati.

I tuoi compiti sono:
1. Analizzare la richiesta dell'utente
2. Creare un piano di azione dettagliato
3. Identificare quali agenti specializzati servono per completare la richiesta
4. Invocare gli agenti appropriati nell'ordine corretto
5. Aggregare i risultati e fornire una risposta coerente

Agenti disponibili:
- **task-writer**: Crea e salva nuovi task nel database DynamoDB
  ARN: {task_writer_arn}
  
- **task-reader**: Legge e recupera task esistenti dal database
  ARN: {task_reader_arn}
  
- **researcher**: Cerca informazioni aggiornate su internet (regione: Italia)
  ARN: {researcher_arn}
  
- **calculator**: Esegue calcoli matematici e mantiene memoria delle operazioni
  ARN: {calculator_arn}

Processo di lavoro:
1. Quando ricevi una richiesta, prima PENSA e crea un piano passo-passo
2. Per ogni passo, identifica l'agente più adatto
3. Invoca gli agenti usando il tool invoke_agent
4. Usa i risultati di un agente come input per il successivo se necessario
5. Presenta i risultati finali in modo chiaro e organizzato

IMPORTANTE: Usa il tool invoke_agent per delegare il lavoro agli agenti specializzati.
Esempio: invoke_agent(agent_name="task-writer", prompt="Crea un task per comprare il latte")

Esempi di routing:
- "Crea un task per comprare il latte" → invoke_agent("task-writer", "...")
- "Mostrami i task con alta priorità" → invoke_agent("task-reader", "...")
- "Cerca informazioni sulla sicurezza in Python" → invoke_agent("researcher", "...")
- "Quanto fa 15 * 23?" → invoke_agent("calculator", "...")
- "Crea un task per studiare i risultati della ricerca su AI" → invoke_agent("researcher", "...") THEN invoke_agent("task-writer", "...")

Sii proattivo e chiedi chiarimenti solo se strettamente necessario.
""".format(
    task_writer_arn=AGENTS["task-writer"],
    task_reader_arn=AGENTS["task-reader"],
    researcher_arn=AGENTS["researcher"],
    calculator_arn=AGENTS["calculator"]
)


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    """Punto di ingresso dell'orchestrator agent"""

    global agent

    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    
    logger.info("Orchestrator invocato")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Configura il modello
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        temperature=0.3,
        streaming=True
    )
    
    # Crea agent con tool per invocare altri agenti
    if agent is None:
        agent = Agent(
            name="Orchestrator",
            hooks=[
                ShortMemoryHook(memory_id=memory_config.memory_id),
                LongTermMemoryHook(memory_id=memory_config.memory_id)
            ],
            state={"actor_id": actor_id, "session_id": session_id},
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[retrieve_memories, invoke_agent]
        )
    
    user_message = payload.get("prompt", "Come posso aiutarti?")
    logger.info(f"Messaggio utente: {user_message}")
    
    try:
        result = agent(user_message)
        logger.info("Orchestrator completato con successo")
        return {"result": result.message}
    except Exception as e:
        logger.error(f"Errore nell'orchestrator: {e}", exc_info=True)
        return {"error": f"Errore durante l'orchestrazione: {str(e)}"}


if __name__ == "__main__":
    app.run()
