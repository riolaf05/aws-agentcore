# Setup e Deploy - Personal Assistant Suite

Questa guida ti accompagnerà passo-passo nel setup e deploy della suite completa.

## 📋 Prerequisiti

### 1. Account e Credenziali

- **AWS Account** con accesso amministrativo
- **Telegram Bot Token** (da [@BotFather](https://t.me/botfather))
- **Microsoft 365 Account** per Outlook
- **Azure AD App** registrata per Outlook API

### 2. Software Richiesto

```bash
# Python 3.11+
python --version

# Node.js 18+ (per CDK)
node --version

# AWS CLI configurato
aws --version
aws configure

# AWS CDK CLI
npm install -g aws-cdk
cdk --version
```

## 🚀 Setup Step-by-Step

### Step 1: Clone e Setup Ambiente

```bash
# Se non l'hai già fatto
cd asws-agentcore

# Crea virtual environment Python
python -m venv venv

# Attiva venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Installa dipendenze Python
pip install -r requirements.txt
```

### Step 2: Configurazione Telegram Bot

1. **Crea Bot con BotFather:**
   ```
   Apri Telegram → cerca @BotFather
   /newbot
   Nome: Personal Assistant Bot
   Username: your_assistant_bot
   
   Copia il TOKEN ricevuto
   ```

2. **Ottieni tuo Chat ID:**
   ```
   Invia messaggio al bot
   Visita: https://api.telegram.org/bot<TOKEN>/getUpdates
   Copia il "chat" -> "id"
   ```

### Step 3: Configurazione Azure AD (Outlook)

1. **Registra App in Azure Portal:**
   - Vai a [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
   - "New registration"
   - Nome: "Personal Assistant Outlook"
   - Supported account types: "Single tenant"
   - Registra

2. **Configura Permessi:**
   - API permissions → Add permission
   - Microsoft Graph → Application permissions
   - Aggiungi:
     - `Mail.Read`
     - `Mail.ReadBasic.All`
     - `User.Read.All`
   - "Grant admin consent"

3. **Crea Client Secret:**
   - Certificates & secrets → New client secret
   - Descrizione: "MCP Server"
   - Expiry: 24 months
   - **Copia subito il secret** (non lo rivedrai)

4. **Annota:**
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret value

### Step 4: Configurazione Variabili d'Ambiente

Crea file `.env` nella root (copia da `.env.example`):

```bash
# Copia template
cp .env.example .env

# Modifica con i tuoi valori
notepad .env  # o usa il tuo editor
```

**Compila con i tuoi valori:**
```env
AWS_REGION=eu-west-1
AWS_ACCOUNT_ID=123456789012

TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

OUTLOOK_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OUTLOOK_CLIENT_SECRET=your-secret-value-here
OUTLOOK_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

MCP_API_KEY=$(openssl rand -hex 32)  # Genera random key
```

### Step 5: Deploy Infrastructure con CDK

```bash
cd infrastructure/cdk-app

# Installa dipendenze Node.js
npm install

# Bootstrap CDK (prima volta)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Preview changes
cdk diff

# Deploy!
cdk deploy PersonalAssistantStack

# Conferma quando richiesto
```

**Output importanti:**
- `TaskApiEndpoint`: URL API Gateway per task
- `TelegramWebhookUrl`: URL da configurare in Telegram
- Lambda ARNs: Necessari per configurazione agenti

### Step 6: Deploy MCP Server

Il MCP server può essere deployato in diversi modi:

#### Opzione A: AWS ECS Fargate (Consigliato)

```bash
# TODO: Implementare deployment ECS
# Per ora, usa opzione B per testing
```

#### Opzione B: Server Locale (Testing)

```bash
cd mcp-server

# Installa dipendenze
pip install -r requirements.txt

# Avvia server
python server.py

# Server in ascolto su http://localhost:8000
```

#### Opzione C: AWS Lambda + API Gateway

```bash
# Configura Lambda per MCP server
# (Aggiungi layer Python con dipendenze)
```

### Step 7: Crea Bedrock Agents

**Nota:** Bedrock Agents devono essere creati manualmente nella Console AWS.

1. **Vai a AWS Bedrock Console** → Agents

2. **Crea Orchestrator Agent:**
   - Nome: `OrchestratorAgent`
   - Model: Claude 3 Sonnet
   - Import configurazione da: `agents/orchestrator/agent-config.json`
   - Action Groups:
     - TaskManagerInvoker → Lambda: `PersonalAssistant-TaskManager`
     - DailyBriefingInvoker → Lambda: `PersonalAssistant-DailyBriefing`
   - Crea & Prepara

3. **Crea Task Manager Agent:**
   - Nome: `TaskManagerAgent`
   - Model: Claude 3 Sonnet
   - Import da: `agents/task-manager/agent-config.json`
   - Action Group: TaskDatabaseAPI → Lambda: `PersonalAssistant-TaskPost`
   - Crea & Prepara

4. **Crea Daily Briefing Agent:**
   - Nome: `DailyBriefingAgent`
   - Model: Claude 3 Sonnet
   - Import da: `agents/daily-briefing/agent-config.json`
   - Action Groups:
     - TaskRetrieval → Lambda: `PersonalAssistant-TaskGet`
     - OutlookMCP → Lambda: (crea Lambda wrapper per MCP)
   - Crea & Prepara

5. **Aggiorna Lambda Environment Variables:**
   
   Nella Lambda `PersonalAssistant-Orchestrator`, aggiorna:
   ```
   BEDROCK_AGENT_ID_TASK_MANAGER=<agent-id-task-manager>
   BEDROCK_AGENT_ID_DAILY_BRIEFING=<agent-id-daily-briefing>
   ```

### Step 8: Configura Telegram Webhook

```bash
# Ottieni webhook URL da CDK output
WEBHOOK_URL="<TelegramWebhookUrl-from-cdk>"

# Configura webhook
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$WEBHOOK_URL\"}"

# Verifica
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

### Step 9: Store Secrets in AWS Secrets Manager

```bash
# Store Telegram token
aws secretsmanager put-secret-value \
  --secret-id personal-assistant/telegram-bot-token \
  --secret-string "{\"token\":\"$TELEGRAM_BOT_TOKEN\"}"

# Store MCP API key
aws secretsmanager put-secret-value \
  --secret-id personal-assistant/mcp-api-key \
  --secret-string "$MCP_API_KEY"

# Store Outlook credentials
aws secretsmanager create-secret \
  --name personal-assistant/outlook-credentials \
  --secret-string "{
    \"client_id\":\"$OUTLOOK_CLIENT_ID\",
    \"client_secret\":\"$OUTLOOK_CLIENT_SECRET\",
    \"tenant_id\":\"$OUTLOOK_TENANT_ID\"
  }"
```

### Step 10: Test la Suite

1. **Test Task API:**
   ```bash
   # POST task
   curl -X POST "$TASK_API_ENDPOINT/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "tasks": [{
         "title": "Test task",
         "description": "Testing API",
         "priority": "high",
         "due_date": "2024-12-31"
       }]
     }'
   
   # GET tasks
   curl "$TASK_API_ENDPOINT/tasks?status=pending"
   ```

2. **Test MCP Server:**
   ```bash
   curl -X GET "http://localhost:8000/health"
   
   curl -X POST "http://localhost:8000/tools/invoke" \
     -H "Authorization: Bearer $MCP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "tool": "outlook_get_emails",
       "parameters": {
         "folder": "inbox",
         "max_results": 5
       }
     }'
   ```

3. **Test Telegram Bot:**
   ```
   Apri Telegram
   Trova il tuo bot
   Invia: /start
   Invia: "Voglio imparare Python"
   Invia: /briefing
   ```

## 🔧 Troubleshooting

### Errore: "Bedrock Agent not found"

Assicurati di aver creato gli agenti Bedrock e aggiornato gli ID nelle env variables.

### Errore: "Outlook authentication failed"

Verifica:
- Azure AD app configurata correttamente
- Permessi granted (admin consent)
- Client secret non scaduto
- Tenant ID corretto

### Errore: "DynamoDB access denied"

Verifica IAM permissions delle Lambda functions.

### Telegram non risponde

Verifica:
- Webhook configurato correttamente (`getWebhookInfo`)
- Chat ID corretto in `AUTHORIZED_USERS`
- Lambda ha permessi per invoke altre Lambda

## 📊 Monitoring

### CloudWatch Logs

```bash
# Logs Orchestrator
aws logs tail /aws/lambda/PersonalAssistant-Orchestrator --follow

