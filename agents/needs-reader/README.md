# Needs API Agent

Agente AI specializzato per la ricerca e gestione di esigenze professionali e opportunità aziendali. Utilizza il Needs API Gateway per accedere ai dati memorizzati in MongoDB.

## Funzionalità

- 🔍 **Ricerca per parola chiave**: Cerca need per titolo, descrizione, ruolo, azienda e città
- 📋 **Elenco completo**: Visualizza tutti i need disponibili
- 🎯 **Ricerca per ID**: Recupera dettagli specifici di un need
- 🤖 **Analisi conversazionale**: Descrivi cosa stai cercando e l'agente troverà le corrispondenze

## Setup

### Prerequisiti
- Python 3.9+
- `bedrock-agentcore-starter-toolkit` installato
- AWS CLI configurato
- Accesso al gateway MCP del Needs API

### Installazione

```bash
cd agents/needs-reader
pip install -r requirements.txt
```

### Configurazione Variabili d'Ambiente

Configura le seguenti variabili d'ambiente:

```bash
export GATEWAY_CLIENT_ID="your-client-id"
export GATEWAY_CLIENT_SECRET="your-client-secret"
export GATEWAY_TOKEN_ENDPOINT="https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/token"
export GATEWAY_MCP_URL="https://your-gateway.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
```

Oppure modifica le impostazioni hardcoded in `agent.py`.

## Utilizzo

### Locale

```bash
python agent.py
```

Quindi invia un payload:

```json
{
    "prompt": "Trovami tutte le posizioni senior developer disponibili"
}
```

### Deploy su AgentCore Runtime

```bash
agentcore agent deploy \
    --name needs-reader \
    --region us-east-1 \
    --entrypoint invoke
```

## Esempi di Query

- "Quali esigenze di programmazione Python ci sono?"
- "Mostrami tutti i need"
- "Cerca il need con ID: 12345"
- "Quali aziende hanno bisogno di project manager?"
- "Quali ruoli sono disponibili a Milano?"
- "Mi serve uno sviluppatore React senior"

## Struttura dell'Agente

```
agent.py
├── Configurazione Gateway MCP
├── System Prompt personalizzato
├── Funzioni di autenticazione OAuth2
├── Integrazione con Bedrock Model
└── Entrypoint AgentCore
```

## Note di Sviluppo

- L'agente utilizza Claude Sonnet 4 come modello di base
- La ricerca è case-insensitive e supporta regex
- Massimo 1000 need per singola query (configurabile)
- La connessione al gateway è auto-autenticante tramite OAuth2

## Troubleshooting

Se riscontri errori:

1. **Errore di autenticazione**: Verifica `GATEWAY_CLIENT_ID` e `GATEWAY_CLIENT_SECRET`
2. **Gateway non raggiungibile**: Controlla `GATEWAY_MCP_URL`
3. **Token scaduto**: Il token viene rigenerato automaticamente ad ogni richiesta
4. **Nessun risultato**: Verifica che MongoDB sia accessibile dalla Lambda

## Prossimi Passi

- Aggiungere supporto per filtri avanzati (data, priorità, etc.)
- Implementare caching dei risultati
- Aggiungere feedback user per migliorare le ricerche
