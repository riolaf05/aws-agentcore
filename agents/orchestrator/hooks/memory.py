# -*- coding: utf-8 -*-
"""
Gestore Memoria AgentCore

Questo modulo fornisce funzionalita di memoria unificate per tutti i framework AgentCore, incluso:
1. Caricamento del contesto della conversazione precedente durante l'inizializzazione
2. Recupero dei ricordi rilevanti prima dell'elaborazione del messaggio
3. Memorizzazione di nuovi messaggi dopo ogni risposta
4. Memorizzazione di fatti semantici

Utilizzo:
    memory_config = MemoryConfig()
    memories = retrieve_memories_for_actor(
        memory_id=memory_config.memory_id,
        actor_id="user-123",
        search_query="query di ricerca",
        memory_client=memory_client
    )
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from bedrock_agentcore.memory import MemoryClient


logger = logging.getLogger(__name__)


class MemoryConfig:
    """Gestisce la configurazione della memoria da file JSON con caching."""
    
    _cached_config: Optional[Dict[str, Any]] = None
    _cached_path: Optional[str] = None
    
    def __init__(self, config_path: str = "memory-config.json"):
        """
        Inizializza MemoryConfig.
        
        Args:
            config_path: Percorso al file di configurazione JSON della memoria
        """
        self.config_path = config_path
        self._load_config()
    
    def _load_config(self) -> None:
        """Carica la configurazione dal file JSON con caching."""
        if MemoryConfig._cached_config is not None and MemoryConfig._cached_path == self.config_path:
            logger.debug(f"Utilizzo della configurazione in cache da {self.config_path}")
            return
        
        try:
            # Prova a caricare dal percorso specificato
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                logger.warning(f"File di configurazione non trovato: {self.config_path}")
                # Usa configurazione di default
                MemoryConfig._cached_config = {
                    "memory_id": "default-memory-id",
                    "namespace": "/default/namespace"
                }
            else:
                with open(config_file, 'r', encoding='utf-8') as f:
                    MemoryConfig._cached_config = json.load(f)
                    logger.info(f"Configurazione della memoria caricata da {self.config_path}")
            
            MemoryConfig._cached_path = self.config_path
            
        except Exception as e:
            logger.error(f"Errore nel caricamento della configurazione della memoria: {e}")
            # Usa configurazione di default in caso di errore
            MemoryConfig._cached_config = {
                "memory_id": "default-memory-id",
                "namespace": "/default/namespace"
            }
    
    @property
    def memory_id(self) -> str:
        """Ottiene ID della memoria."""
        if MemoryConfig._cached_config is None:
            self._load_config()
        return MemoryConfig._cached_config.get("memory_id", "default-memory-id")
    
    @property
    def namespace(self) -> str:
        """Ottiene il namespace della memoria."""
        if MemoryConfig._cached_config is None:
            self._load_config()
        return MemoryConfig._cached_config.get("namespace", "/default/namespace")


def retrieve_memories_for_actor(
    memory_id: str,
    actor_id: str,
    search_query: str,
    memory_client: MemoryClient
) -> List[Dict[str, Any]]:
    """
    Recupera i ricordi per un attore specifico utilizzando una query di ricerca.
    
    Args:
        memory_id: L'ID dell'istanza di memoria
        actor_id: L'identificatore dell'attore
        search_query: La query di ricerca per trovare ricordi rilevanti
        memory_client: Il client della memoria da utilizzare
        
    Returns:
        Lista di ricordi recuperati dal client della memoria
    """
    try:
        logger.debug(f"Ricerca ricordi per actor_id={actor_id} con query='{search_query}'")
        
        # Cerca i ricordi usando il memory client
        response = memory_client.search_memories(
            memory_id=memory_id,
            actor_id=actor_id,
            query=search_query,
            max_results=5
        )
        
        memories = response.get("results", [])
        logger.info(f"Trovati {len(memories)} ricordi per la query '{search_query}'")
        
        return memories
        
    except Exception as e:
        logger.warning(f"Errore nel recupero dei ricordi: {e}")
        return []
