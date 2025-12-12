# Riepilogo Modifiche - Integrazione Telegram e MCP

## Modifiche Implementate

### 1. Script Telegram to Agent (`scripts/telegram_to_agent.py`)

✅ **Creato nuovo script standalone** per ricevere messaggi testuali dal bot Telegram e inviarli all'Orchestrator Agent.

**Caratteristiche:**
- Modalità polling per testing locale
- Verifica autorizzazione tramite Chat ID
- Invocazione asincrona dell'Orchestrator Lambda
- Gestione errori e logging dettagliato
- Support per metadata utente (user_id, chat_id, username)

**Utilizzo:**
```bash
python scripts/telegram_to_agent.py
```

### 2. Client MCP Esterno (`shared/utils/mcp_client.py`)

✅ **Creata libreria per invocare server MCP esterni** tramite HTTPS con x-api-key.

**Funzionalità:**
- `invoke_tool()` - Invoca tool MCP
- `list_tools()` - Elenca tool disponibili
- `invoke_prompt()` - Invoca prompt MCP
- `get_resources()` - Recupera risorse MCP
- Supporto AWS Secrets Manager per credenziali
- Headers HTTP con `x-api-key` per autenticazione
- Timeout configurabili
- Error handling robusto

**Esempio:**
```python
from shared.utils.mcp_client import create_mcp_client

mcp = create_mcp_client()
result = mcp.invoke_tool('tool_name', {'param': 'value'})
```

### 3. Aggiornamento Orchestrator Agent (`agents/orchestrator/agent.py`)

✅ **Aggiunti nuovi tool per MCP:**
- `invoke_mcp_tool()` - Invoca tool su server MCP esterno
- `list_mcp_tools()` - Lista tool MCP disponibili
- Lazy loading del client MCP
- Integration nel system prompt

**Capacità:**
L'Orchestrator ora può:
1. Gestire task tramite Task Manager
2. Generare briefing tramite Daily Briefing
3. **Invocare tool MCP esterni tramite HTTPS**
4. **Scoprire dinamicamente tool MCP disponibili**

### 4. Stack CDK Aggiornato (`infrastructure/cdk-app/lib/personal-assistant-stack.ts`)

✅ **Modifiche:**

#### a) Secret MCP aggiornato
```typescript
const mcpApiKeySecret = new secretsmanager.Secret(this, 'MCPApiKey', {
  secretName: 'personal-assistant/mcp-api-key',
  description: 'MCP Server API Key for external MCP server',
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ apiKey: '', url: '' }),
    generateStringKey: 'generated',
  },
});
```

#### b) Integrazione Outlook DISABILITATA
La lambda per leggere messaggi Outlook è stata commentata. Per riabilitarla:
```typescript
// Decommenta la sezione "OUTLOOK INTEGRATION (DISABLED)"
```

#### c) MCP support negli agent
- `orchestratorLambda` ha accesso al secret MCP
- `dailyBriefingLambda` usa `MCP_SECRET_NAME` invece di URL hardcoded
- Grant read permissions sul secret

### 5. Variabili d'ambiente aggiornate (`.env`)

✅ **Nuove variabili:**
```env
# Telegram
TELEGRAM_CHAT_ID=<your_telegram_chat_id>
LAMBDA_ORCHESTRATOR_ARN=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:PersonalAssistant-Orchestrator

# MCP Esterno
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=<tua_chiave_api_mcp>
MCP_SECRET_NAME=personal-assistant/mcp-api-key

# Outlook (DISABILITATO)
# AZURE_CLIENT_ID=<client_id>
# AZURE_CLIENT_SECRET=<client_secret>
# AZURE_TENANT_ID=<tenant_id>
```

### 6. Documentazione (`scripts/README_telegram.md`)

✅ **Creata guida completa** per:
- Setup script Telegram to Agent
- Configurazione variabili d'ambiente
- Come ottenere Chat ID Telegram
- Troubleshooting
- Integrazione MCP

## Flusso dei Messaggi

```
┌─────────────────┐
│ Utente Telegram │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────┐
│ telegram_to_agent.py (polling) │
│ o webhook Lambda               │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Orchestrator Agent     │
│ (AWS Lambda)           │
└────┬───────────────┬───┘
     │               │
     ▼               ▼
┌─────────┐   ┌──────────────┐
│Task Mgr │   │Daily Briefing│
└─────────┘   └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │ MCP Server   │
              │ (HTTPS)      │
              └──────────────┘
```

## Setup Post-Deploy

### 1. Configura Secret MCP in AWS

```bash
aws secretsmanager update-secret \
  --secret-id personal-assistant/mcp-api-key \
  --secret-string '{"url":"https://your-mcp-server.com","apiKey":"your-api-key"}'
```

### 2. Configura Token Telegram

```bash
aws secretsmanager update-secret \
  --secret-id personal-assistant/telegram-bot-token \
  --secret-string '{"token":"YOUR_BOT_TOKEN"}'
```

### 3. Deploy dello Stack

```bash
cd infrastructure/cdk-app
cdk deploy
```

### 4. Configura Webhook Telegram (Opzionale)

Se usi webhook invece di polling:
```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<API_GATEWAY_URL>/webhook"
```

### 5. Test Script Locale

```bash
# Assicurati di avere configurato .env
python scripts/telegram_to_agent.py
```

## Testing

### Test MCP Client
```python
from shared.utils.mcp_client import create_mcp_client

mcp = create_mcp_client()

# Lista tool
tools = mcp.list_tools()
print(tools)

# Invoca tool
result = mcp.invoke_tool('example_tool', {'param': 'value'})
print(result)
```

### Test Script Telegram
1. Avvia lo script: `python scripts/telegram_to_agent.py`
2. Invia un messaggio al bot Telegram
3. Verifica nei log che il messaggio viene ricevuto e processato
4. Controlla la risposta sul bot

## Sicurezza

✅ **Implementate le seguenti misure:**
1. **Autorizzazione Telegram**: Solo Chat ID configurati possono usare il bot
2. **AWS Secrets Manager**: Credenziali MCP e token Telegram protetti
3. **x-api-key**: Autenticazione HTTP per server MCP
4. **IAM Roles**: Permessi minimi necessari per Lambda
5. **HTTPS**: Comunicazione criptata con MCP server

## Note Importanti

- ⚠️ **Outlook disabilitato**: L'integrazione Outlook è commentata nello stack CDK
- ✅ **MCP esterno**: Usa HTTPS con x-api-key per invocare server MCP
- ✅ **Polling vs Webhook**: Lo script usa polling per semplicità, webhook Lambda per produzione
- ✅ **Lazy loading**: Il client MCP viene inizializzato solo quando necessario

## Prossimi Passi

1. Deploy dello stack aggiornato: `cdk deploy`
2. Configura i secret AWS con credenziali reali
3. Ottieni il Chat ID Telegram tramite @userinfobot
4. Aggiorna `.env` con i valori corretti
5. Test del flusso end-to-end

## Troubleshooting

### MCP non risponde
- Verifica URL e API key nel secret AWS
- Controlla i log Lambda CloudWatch
- Test manuale: `curl -H "x-api-key: KEY" https://mcp-server.com/tools`

### Bot Telegram non riceve messaggi
- Verifica `TELEGRAM_CHAT_ID` in `.env`
- Controlla token bot con @BotFather
- Verifica credenziali AWS

### Errori Lambda
- Controlla CloudWatch Logs
- Verifica IAM permissions
- Test payload manualmente nella console AWS
