# -*- coding: utf-8 -*-
"""Configurazione agente e logica di creazione con punto di ingresso principale applicazione."""

import json
import logging
from typing import List, Dict, Any, Optional

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from bedrock_agentcore.memory import MemoryClient

from strands import Agent, tool
from strands_tools import calculator

from hooks.short_memory_hook import ShortMemoryHook
from hooks.long_term_memory_hook import LongTermMemoryHook
# Importa moduli memoria condivisi
from hooks.memory import MemoryConfig, retrieve_memories_for_actor

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"

# Inizializza la configurazione della memoria e il client
memory_config = MemoryConfig()
memory_client = MemoryClient()

# Inizializza app Bedrock AgentCore
app = BedrockAgentCoreApp()


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


def create_agent(actor_id: str, session_id: str) -> Agent:
    """Crea e configura l'agente con hook e tool."""
    logger.info("Creazione agente con hook della memoria e tool calcolatrice")
    logger.debug("Stato agente - actor_id: %s, session_id: %s", actor_id, session_id)
    
    agent = Agent(
        hooks=[
            ShortMemoryHook(memory_id=memory_config.memory_id),
            LongTermMemoryHook(memory_id=memory_config.memory_id)
        ],
        tools=[calculator, retrieve_memories], 
        state={"actor_id": actor_id, "session_id": session_id}
    )
    
    logger.info("Agente creato con successo")
    return agent


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    """Punto di ingresso agente AI"""   
    global agent
    
    # Estrai i parametri con priorita al contesto per session_id
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    
    if agent is None:
        agent = create_agent(actor_id, session_id)
    
    logger.info("Ricevuta richiesta di invocazione")
    logger.debug("Payload: %s", json.dumps(payload, indent=2))
    logger.debug("Context: %s", json.dumps(context, indent=2, default=str) if context else "Nessun contesto")
    logger.info(f"Elaborazione richiesta per actor_id: {actor_id}, session_id: {session_id}")
    
    user_message = payload.get("prompt", "Spiega cosa puoi fare per me.")
    logger.debug("Messaggio utente: %s", user_message)
    
    try:
        result = agent(user_message)
        logger.info("Risposta agente generata con successo")
        return {"result": result.message}
    except Exception as e:
        logger.error("Errore durante invocazione agente: %s", e, exc_info=True)
        return {"error": "Si e verificato un errore durante elaborazione della tua richiesta"}


def main():
    """Punto di ingresso principale per applicazione."""
    app.run()


if __name__ == "__main__":
    main()
