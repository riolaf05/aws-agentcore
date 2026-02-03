"""
Utility per l'interazione con Qdrant Vector Database.
Fornisce funzioni per gestire collections, salvare embeddings con metadata,
e fare ricerche filtrate.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


class QdrantManager:
    """
    Manager per operazioni su Qdrant Vector Database.
    Supporta storage modes 'fixed' e 'parent-child' per embeddings.
    """
    
    def __init__(self, host='localhost', port=6333, collection_name='default_collection'):
        """
        Inizializza il manager Qdrant.
        
        Args:
            host (str): Host del server Qdrant
            port (int): Porta del server Qdrant
            collection_name (str): Nome della collection da usare
            
        Example:
            >>> manager = QdrantManager(host='localhost', port=6333, collection_name='my_kb')
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connette al server Qdrant."""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"✅ Qdrant client connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
            raise
    
    def create_collection(self, vector_size=1536, distance=Distance.COSINE):
        """
        Crea una collection se non esiste.
        
        Args:
            vector_size (int): Dimensione dei vettori (default 1536 per OpenAI)
            distance (Distance): Metrica di distanza (COSINE, EUCLID, DOT)
            
        Example:
            >>> manager.create_collection(vector_size=1536)
        """
        try:
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance)
                )
                logger.info(f"📦 Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"📦 Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise
    
    def save_chunks(self, chunks: List[Dict[str, Any]], metadata: Dict[str, Any], 
                    storage_mode: str = "fixed", parent_text: Optional[str] = None,
                    parent_vector: Optional[List[float]] = None, vector_size: int = 1536) -> bool:
        """
        Salva chunks con embeddings su Qdrant.
        
        Args:
            chunks: Lista di dict con 'text', 'embedding', e opzionalmente 'id'
            metadata: Metadata comuni per tutti i chunk (es. {"nome_obiettivo": "...", "data": "..."})
            storage_mode: "fixed" o "parent-child"
            
        Returns:
            bool: True se il salvataggio ha successo
            
        Example:
            >>> chunks = [
            ...     {'text': 'Primo chunk...', 'embedding': [0.1, 0.2, ...], 'id': 1},
            ...     {'text': 'Secondo chunk...', 'embedding': [0.3, 0.4, ...], 'id': 2}
            ... ]
            >>> metadata = {'nome_obiettivo': 'Progetto AI', 'data_odierna': '2026-02-02'}
            >>> success = manager.save_chunks(chunks, metadata, storage_mode='fixed')
        """
        try:
            # Assicura che la collection esista
            # Tenta di derivare la dimensione dal primo embedding se disponibile
            if chunks and isinstance(chunks[0].get('embedding', None), list) and chunks[0].get('embedding'):
                vector_size = len(chunks[0].get('embedding'))
            self.create_collection(vector_size=vector_size)

            points = []

            # Modalità parent-child
            if storage_mode == "parent-child":
                parent_id = str(uuid.uuid4())
                parent_text = parent_text or "\n".join([c.get('text', '') for c in chunks])

                # Vector del parent: usa parent_vector se fornito, altrimenti media dei child
                if parent_vector is None:
                    child_vectors = [c.get('embedding', []) for c in chunks if c.get('embedding')]
                    if child_vectors:
                        parent_vector = [sum(vals) / len(vals) for vals in zip(*child_vectors)]
                    else:
                        parent_vector = [0.0] * vector_size

                parent_payload = {
                    "text": parent_text,
                    "is_parent": True,
                    "storage_mode": storage_mode,
                    **metadata
                }
                points.append(PointStruct(
                    id=parent_id,
                    vector=parent_vector,
                    payload=parent_payload
                ))

                for i, chunk in enumerate(chunks):
                    payload = {
                        "text": chunk.get('text', ''),
                        "chunk_index": i,
                        "storage_mode": storage_mode,
                        "is_parent": False,
                        "parent_id": parent_id,
                        **metadata
                    }
                    if 'metadata' in chunk:
                        payload.update(chunk['metadata'])
                    points.append(PointStruct(
                        id=chunk.get('id', i),
                        vector=chunk.get('embedding', []),
                        payload=payload
                    ))
            else:
                # Modalità fixed
                for i, chunk in enumerate(chunks):
                    payload = {
                        "text": chunk.get('text', ''),
                        "chunk_index": i,
                        "storage_mode": storage_mode,
                        **metadata
                    }
                    if 'metadata' in chunk:
                        payload.update(chunk['metadata'])
                    points.append(PointStruct(
                        id=chunk.get('id', i),
                        vector=chunk.get('embedding', []),
                        payload=payload
                    ))

            # Inserisci i punti
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"✅ Saved {len(points)} points to Qdrant (mode: {storage_mode})")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving to Qdrant: {e}")
            raise
    
    def search(self, query_vector: List[float], filters: Optional[Dict[str, Any]] = None, 
               limit: int = 10) -> List[Any]:
        """
        Cerca su Qdrant con filtri sul payload.
        
        Args:
            query_vector: Vettore embedding della query
            filters: Dict con filtri (es. {"nome_obiettivo": "Progetto AI"})
            limit: Numero massimo di risultati
            
        Returns:
            List[ScoredPoint]: Lista di risultati ordinati per score
            
        Example:
            >>> query_emb = [0.1, 0.2, 0.3, ...]  # Embedding della query
            >>> filters = {"nome_obiettivo": "Progetto AI"}
            >>> results = manager.search(query_emb, filters=filters, limit=5)
            >>> for hit in results:
            ...     print(f"Score: {hit.score}, Text: {hit.payload['text'][:50]}...")
        """
        try:
            # Costruisci i filtri
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                query_filter = Filter(must=conditions)
            
            # Cerca
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            
            logger.info(f"🔍 Found {len(results)} results from Qdrant")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching Qdrant: {e}")
            raise
    
    def delete_by_filter(self, filters: Dict[str, Any]) -> bool:
        """
        Elimina punti filtrati dal payload.
        
        Args:
            filters: Dict con filtri per identificare i punti da eliminare
            
        Returns:
            bool: True se l'eliminazione ha successo
            
        Example:
            >>> # Elimina tutti i chunk di un obiettivo specifico
            >>> manager.delete_by_filter({"nome_obiettivo": "Vecchio Progetto"})
        """
        try:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            query_filter = Filter(must=conditions)
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=query_filter
            )
            
            logger.info(f"🗑️ Deleted points matching filters: {filters}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting from Qdrant: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sulla collection.
        
        Returns:
            dict: Informazioni sulla collection (count, config, etc.)
            
        Example:
            >>> info = manager.get_collection_info()
            >>> print(f"Points count: {info['points_count']}")
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'status': info.status,
                'config': info.config
            }
        except Exception as e:
            logger.error(f"❌ Error getting collection info: {e}")
            raise


# ========== FUNZIONI HELPER ==========

def create_qdrant_client(host='localhost', port=6333):
    """
    Crea e restituisce un client Qdrant connesso.
    
    Example:
        >>> client = create_qdrant_client(host='localhost', port=6333)
    """
    try:
        client = QdrantClient(host=host, port=port)
        logger.info(f"✅ Qdrant client created: {host}:{port}")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to create Qdrant client: {e}")
        raise


# ========== ESEMPIO DI UTILIZZO ==========
if __name__ == '__main__':
    """
    Esempi di utilizzo delle funzioni Qdrant utilities.
    """
    
    # Configurazione logging
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Qdrant Utilities - Esempi di Utilizzo")
    print("=" * 60)
    
    # Esempio 1: Inizializzazione
    print("\n1️⃣ Esempio: Inizializzazione QdrantManager")
    print("-" * 60)
    """
    # Crea il manager
    manager = QdrantManager(
        host='localhost',
        port=6333,
        collection_name='knowledge_base'
    )
    print("✅ Manager inizializzato")
    """
    print("# Decommenta il codice sopra per connetterti a Qdrant")
    
    # Esempio 2: Salvare chunks
    print("\n2️⃣ Esempio: Salvare chunks con embeddings")
    print("-" * 60)
    """
    # Prepara chunks con embeddings (simulati)
    chunks = [
        {
            'id': 1,
            'text': 'Il progetto AI mira a sviluppare un assistente intelligente...',
            'embedding': [0.1] * 1536  # Embedding simulato (1536 dimensioni per OpenAI)
        },
        {
            'id': 2,
            'text': 'Le funzionalità principali includono NLP e machine learning...',
            'embedding': [0.2] * 1536
        }
    ]
    
    # Metadata comuni per tutti i chunk
    metadata = {
        'nome_obiettivo': 'Progetto AI Assistant',
        'data_odierna': datetime.now().strftime("%Y-%m-%d"),
        'tipo': 'meeting-notes'
    }
    
    # Salva su Qdrant
    success = manager.save_chunks(chunks, metadata, storage_mode='fixed')
    print(f"✅ Chunks salvati: {success}")
    """
    print("# Decommenta il codice sopra per salvare chunks")
    
    # Esempio 3: Ricerca con filtri
    print("\n3️⃣ Esempio: Ricerca con filtri sul payload")
    print("-" * 60)
    """
    # Embedding della query (simulato)
    query_embedding = [0.15] * 1536
    
    # Cerca solo chunk relativi a un obiettivo specifico
    filters = {
        'nome_obiettivo': 'Progetto AI Assistant'
    }
    
    results = manager.search(
        query_vector=query_embedding,
        filters=filters,
        limit=5
    )
    
    print(f"✅ Trovati {len(results)} risultati")
    for i, hit in enumerate(results):
        print(f"\n  Risultato {i+1}:")
        print(f"    - Score: {hit.score:.4f}")
        print(f"    - Text: {hit.payload['text'][:80]}...")
        print(f"    - Obiettivo: {hit.payload['nome_obiettivo']}")
        print(f"    - Data: {hit.payload['data_odierna']}")
    """
    print("# Decommenta il codice sopra per fare ricerche")
    
    # Esempio 4: Informazioni collection
    print("\n4️⃣ Esempio: Ottenere informazioni sulla collection")
    print("-" * 60)
    """
    info = manager.get_collection_info()
    print(f"✅ Informazioni collection:")
    print(f"   - Punti totali: {info['points_count']}")
    print(f"   - Vettori totali: {info['vectors_count']}")
    print(f"   - Status: {info['status']}")
    """
    print("# Decommenta il codice sopra per vedere le info")
    
    # Esempio 5: Workflow completo
    print("\n5️⃣ Esempio: Workflow completo (Save → Search → Delete)")
    print("-" * 60)
    """
    try:
        # 1. Inizializza manager
        manager = QdrantManager(host='localhost', port=6333, collection_name='test_kb')
        
        # 2. Salva alcuni chunk
        chunks = [
            {'id': i, 'text': f'Chunk {i} content...', 'embedding': [0.1 * i] * 1536}
            for i in range(5)
        ]
        metadata = {'nome_obiettivo': 'Test Project', 'data_odierna': '2026-02-02'}
        manager.save_chunks(chunks, metadata)
        
        # 3. Cerca
        query_emb = [0.2] * 1536
        results = manager.search(query_emb, filters={'nome_obiettivo': 'Test Project'}, limit=3)
        print(f"Trovati {len(results)} risultati")
        
        # 4. Elimina
        manager.delete_by_filter({'nome_obiettivo': 'Test Project'})
        print("Chunk eliminati")
        
    except Exception as e:
        print(f"❌ Errore nel workflow: {e}")
    """
    print("# Decommenta il codice sopra per il workflow completo")
    
    print("\n" + "=" * 60)
    print("Per usare queste funzioni nel tuo codice:")
    print("  from qdrant_utils import QdrantManager")
    print("  manager = QdrantManager(host='localhost', port=6333)")
    print("=" * 60)
