# Utility Modules - PDF & Qdrant

Moduli riutilizzabili per la gestione di PDF e Qdrant Vector Database.

## 📄 pdf_utils.py

Utility per la lettura e l'elaborazione di file PDF.

### Funzioni principali:

#### `extract_text_from_pdf(file_content)`
Estrae il testo da un file PDF fornito come bytes.

```python
from pdf_utils import extract_text_from_pdf

# Da file già letto
with open('document.pdf', 'rb') as f:
    content = f.read()
text = extract_text_from_pdf(content)
print(text)
```

#### `extract_text_from_pdf_file(filepath)`
Estrae il testo da un file PDF dato il percorso.

```python
from pdf_utils import extract_text_from_pdf_file

text = extract_text_from_pdf_file('/path/to/document.pdf')
print(f"Estratti {len(text)} caratteri")
```

#### `get_pdf_metadata(file_content)`
Estrae metadati da un PDF (titolo, autore, numero di pagine, etc.).

```python
from pdf_utils import get_pdf_metadata

with open('document.pdf', 'rb') as f:
    content = f.read()
metadata = get_pdf_metadata(content)
print(f"Titolo: {metadata['metadata']['title']}")
print(f"Pagine: {metadata['pages']}")
```

#### `chunk_text(text, chunk_size=1000, overlap=200)`
Divide un testo in chunk di dimensione fissa con overlap.

```python
from pdf_utils import chunk_text

text = "Testo molto lungo da dividere..."
chunks = chunk_text(text, chunk_size=500, overlap=100)
print(f"Creati {len(chunks)} chunks")
```

### Esempio completo

```python
from pdf_utils import extract_text_from_pdf_file, chunk_text

# 1. Estrai testo dal PDF
text = extract_text_from_pdf_file('/path/to/document.pdf')

# 2. Dividi in chunk
chunks = chunk_text(text, chunk_size=1000, overlap=200)

# 3. Processa ogni chunk
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk[:50]}...")
```

---

## 🗄️ qdrant_utils.py

Utility per l'interazione con Qdrant Vector Database.

### Classe principale: `QdrantManager`

Manager per operazioni su Qdrant con supporto per storage modes 'fixed' e 'parent-child'.

#### Inizializzazione

```python
from qdrant_utils import QdrantManager

manager = QdrantManager(
    host='localhost',
    port=6333,
    collection_name='my_collection'
)
```

#### Metodi principali:

##### `create_collection(vector_size=1536, distance=Distance.COSINE)`
Crea una collection se non esiste.

```python
manager.create_collection(vector_size=1536)
```

##### `save_chunks(chunks, metadata, storage_mode='fixed')`
Salva chunks con embeddings su Qdrant.

```python
chunks = [
    {
        'id': 1,
        'text': 'Primo chunk di testo...',
        'embedding': [0.1, 0.2, 0.3, ...]  # 1536 dimensioni
    },
    {
        'id': 2,
        'text': 'Secondo chunk di testo...',
        'embedding': [0.4, 0.5, 0.6, ...]
    }
]

metadata = {
    'nome_obiettivo': 'Progetto AI',
    'data_odierna': '2026-02-02',
    'tipo': 'meeting-notes'
}

manager.save_chunks(chunks, metadata, storage_mode='fixed')
```

##### `search(query_vector, filters=None, limit=10)`
Cerca su Qdrant con filtri sul payload.

```python
# Embedding della query (ottenuto da un modello di embedding)
query_embedding = [0.15, 0.25, 0.35, ...]  # 1536 dimensioni

# Cerca solo chunk relativi a un obiettivo specifico
filters = {'nome_obiettivo': 'Progetto AI'}
results = manager.search(query_embedding, filters=filters, limit=5)

for hit in results:
    print(f"Score: {hit.score:.4f}")
    print(f"Text: {hit.payload['text'][:100]}...")
    print(f"Obiettivo: {hit.payload['nome_obiettivo']}")
```

##### `delete_by_filter(filters)`
Elimina punti filtrati dal payload.

```python
# Elimina tutti i chunk di un obiettivo specifico
manager.delete_by_filter({'nome_obiettivo': 'Vecchio Progetto'})
```

##### `get_collection_info()`
Ottiene informazioni sulla collection.

```python
info = manager.get_collection_info()
print(f"Punti totali: {info['points_count']}")
print(f"Vettori totali: {info['vectors_count']}")
```

### Esempio completo: Knowledge Base con RAG

