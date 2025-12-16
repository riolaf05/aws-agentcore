# -*- coding: utf-8 -*-
"""Hook per memorizzare e recuperare la cronologia della conversazione dalla memoria."""

import json
import logging
from bedrock_agentcore.memory import MemoryClient
from strands.hooks import HookProvider, HookRegistry, AgentInitializedEvent, MessageAddedEvent
from .memory import MemoryConfig

logger = logging.getLogger(__name__)


class ShortMemoryHook(HookProvider):
    """Hook per memorizzare e recuperare la cronologia della conversazione dalla memoria."""

    def __init__(self, memory_id: str):
        """Inizializza lo ShortMemoryHook con ID della memoria."""
        self.memory_id = memory_id
        self.memory_client = MemoryClient()
        self.memory_config = MemoryConfig()

    def register_hooks(self, registry: HookRegistry) -> None:
        """Registra gli hook per ascoltare gli eventi agente."""
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)

    def on_agent_initialized(self, event: AgentInitializedEvent) -> None:
        """Carica la cronologia della conversazione quando agente viene inizializzato."""
        logger.info("Agente inizializzato: %s", event.agent.name)
        logger.debug("Messaggi dell'agente: %s", event.agent.messages)

        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        logger.debug("Recupero cronologia conversazione per actor_id=%s, session_id=%s", actor_id, session_id)
        
        try:
            conversations = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=100,
            )
            logger.debug("Recuperati %d turni di conversazione dalla memoria", len(conversations) if conversations else 0)
        except Exception as e:
            logger.warning("Impossibile recuperare la cronologia della conversazione dalla memoria: %s", e)
            conversations = None

        if conversations:
            # Aggiungi i messaggi della conversazione precedente all'agente
            for conv_message in conversations:
                # I messaggi della memoria sono gia nel formato corretto
                event.agent.messages.append(conv_message)
            
            logger.info("Caricati %d messaggi precedenti nella conversazione", len(conversations))

    def on_message_added(self, event: MessageAddedEvent) -> None:
        """Memorizza i messaggi quando vengono aggiunti all'agente."""
        logger.info("Messaggio aggiunto all'agente: %s", event.agent.name)
        logger.debug("Messaggi dell'agente: %s", event.agent.messages)

        last_message = event.agent.messages[-1]
        last_message_tuple = (json.dumps(last_message["content"]), last_message["role"])

        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        logger.debug("Memorizzazione messaggio nella memoria per actor_id=%s, session_id=%s", actor_id, session_id)

        try:
            self.memory_client.create_event(
                memory_id=self.memory_id,  # Questo e ID da create_memory o list_memories
                actor_id=actor_id,  # Identificatore attore, potrebbe essere un agente o un utente finale
                session_id=session_id,  # ID univoco per una particolare richiesta/conversazione
                messages=[last_message_tuple]
            )
            logger.debug("Messaggio memorizzato con successo nella memoria")
        except Exception as e:
            logger.error("Errore nella memorizzazione del messaggio: %s", e)
