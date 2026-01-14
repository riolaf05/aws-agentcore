# Researcher Agent

## Descrizione

Agente specializzato nella ricerca di informazioni su internet usando DuckDuckGo con regione Italia.

## Caratteristiche

- **DuckDuckGo Search**: Ricerca web senza API key
- **Regione Italia**: Risultati localizzati (`it-it`)
- **Rate Limiting**: Gestione automatica dei limiti di ricerca
- **No Memory**: Ogni ricerca è indipendente

## Setup

```powershell
pip install -r requirements.txt

# Test locale
python test_researcher.py

# Deploy
agentcore launch
```

## Tool: websearch

Parametri:
- `keywords` (str): Query di ricerca
- `region` (str): Regione (default: "it-it")
- `max_results` (int): Max risultati (default: 5)

## Esempi

### Ricerca tecnologia

```json
{"prompt": "Cerca le novità di Python 3.13"}
```

### Ricerca locale

```json
{"prompt": "Qual è il meteo previsto per Roma?"}
```

### Ricerca con analisi

```json
{"prompt": "Cerca articoli recenti sull'AI generativa e riassumili"}
```

## Note

- **Rate Limiting**: DuckDuckGo ha limiti di frequenza. In caso di errore "Rate limit reached", aspetta qualche secondo.
- **Risultati**: Include titolo, snippet, URL per ogni risultato
- **Regione**: Impostata su Italia per default, modificabile nel prompt

## Upgrade Futuro

Per uso intensivo, considera:
- Google Custom Search API
- Bing Search API  
- SerpAPI
- Implementare caching dei risultati
