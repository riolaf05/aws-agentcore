# 🚀 Deployment Guide - AWS Bedrock AgentCore

Questa guida ti porta passo-passo nel deployment della suite di agenti su AWS usando Bedrock AgentCore Runtime.

## 📋 Prerequisiti

1. **Account AWS** configurato con:
   - AWS CLI installato e configurato (`aws configure`)
   - Credenziali con permessi per: Bedrock, ECR, Lambda, DynamoDB, API Gateway, EventBridge
   
2. **Tool locali**:
   - Python 3.11+ installato
   - AWS CLI v2
   - Docker Desktop (opzionale, ma consigliato per build locali)
   - PowerShell 7+ (su Windows)

3. **Bedrock AgentCore Starter Toolkit**:
   ```powershell
   pip install bedrock-agentcore-starter-toolkit strands-agents bedrock-agentcore
   ```

4. **Configurazione Telegram Bot**:
   - Crea un bot su [@BotFather](https://t.me/BotFather)
   - Salva il token ricevuto

5. **Configurazione Microsoft Graph** (per MCP Outlook):
   - Registra app su [Azure Portal](https://portal.azure.com)
   - Abilita permessi: `Mail.Read`, `Mail.ReadBasic`
   - Genera Client ID e Client Secret

---

## 🏗️ Fase 1: Infrastruttura Base

### Step 1.1: Deploy Infrastruttura AWS con CDK

```powershell
cd infrastructure/cdk-app

# Installa dipendenze
npm install

# Bootstrap CDK (prima volta only)
cdk bootstrap

# Deploy stack (DynamoDB, Lambda API, Telegram webhook, etc)
cdk deploy --require-approval never
```

**Output importante**: salva gli ARN delle Lambda e della tabella DynamoDB.

### Step 1.2: Configura Variabili d'Ambiente

Crea il file `.env` nella root del progetto:

```bash
# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Telegram Bot
TELEGRAM_BOT_TOKEN=<tuo_token>
TELEGRAM_WEBHOOK_URL=<api_gateway_url_da_cdk_output>

# Task API Lambda ARNs (da CDK output)
LAMBDA_TASK_POST_ARN=arn:aws:lambda:us-east-1:123456789012:function:TaskPost
LAMBDA_TASK_GET_ARN=arn:aws:lambda:us-east-1:123456789012:function:TaskGet

# MCP Server (da configurare dopo deploy MCP)
MCP_SERVER_URL=http://localhost:8000
MCP_API_KEY=<tua_chiave_sicura>

# Microsoft Graph (per MCP Outlook)
AZURE_CLIENT_ID=<client_id>
AZURE_CLIENT_SECRET=<client_secret>
AZURE_TENANT_ID=<tenant_id>

# Bedrock AgentCore (compilerai dopo deploy agenti)
TASK_MANAGER_AGENT_ARN=
DAILY_BRIEFING_AGENT_ARN=
```

---

## 🤖 Fase 2: Deploy Agenti su Bedrock AgentCore

Ci sono due approcci: **Cloud Build** (raccomandato) o **Local Build**.

### Opzione A: Cloud Build con AWS CodeBuild (Raccomandato)

Usa lo script PowerShell automatizzato:

```powershell
# Deploy tutti e 3 gli agenti
.\scripts\deploy.ps1
```

Lo script esegue per ogni agente:
1. Crea repository ECR se non esiste
2. Configura CodeBuild per build ARM64
3. Pusha il codice e avvia la build cloud
4. Deploya l'agente su Bedrock AgentCore Runtime
5. Salva gli ARN per configurazione

### Opzione B: Local Build con Docker

Se hai Docker Desktop e vuoi buildare localmente:

```powershell
# Orchestrator Agent
cd agents/orchestrator
agentcore configure -e agent.py --runtime-arch ARM64
agentcore launch

# Task Manager Agent
cd ../task-manager
agentcore configure -e agent.py --runtime-arch ARM64
agentcore launch

# Daily Briefing Agent
cd ../daily-briefing
agentcore configure -e agent.py --runtime-arch ARM64
agentcore launch
```

**Nota**: Il build locale richiede Docker con supporto ARM64 (Apple Silicon nativo o emulazione).

### Step 2.1: Verifica Deploy Agenti

Dopo il deploy, verifica gli agent runtime:

```powershell
# Lista tutti gli agent runtime
aws bedrock-agentcore list-agent-runtimes --region us-east-1

# Testa orchestrator
agentcore invoke \
  --agent-runtime-arn <orchestrator_arn> \
  --prompt "Ciao, cosa puoi fare?"

# Testa task manager
agentcore invoke \
  --agent-runtime-arn <task_manager_arn> \
  --prompt "Voglio imparare Python entro 3 mesi"

# Testa daily briefing
agentcore invoke \
  --agent-runtime-arn <daily_briefing_arn> \
  --prompt "Dammi il briefing di oggi"
```

### Step 2.2: Aggiorna Variabili d'Ambiente

Aggiorna `.env` con gli ARN ricevuti:

```bash
TASK_MANAGER_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/task-manager-xyz
DAILY_BRIEFING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/daily-briefing-xyz
```

### Step 2.3: Ri-deploy Orchestrator con ARN Sub-Agenti

L'orchestrator ha bisogno degli ARN degli altri agenti nelle sue environment variables:

```powershell
cd agents/orchestrator

# Aggiorna .bedrock_agentcore.yaml con environment variables
# Poi ri-deploy
agentcore launch --update
```

---

## 🌐 Fase 3: Deploy MCP Server (Outlook Integration)

### Step 3.1: Deploy MCP Server su AWS Lambda o EC2

**Opzione Lambda** (serverless):

```powershell
cd mcp-server

# Package con dependencies
pip install -r requirements.txt -t package/
cp server.py package/
cd package
zip -r ../mcp-server.zip .

# Deploy Lambda
aws lambda create-function \
  --function-name MCPOutlookServer \
  --runtime python3.11 \
  --role <execution_role_arn> \
  --handler server.app \
  --zip-file fileb://../mcp-server.zip \
  --environment Variables="{AZURE_CLIENT_ID=...,AZURE_CLIENT_SECRET=...,MCP_API_KEY=...}"

# Crea Function URL per HTTP endpoint
aws lambda create-function-url-config \
  --function-name MCPOutlookServer \
  --auth-type NONE
```

**Opzione EC2/ECS** (long-running):

```powershell
# Build e push Docker image
docker build -t mcp-outlook-server .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag mcp-outlook-server:latest <account>.dkr.ecr.us-east-1.amazonaws.com/mcp-outlook-server:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/mcp-outlook-server:latest

# Deploy su ECS Fargate (via CDK o Console)
```

### Step 3.2: Testa MCP Server

```powershell
# Health check
curl http://<mcp_server_url>/health

# Test tool invocation
curl -X POST http://<mcp_server_url>/tools/invoke \
  -H "Authorization: Bearer <MCP_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "outlook_get_emails",
    "parameters": {
      "folder": "inbox",
      "max_results": 5
    }
  }'
```

---

## 📱 Fase 4: Configura Telegram Bot

### Step 4.1: Set Webhook

```powershell
# Usa l'URL API Gateway dal CDK output
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=<TELEGRAM_WEBHOOK_URL>"

# Verifica webhook
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

### Step 4.2: Aggiorna Lambda Telegram con Orchestrator ARN

La Lambda `telegram-webhook` deve invocare l'orchestrator agent. Aggiorna CDK:

```typescript
// In lib/personal-assistant-stack.ts
const telegramWebhook = new lambda.Function(this, 'TelegramWebhook', {
  // ... existing config
  environment: {
    ORCHESTRATOR_AGENT_ARN: '<orchestrator_arn>',
    // ... altri env vars
  }
});
```

Ri-deploy:

```powershell
cd infrastructure/cdk-app
cdk deploy
```

---

## ⏰ Fase 5: Configura Daily Briefing Automatico

### Step 5.1: Crea EventBridge Rule

```powershell
# Crea rule per trigger giornaliero alle 8:00 AM
aws events put-rule \
  --name DailyBriefingTrigger \
  --schedule-expression "cron(0 8 * * ? *)" \
  --state ENABLED

# Aggiungi target (Lambda che invoca Daily Briefing Agent)
aws events put-targets \
  --rule DailyBriefingTrigger \
  --targets "Id"="1","Arn"="<lambda_trigger_briefing_arn>"
```

La Lambda di trigger invoca il Daily Briefing Agent e invia il risultato su Telegram.

---

## ✅ Fase 6: Test End-to-End

### Test 1: Creazione Task

Invia su Telegram:
```
Voglio imparare AWS entro 2 mesi
```

**Output atteso**: 
- Orchestrator analizza intent → invoca Task Manager
- Task Manager decompone in 4-6 task SMART
- Lambda POST salva task su DynamoDB
- Conferma su Telegram con lista task creati

### Test 2: Briefing Giornaliero

Invia su Telegram:
```
/briefing
```

**Output atteso**:
- Orchestrator invoca Daily Briefing Agent
- Agent chiama Lambda GET per task del giorno
- Agent chiama MCP server per email Outlook
- Risposta con briefing formattato in Markdown

### Test 3: Query Task

Invia su Telegram:
```
/tasks
```

**Output atteso**:
- Lista di tutti i task attivi con priorità e scadenze

---

## 📊 Monitoraggio e Debug

### CloudWatch Logs

```powershell
# Logs orchestrator
aws logs tail /aws/bedrock-agentcore/orchestrator --follow

# Logs task manager
aws logs tail /aws/bedrock-agentcore/task-manager --follow

# Logs daily briefing
aws logs tail /aws/bedrock-agentcore/daily-briefing --follow

# Logs Lambda task API
aws logs tail /aws/lambda/TaskPost --follow
aws logs tail /aws/lambda/TaskGet --follow

# Logs Telegram webhook
aws logs tail /aws/lambda/TelegramWebhook --follow
```

### Bedrock AgentCore Observability

```powershell
# Vedi runtime status
aws bedrock-agentcore describe-agent-runtime \
  --agent-runtime-arn <arn>

# Vedi invoke history
aws bedrock-agentcore list-invocations \
  --agent-runtime-arn <arn> \
  --start-time 2025-01-20T00:00:00Z
```

### Cost Monitoring

```powershell
# Stima costi AgentCore (pay-per-use)
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity DAILY \
  --metrics "BlendedCost" \
  --filter file://bedrock-filter.json
```

---

## 🔄 Aggiornamento Agenti

Per aggiornare il codice degli agenti:

```powershell
cd agents/<agent-name>

# Modifica agent.py

# Rebuild e redeploy
agentcore launch --update

# Verifica versione
aws bedrock-agentcore describe-agent-runtime \
  --agent-runtime-arn <arn>
```

---

## 🛠️ Troubleshooting

Vedi [troubleshooting.md](./troubleshooting.md) per soluzioni a problemi comuni.

---

## 📈 Next Steps

1. **Aggiungi più agenti**: Es. agente per booking meeting, agente per ricerca info
2. **Integra più MCP tools**: Calendar, Notion, Jira, etc
3. **Migliora prompts**: Testa e ottimizza i system prompt degli agenti
4. **Dashboard**: Crea UI web per visualizzare task e analytics
5. **Multi-utente**: Estendi per supportare più utenti con autenticazione

---

## 💰 Prezzi Stimati

**Bedrock AgentCore Runtime** (pay-per-use):
- Compute: $0.00003 per second di execution
- Storage: $0.10 per GB-month

**DynamoDB** (pay-per-request):
- Write: $1.25 per milione di richieste
- Read: $0.25 per milione di richieste

**Lambda**:
- First 1M requests free, poi $0.20 per milione

**Stima mensile** (uso moderato: 50 interazioni/giorno):
- AgentCore: ~$5-10
- DynamoDB: ~$1
- Lambda: ~$0.50
- **Totale: ~$7-12/mese** ✅ Pay-per-use!

---

**Buon lavoro! 🚀**
