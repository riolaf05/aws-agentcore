# Telegram to Agent Script

Script standalone per ricevere messaggi dal bot Telegram e inviarli all'Orchestrator Agent AWS.

## Funzionalità

- Riceve messaggi testuali dal bot Telegram (tramite polling)
- Inoltra i messaggi all'Orchestrator Agent AWS Lambda
- Verifica l'autorizzazione degli utenti tramite Chat ID
- Gestisce risposte e errori dall'agent

## Configurazione

### 1. Variabili d'ambiente (.env)

Crea o modifica il file `.env` nella root del progetto:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_telegram_chat_id

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your_aws_account_id
LAMBDA_ORCHESTRATOR_ARN=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:PersonalAssistant-Orchestrator

# MCP Server (opzionale)
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=your_mcp_api_key
```

### 2. Come ottenere il Chat ID Telegram

1. Avvia una conversazione con il bot [@userinfobot](https://t.me/userinfobot)
2. Il bot ti risponderà con il tuo Chat ID
3. Copia il numero e inseriscilo in `TELEGRAM_CHAT_ID`

### 3. AWS Credentials

Assicurati di avere configurato le credenziali AWS:

```bash
aws configure
```

O imposta le variabili d'ambiente:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## Installazione

```bash
# Installa dipendenze
pip install -r requirements.txt
```

## Utilizzo

### Modalità Polling (per testing locale)

```bash
python scripts/telegram_to_agent.py
```

Il bot si avvierà in modalità polling e riceverà tutti i messaggi in tempo reale.

### Logs

Lo script utilizza il modulo `logging` di Python. Per aumentare il livello di dettaglio:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Integrazione con AWS Lambda

Per utilizzare questo codice come webhook Lambda invece che polling:

1. Il webhook Lambda è già implementato in `lambdas/telegram-webhook/bot.py`
2. Deploy dello stack CDK configura automaticamente il webhook
3. Configura l'URL webhook in Telegram tramite BotFather

## Flusso dei messaggi

```
Utente Telegram
    ↓
[telegram_to_agent.py o webhook Lambda]
    ↓
Orchestrator Agent (AWS Lambda)
    ↓
Task Manager / Daily Briefing / MCP Server
    ↓
Risposta all'utente
```

## Sicurezza

- **Autorizzazione**: Solo i Chat ID configurati in `TELEGRAM_CHAT_ID` possono usare il bot
- **API Key**: Le credenziali MCP sono salvate in AWS Secrets Manager
- **IAM Roles**: Lambda ha permessi minimi necessari

## Troubleshooting

### Bot non risponde

1. Verifica che `TELEGRAM_BOT_TOKEN` sia corretto
2. Controlla che il tuo Chat ID sia in `TELEGRAM_CHAT_ID`
3. Verifica i log per errori di connessione

### Errore Lambda

1. Verifica che `LAMBDA_ORCHESTRATOR_ARN` sia corretto
2. Controlla che le credenziali AWS siano valide
3. Verifica i log CloudWatch della Lambda

### Timeout

Se l'agent impiega molto tempo:
```python
# Aumenta il timeout nella configurazione
timeout=60  # secondi
```

## MCP Server Integration

Per invocare un server MCP esterno:

```python
from shared.utils.mcp_client import create_mcp_client

# Crea client
mcp = create_mcp_client()

# Lista tool disponibili
tools = mcp.list_tools()

# Invoca un tool
result = mcp.invoke_tool('tool_name', {'param': 'value'})
```

## Testing

```bash
# Test manuale
python scripts/telegram_to_agent.py

# Invia un messaggio al bot
# Il messaggio verrà processato e vedrai i log
```

## Note

- Lo script usa **polling** per semplicità di testing locale
- In produzione, usa il **webhook Lambda** per migliori performance
- I messaggi sono processati in modo sincrono (uno alla volta)
