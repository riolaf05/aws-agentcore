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
    "researcher": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/researcher-hGVInWG4SS",   
    "calculator": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/calculator-lgV0vpGtcq",
    "project_goal_writer_reader": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/project_goal_writer_reader-61UCrz38Qt",
    "contact_writer_reader": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/contact_writer_reader-6T9ddn3sFx",
    "event_place_writer_reader": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/event_place_writer_reader-2WQYqVFvzj",
    "needs_reader": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/needs_reader-GM0Cq57Z3G"
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
        agent_name: Nome dell'agente da invocare. Valori: researcher, calculator, project-goal-writer-reader, contact-writer-reader, event-place-writer-reader, needs_reader
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
        logger.debug(f"Struttura risposta: {type(response.get('response'))}, Keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
        
        # Processa la risposta
        if "text/event-stream" in response.get("contentType", ""):
            # Handle streaming response
            content = []
            response_body = response.get("response")
            
            if hasattr(response_body, 'iter_lines'):
                for line in response_body.iter_lines(chunk_size=1024):
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            line_str = line_str[6:]
                        content.append(line_str)
            else:
                logger.warning(f"Response body for streaming doesn't have iter_lines method: {type(response_body)}")
                content = [str(response_body)]
            
            result = "\n".join(content)
            logger.debug(f"Risposta streaming da '{agent_name}': {result[:200]}...")
            return result
            
        elif response.get("contentType") == "application/json":
            # Handle standard JSON response
            content = []
            response_body = response.get("response")
            
            # Handle different response body types
            if hasattr(response_body, 'iter_lines'):
                # It's a stream object
                for line in response_body.iter_lines(chunk_size=1024):
                    if line:
                        content.append(line.decode("utf-8"))
            elif isinstance(response_body, bytes):
                # It's raw bytes
                content.append(response_body.decode('utf-8'))
            elif isinstance(response_body, str):
                # It's already a string
                content.append(response_body)
            elif isinstance(response_body, list):
                # It's a list of chunks
                for chunk in response_body:
                    if isinstance(chunk, bytes):
                        content.append(chunk.decode('utf-8'))
                    else:
                        content.append(str(chunk))
            else:
                logger.warning(f"Unknown response body type: {type(response_body)}")
                content.append(str(response_body))
            
            result_str = ''.join(content)
            logger.debug(f"Raw JSON string da '{agent_name}': {result_str[:300]}...")
            
            try:
                result_data = json.loads(result_str)
            except json.JSONDecodeError:
                logger.error(f"Errore parsing JSON: {result_str}")
                return result_str
            
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
            # Try to read response body
            response_body = response.get("response")
            if hasattr(response_body, 'read'):
                body_content = response_body.read().decode('utf-8')
                return body_content
            else:
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
  
- **researcher**: Cerca informazioni aggiornate su internet (regione: Italia)
  ARN: {researcher_arn}
  
- **calculator**: Esegue calcoli matematici e mantiene memoria delle operazioni
  ARN: {calculator_arn}

- **project_goal_writer_reader**: Gestisce progetti e obiettivi strategici (CRUD completo)
  ARN: {project_goal_arn}
  Usa questo agente per:
  - Creare, leggere, aggiornare progetti software
  - Creare, leggere, aggiornare o eliminare obiettivi strategici

- **contact_writer_reader**: Gestisce contatti personali e professionali (CRUD completo)
    ARN: {contact_arn}
    Usa questo agente per:
    - Creare, leggere, aggiornare o eliminare contatti
    - Gestire informazioni come nome, cognome, email, telefono, descrizione, tipo, dove_conosciuto, note, url
    - Quando aggiungi o aggiorni un contatto, se l'utente menziona il tipo (es. "investitore", "fornitore", "startup"), passa il parametro "tipo" al tool

- **event_place_writer_reader**: Gestisce eventi e luoghi (CRUD completo per entrambi)
  ARN: {event_place_arn}
  Usa questo agente per:
  - EVENTI: Creare, leggere, aggiornare o eliminare eventi
    * Campi: nome, data, luogo, descrizione (può invocare researcher per descrizioni dettagliate)
  - LUOGHI: Creare, leggere, aggiornare o eliminare luoghi
    * Campi: nome, descrizione, categoria (ristorante, sport, agriturismo, museo, teatro, cinema, bar, hotel, parco, altro), indirizzo
  - Supporta caricamento multiplo di eventi/luoghi

- **needs_reader**: Cerca e recupera job needs dal database MongoDB MatchGuru
  ARN: {needs_reader_arn}
  Usa questo agente per:
  - Elencare tutti i need disponibili
  - Cercare need per parole chiave (ruolo, competenze, tecnologie, azienda, location)
  - Recuperare un need specifico tramite ID
  Esempi: "Mostrami i need per Cloud engineer", "Cerca need da Data Scientist", "Mostrami tutti i need disponibili"

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
- "Crea un progetto per sistema di raccomandazione AI" → invoke_agent("project-goal-writer-reader", "...")
- "Mostrami gli obiettivi per Reply" → invoke_agent("project-goal-writer-reader", "...")
- "Crea un obiettivo per aumentare il fatturato Q1" → invoke_agent("project-goal-writer-reader", "...")
- "Aggiungi un contatto per Mario Rossi" → invoke_agent("contact-writer-reader", "...")
- "Mostrami i contatti conosciuti a Roma" → invoke_agent("contact-writer-reader", "...")
- "Crea un evento per conferenza AI a Milano" → invoke_agent("event-place-writer-reader", "...")
- "Aggiungi il ristorante Da Giovanni in via Roma" → invoke_agent("event-place-writer-reader", "...")
- "Mostrami gli eventi a dicembre" → invoke_agent("event-place-writer-reader", "...")
- "Mostrami i need per Cloud engineer" → invoke_agent("needs_reader", "...")
- "Cerca need da Data Scientist a Milano" → invoke_agent("needs_reader", "...")
- "Crea un task per studiare i risultati della ricerca su AI" → invoke_agent("researcher", "...") THEN invoke_agent("task-writer", "...")

Sii proattivo e chiedi chiarimenti solo se strettamente necessario.
""".format(
    researcher_arn=AGENTS["researcher"],
    calculator_arn=AGENTS["calculator"],
    project_goal_arn=AGENTS["project_goal_writer_reader"],
    contact_arn=AGENTS["contact_writer_reader"],
    event_place_arn=AGENTS["event_place_writer_reader"],
    needs_reader_arn=AGENTS["needs_reader"]
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