```python
from pdf_utils import extract_text_from_pdf_file, chunk_text
from qdrant_utils import QdrantManager
from datetime import datetime

# 1. Estrai testo dal PDF
text = extract_text_from_pdf_file('/path/to/document.pdf')

# 2. Dividi in chunk
text_chunks = chunk_text(text, chunk_size=1000, overlap=200)

# 3. Genera embeddings (usa il tuo modello preferito)
# Esempio con OpenAI (necessita openai library)
"""
import openai
embeddings = []
for chunk in text_chunks:
    response = openai.Embedding.create(
        input=chunk,
        model="text-embedding-ada-002"
    )
    embeddings.append(response['data'][0]['embedding'])
"""

# 4. Prepara chunks con embeddings (simulati qui)
chunks_with_embeddings = [
    {
        'id': i,
        'text': chunk,
        'embedding': [0.1] * 1536  # Sostituisci con embedding reale
    }
    for i, chunk in enumerate(text_chunks)
]

# 5. Salva su Qdrant
manager = QdrantManager(host='localhost', port=6333, collection_name='knowledge_base')

metadata = {
    'nome_obiettivo': 'Progetto AI Assistant',
    'data_odierna': datetime.now().strftime("%Y-%m-%d"),
    'document_type': 'technical_doc'
}

manager.save_chunks(chunks_with_embeddings, metadata, storage_mode='fixed')

# 6. Cerca (RAG - Retrieval)
query = "Come funziona l'intelligenza artificiale?"
# query_embedding = generate_embedding(query)  # Usa lo stesso modello del punto 3
query_embedding = [0.15] * 1536  # Simulato

results = manager.search(
    query_vector=query_embedding,
    filters={'nome_obiettivo': 'Progetto AI Assistant'},
    limit=3
)

# 7. Usa i risultati per generare risposta (Generation in RAG)
context = "\n\n".join([hit.payload['text'] for hit in results])
print(f"Contesto recuperato ({len(results)} chunks):")
print(context[:500])

# Qui passeresti il context a un LLM per generare la risposta finale
```

---

## 🔧 Utilizzo nel Backend Flask

Nel file `backend.py` i moduli vengono importati così:

```python
from pdf_utils import extract_text_from_pdf
from qdrant_utils import QdrantManager

# Inizializzazione
qdrant_manager = QdrantManager(
    host=os.getenv('QDRANT_HOST', 'localhost'),
    port=int(os.getenv('QDRANT_PORT', '6333')),
    collection_name=os.getenv('QDRANT_COLLECTION', 'knowledge_base')
)

# Uso nell'endpoint
@app.route('/api/kb', methods=['POST'])
def create_kb_document():
    # Estrai testo dal PDF
    text = extract_text_from_pdf(pdf_content)
    
    # Salva su Qdrant
    qdrant_manager.save_chunks(chunks, metadata, storage_mode='fixed')
```

---

## 📦 Dipendenze

Assicurati di avere installato le seguenti librerie:

```bash
pip install PyPDF2>=3.0.0 qdrant-client>=1.7.0
```

O aggiungi al `requirements.txt`:

```
PyPDF2>=3.0.0
qdrant-client>=1.7.0
```

---

## 🧪 Testing

Entrambi i moduli includono esempi eseguibili nel blocco `if __name__ == '__main__'`.

### Test pdf_utils.py

```bash
cd /path/to/your/project
python pdf_utils.py
```

### Test qdrant_utils.py

```bash
# Assicurati che Qdrant sia in esecuzione su localhost:6333
docker run -p 6333:6333 qdrant/qdrant:latest

# Esegui test
python qdrant_utils.py
```

---

## 🐳 Docker Setup

Per usare questi moduli in Docker, assicurati di copiarli nel Dockerfile:

```dockerfile
COPY ../pdf_utils.py .
COPY ../qdrant_utils.py .
```

E che le dipendenze siano in `requirements.txt`.

---

## 📝 Note

- **PDF Extraction**: PyPDF2 funziona bene per la maggior parte dei PDF testuali. Per PDF con layout complessi o immagini, considera `pdfplumber` o `pypdfium2`.
- **Qdrant Storage Modes**: 
  - `fixed`: Ogni chunk è indipendente
  - `parent-child`: Per relazioni gerarchiche tra chunk (implementazione personalizzabile)
- **Vector Size**: Default 1536 dimensioni (OpenAI text-embedding-ada-002). Modifica in base al tuo modello di embedding.
- **Filters**: Qdrant supporta filtri complessi. Vedi [documentazione Qdrant](https://qdrant.tech/documentation/concepts/filtering/) per filtri avanzati.

---

## 🚀 Prossimi Passi

1. Integra un modello di embedding (OpenAI, Sentence Transformers, Cohere, etc.)
2. Implementa un sistema di chunking più sofisticato (semantic chunking)
3. Aggiungi gestione errori più robusta
4. Implementa logging strutturato
5. Aggiungi caching per embedding già generati

---

## 📄 Licenza

Questi moduli sono parte del progetto AWS AgentCore.
