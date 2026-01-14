"""
Researcher Agent - Cerca informazioni aggiornate su internet usando DuckDuckGo.
"""

import logging
from typing import Dict, Any, Optional
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from strands import Agent, tool
from strands.models import BedrockModel
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException, RatelimitException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

SYSTEM_PROMPT = """Sei un assistente AI esperto nella ricerca di informazioni su internet.

Il tuo compito è:
1. Comprendere la richiesta di ricerca dell'utente
2. Formulare query di ricerca efficaci
3. Cercare informazioni usando DuckDuckGo (regione: Italia)
4. Analizzare e sintetizzare i risultati
5. Fornire risposte accurate e ben documentate con citazioni delle fonti

Quando presenti i risultati:
- Riassumi le informazioni principali
- Cita sempre le fonti (titolo e URL)
- Indica la data se disponibile
- Se i risultati sono insufficienti, suggerisci query alternative

Sii accurato, obiettivo e verifica le informazioni da multiple fonti quando possibile.
"""

@tool
def websearch(keywords: str, region: str = "it-it", max_results: int = 5) -> str:
    """Cerca informazioni aggiornate su internet usando DuckDuckGo.
    
    Args:
        keywords (str): Parole chiave per la ricerca.
        region (str): Regione di ricerca (default: it-it per Italia).
        max_results (int): Numero massimo di risultati da restituire (default: 5).
    
    Returns:
        str: Risultati della ricerca formattati come JSON string.
    """
    logger.info(f"Ricerca web per: '{keywords}' (regione: {region})")
    
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        
        if not results:
            return "Nessun risultato trovato. Prova con termini di ricerca diversi."
        
        logger.info(f"Trovati {len(results)} risultati")
        return str(results)
        
    except RatelimitException:
        logger.warning("Rate limit raggiunto")
        return "Rate limit raggiunto. Riprova tra qualche istante."
    except DuckDuckGoSearchException as e:
        logger.error(f"Errore DuckDuckGo: {e}")
        return f"Errore durante la ricerca: {e}"
    except Exception as e:
        logger.error(f"Errore generico: {e}", exc_info=True)
        return f"Errore durante la ricerca: {str(e)}"


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    """Punto di ingresso del researcher agent"""
    
    logger.info("Researcher invocato")
    
    # Configura modello
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        temperature=0.4,
        streaming=True
    )
    
    # Crea agent con tool di ricerca web
    agent = Agent(
        name="Researcher",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[websearch]
    )
    
    user_message = payload.get("prompt", "Cerca informazioni su Python.")
    logger.info(f"Messaggio utente: {user_message}")
    
    try:
        result = agent(user_message)
        logger.info("Researcher completato con successo")
        return {"result": result.message}
    except Exception as e:
        logger.error(f"Errore nel Researcher: {e}", exc_info=True)
        return {"error": f"Errore durante la ricerca: {str(e)}"}


if __name__ == "__main__":
    app.run()