# Logs Task Manager
aws logs tail /aws/lambda/PersonalAssistant-TaskManager --follow

# Logs Daily Briefing
aws logs tail /aws/lambda/PersonalAssistant-DailyBriefing --follow
```

### CloudWatch Metrics

Vai a CloudWatch Console → Metrics → Lambda per vedere:
- Invocations
- Duration
- Errors
- Throttles

### Cost Explorer

Monitora costi su AWS Cost Explorer:
- Bedrock Agent invocations
- Lambda executions
- DynamoDB requests
- API Gateway calls

## 🗑️ Cleanup (Rimozione)

```bash
# Rimuovi stack CDK
cd infrastructure/cdk-app
cdk destroy PersonalAssistantStack

# Rimuovi manualmente:
# - Bedrock Agents (console)
# - Secrets Manager secrets
# - CloudWatch Log Groups (se vuoi cancellare logs)
```

## 🎉 Deploy Completato!

La tua suite è ora operativa! Usa il bot Telegram per interagire con i tuoi agenti.

**Prossimi step:**
- Personalizza prompt degli agenti
- Aggiungi nuovi tool al MCP server
- Configura notification aggiuntive
- Ottimizza costi monitorando usage

---

Per domande o problemi, consulta [docs/troubleshooting.md](troubleshooting.md)
