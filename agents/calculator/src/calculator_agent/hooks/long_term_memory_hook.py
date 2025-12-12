# -*- coding: utf-8 -*-
"""Hook per recuperare e iniettare il contesto della memoria a lungo termine prima invocazione del modello."""

import logging
from bedrock_agentcore.memory import MemoryClient
from strands.hooks import HookProvider, HookRegistry, BeforeInvocationEvent
from .memory import MemoryConfig

logger = logging.getLogger(__name__)


class LongTermMemoryHook(HookProvider):
    """Hook per recuperare e iniettare il contesto della memoria a lungo termine prima dell'invocazione del modello."""

    def __init__(self, memory_id: str):
        """Inizializza il LongTermMemoryHook con l'ID della memoria."""
        self.memory_id = memory_id
        self.memory_client = MemoryClient()
        self.memory_config = MemoryConfig()

    def register_hooks(self, registry: HookRegistry) -> None:
        """Registra l'hook per ascoltare il BeforeInvocationEvent."""
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)

    def on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        """
        Recupera e inietta il contesto della memoria a lungo termine prima di invocare il modello.
        
        Questo metodo viene chiamato prima che l'agente invochi il modello,
        permettendoci di arricchire il contesto con informazioni rilevanti dalla memoria.
        """
        agent = event.agent
        actor_id = agent.state.get("actor_id")
        session_id = agent.state.get("session_id")
        
        # Ottieni l'ultimo messaggio dell'utente per usarlo come query di ricerca
        if agent.messages:
            last_user_message = None
            for msg in reversed(agent.messages):
                if msg.get("role") == "user":
                    last_user_message = msg
                    break
            
            if last_user_message:
                # Estrai il testo del messaggio
                content = last_user_message.get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    search_query = content[0].get("text", "")
                    
                    if search_query:
                        logger.debug(f"Ricerca ricordi a lungo termine per: {search_query}")
                        
                        try:
                            # Cerca ricordi rilevanti
                            response = self.memory_client.search_memories(
                                memory_id=self.memory_id,
                                actor_id=actor_id,
                                query=search_query,
                                max_results=3
                            )
                            
                            memories = response.get("results", [])
                            
                            if memories:
                                # Crea un messaggio di sistema con il contesto della memoria
                                memory_context = "Informazioni rilevanti dalla memoria a lungo termine:\n"
                                for i, memory in enumerate(memories, 1):
                                    memory_text = memory.get("content", "")
                                    memory_context += f"{i}. {memory_text}\n"
                                
                                # Inserisci il contesto della memoria prima dell'ultimo messaggio dell'utente
                                memory_message = {
                                    "role": "system",
                                    "content": [{"text": memory_context}]
                                }
                                
                                # Trova la posizione dell'ultimo messaggio dell'utente
                                last_user_index = len(agent.messages) - 1
                                for i in range(len(agent.messages) - 1, -1, -1):
                                    if agent.messages[i].get("role") == "user":
                                        last_user_index = i
                                        break
                                
                                # Inserisci il messaggio della memoria prima dell'ultimo messaggio dell'utente
                                agent.messages.insert(last_user_index, memory_message)
                                
                                logger.info(f"Iniettati {len(memories)} ricordi nel contesto")
                            
                        except Exception as e:
                            logger.warning(f"Errore nel recupero della memoria a lungo termine: {e}")
