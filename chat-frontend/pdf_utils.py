"""
Utility per la lettura e l'elaborazione di file PDF.
Fornisce funzioni per estrarre testo da PDF e manipolare contenuti.
"""

import io
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_content):
    """
    Estrae il testo da un file PDF.
    
    Args:
        file_content (bytes): Contenuto binario del file PDF
        
    Returns:
        str: Testo estratto dal PDF
        
    Raises:
        Exception: Se l'estrazione fallisce
        
    Example:
        >>> with open('document.pdf', 'rb') as f:
        ...     content = f.read()
        >>> text = extract_text_from_pdf(content)
        >>> print(text[:100])
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += page_text + "\n"
            logger.debug(f"Extracted {len(page_text)} chars from page {page_num + 1}")
        
        logger.info(f"📄 Extracted {len(text)} characters from PDF ({len(pdf_reader.pages)} pages)")
        return text
    except Exception as e:
        logger.error(f"❌ Error extracting text from PDF: {e}")
        raise


def extract_text_from_pdf_file(filepath):
    """
    Estrae il testo da un file PDF dato il percorso.
    
    Args:
        filepath (str): Percorso del file PDF
        
    Returns:
        str: Testo estratto dal PDF
        
    Example:
        >>> text = extract_text_from_pdf_file('/path/to/document.pdf')
        >>> print(text)
    """
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        return extract_text_from_pdf(content)
    except Exception as e:
        logger.error(f"❌ Error reading PDF file {filepath}: {e}")
        raise


def get_pdf_metadata(file_content):
    """
    Estrae i metadati da un file PDF.
    
    Args:
        file_content (bytes): Contenuto binario del file PDF
        
    Returns:
        dict: Dizionario con metadati (author, title, pages, etc.)
        
    Example:
        >>> with open('document.pdf', 'rb') as f:
        ...     content = f.read()
        >>> metadata = get_pdf_metadata(content)
        >>> print(f"Title: {metadata['title']}, Pages: {metadata['pages']}")
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(file_content))
        
        metadata = {
            'pages': len(pdf_reader.pages),
            'metadata': {}
        }
        
        if pdf_reader.metadata:
            metadata['metadata'] = {
                'author': pdf_reader.metadata.get('/Author', ''),
                'title': pdf_reader.metadata.get('/Title', ''),
                'subject': pdf_reader.metadata.get('/Subject', ''),
                'creator': pdf_reader.metadata.get('/Creator', ''),
                'producer': pdf_reader.metadata.get('/Producer', ''),
            }
        
        logger.info(f"📋 Extracted metadata from PDF: {metadata['pages']} pages")
        return metadata
    except Exception as e:
        logger.error(f"❌ Error extracting PDF metadata: {e}")
        raise


def chunk_text(text, chunk_size=1000, overlap=200):
    """
    Divide un testo in chunk di dimensione fissa con overlap.
    
    Args:
        text (str): Testo da dividere
        chunk_size (int): Dimensione massima di ogni chunk in caratteri
        overlap (int): Numero di caratteri sovrapposti tra chunk consecutivi
        
    Returns:
        list[str]: Lista di chunk di testo
        
    Example:
        >>> text = "Questo è un testo molto lungo che deve essere diviso in chunk..."
        >>> chunks = chunk_text(text, chunk_size=100, overlap=20)
        >>> print(f"Created {len(chunks)} chunks")
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Se abbiamo raggiunto la fine, esci
        if end >= len(text):
            break
        
        # Sposta l'inizio considerando l'overlap
        start = end - overlap
    
    logger.info(f"✂️ Split text into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks


# ========== ESEMPIO DI UTILIZZO ==========
if __name__ == '__main__':
    """
    Esempi di utilizzo delle funzioni PDF utilities.
    """
    
    # Configurazione logging
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("PDF Utilities - Esempi di Utilizzo")
    print("=" * 60)
    
    # Esempio 1: Estrarre testo da un PDF
    print("\n1️⃣ Esempio: Estrazione testo da PDF")
    print("-" * 60)
    """
    # Esempio con file reale
    pdf_path = "/path/to/your/document.pdf"
    
    try:
        # Leggi il PDF
        text = extract_text_from_pdf_file(pdf_path)
        print(f"✅ Testo estratto: {len(text)} caratteri")
        print(f"Preview: {text[:200]}...")
        
    except FileNotFoundError:
        print("❌ File non trovato")
    except Exception as e:
        print(f"❌ Errore: {e}")
    """
    print("# Decommenta il codice sopra e fornisci un percorso PDF valido")
    
    # Esempio 2: Estrarre metadati
    print("\n2️⃣ Esempio: Estrazione metadati da PDF")
    print("-" * 60)
    """
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
        
        metadata = get_pdf_metadata(content)
        print(f"✅ Metadati estratti:")
        print(f"   - Pagine: {metadata['pages']}")
        print(f"   - Titolo: {metadata['metadata'].get('title', 'N/A')}")
        print(f"   - Autore: {metadata['metadata'].get('author', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    """
    print("# Decommenta il codice sopra per estrarre i metadati")
    
    # Esempio 3: Dividere testo in chunk
    print("\n3️⃣ Esempio: Divisione testo in chunk")
    print("-" * 60)
    
    sample_text = """
    Questo è un esempio di testo che vogliamo dividere in chunk.
    La divisione in chunk è utile quando si lavora con large language models
    o quando si devono salvare testi lunghi in database vettoriali come Qdrant.
    Ogni chunk può essere processato separatamente e convertito in embedding.
    L'overlap tra chunk consecutivi aiuta a mantenere il contesto tra un chunk e l'altro.
    """ * 10  # Ripeti per avere un testo più lungo
    
    chunks = chunk_text(sample_text, chunk_size=200, overlap=50)
    print(f"✅ Testo diviso in {len(chunks)} chunks")
    print(f"   - Chunk 1 (len={len(chunks[0])}): {chunks[0][:80]}...")
    print(f"   - Chunk 2 (len={len(chunks[1])}): {chunks[1][:80]}...")
    
    # Esempio 4: Workflow completo
    print("\n4️⃣ Esempio: Workflow completo (PDF → Text → Chunks)")
    print("-" * 60)
    """
    try:
        # 1. Estrai testo dal PDF
        text = extract_text_from_pdf_file(pdf_path)
        
        # 2. Dividi in chunk
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        
        # 3. Processa ogni chunk (es. genera embeddings)
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            # Qui potresti chiamare un modello di embedding
            # embedding = generate_embedding(chunk)
            # save_to_database(chunk, embedding)
        
        print(f"✅ Processati {len(chunks)} chunks")
        
    except Exception as e:
        print(f"❌ Errore nel workflow: {e}")
    """
    print("# Decommenta il codice sopra per il workflow completo")
    
    print("\n" + "=" * 60)
    print("Per usare queste funzioni nel tuo codice:")
    print("  from pdf_utils import extract_text_from_pdf, chunk_text")
    print("=" * 60)
