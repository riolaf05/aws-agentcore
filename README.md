# 🤖 Personal Assistant Suite - AWS Bedrock AgentCore Edition

Una suite di agenti AI intelligenti per l'organizzazione personale, costruita con **AWS Bedrock AgentCore Runtime** e **Strands Agents**. Sistema multi-agente con pay-per-use pricing model.

---

## 🌟 Features

### 🎯 3 Agenti Specializzati

1. **Orchestrator Agent** 🎭
   - Coordina tutti gli altri agenti
   - Analizza intent e delega richieste
   - Interfaccia principale con l'utente

2. **Task Manager Agent** 📝
   - Riceve obiettivi in linguaggio naturale
   - Decompone in task SMART actionable
   - Persiste su DynamoDB

3. **Daily Briefing Agent** 📊
   - Riassunto giornaliero automatico
   - Legge task dal database
   - Integra email da Outlook (via MCP)

### 💬 Interfaccia Telegram

- Chat interattiva
- Comandi: `/briefing`, `/tasks`, `/add <obiettivo>`
- Notifiche push
- Supporto Markdown

### 🔌 Integrazioni

- **AgentCore Gateway**: Secure Lambda access with OAuth2 + MCP protocol
- **DynamoDB**: Persistence layer per task
- **MCP Server**: Model Context Protocol per Outlook
- **Microsoft Graph**: Email e calendar access
- **EventBridge**: Scheduled daily briefings (8:00 AM)

### 💰 Architettura Pay-Per-Use

- **Bedrock AgentCore Runtime**: $0.00003/sec di esecuzione
- **DynamoDB On-Demand**: $1.25/milione write
- **Lambda**: Primo milione free
- **Stima mensile**: ~$7-12 per uso moderato

---

## 🏗️ Architettura

```
┌─────────────┐
│  Telegram   │
│    Bot      │
└──────┬──────┘
       │
       v
┌──────────────────┐      ┌───────────────┐
│  API Gateway     │─────>│  Orchestrator │
│  (Webhook)       │      │     Agent     │
└──────────────────┘      └───────┬───────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    v                           v
          ┌──────────────────┐      ┌──────────────────┐
          │  Task Manager    │      │ Daily Briefing   │
          │     Agent        │      │     Agent        │
          └────────┬─────────┘      └────────┬─────────┘
                   │                         │
                   │  ┌──────────────────┐   │
                   └─>│  AgentCore       │<──┘
                      │    Gateway       │
                      │  (OAuth2 + MCP)  │
                      └────────┬─────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                v                             v
          ┌────────────────┐       ┌────────────────┐
          │ Lambda Task API│       │  MCP Server    │
          │  (DynamoDB)    │       │   (Outlook)    │
          └────────────────┘       └────────────────┘
```

**Framework Stack**:
- **BedrockAgentCore**: Runtime container-based su AWS
- **AgentCore Gateway**: Secure MCP endpoint with OAuth2
- **Strands Agents**: Python agent framework con tool orchestration
- **AWS CDK**: Infrastructure as Code (TypeScript)
- **Docker**: Containerizzazione agenti (ARM64)

---

## 📁 Struttura Progetto

```
asws-agentcore/
├── agents/                          # AI Agents (Bedrock AgentCore)
│   ├── gateway_client.py           # Shared Gateway client with OAuth2
│   ├── orchestrator/
│   │   ├── agent.py                # Main orchestrator logic
│   │   ├── requirements.txt        # Dependencies
│   │   └── Dockerfile              # ARM64 container
│   ├── task-manager/
│   │   ├── agent.py                # Task decomposition logic
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── daily-briefing/
│       ├── agent.py                # Briefing generation logic
│       ├── requirements.txt
│       └── Dockerfile
│
├── lambdas/                         # Support Lambda Functions
│   ├── task-api/
│   │   ├── post_task.py           # POST /tasks - Create tasks
│   │   ├── get_task.py            # GET /tasks - Query tasks
│   │   └── requirements.txt
│   └── telegram-webhook/
│       ├── bot.py                  # Telegram bot handler
│       └── requirements.txt
│
├── mcp-server/                      # Model Context Protocol Server
│   ├── server.py                   # FastAPI MCP server
│   ├── requirements.txt
│   └── Dockerfile
│
├── infrastructure/                  # AWS Infrastructure
│   └── cdk-app/
│       ├── lib/
│       │   └── personal-assistant-stack.ts
│       ├── bin/
│       │   └── cdk-app.ts
│       ├── package.json
│       └── tsconfig.json
│
├── shared/                          # Shared utilities
│   ├── models/
│   │   └── data_models.py          # Task, Email, Briefing models
│   └── utils/
│       └── helpers.py              # Common utilities
│
├── docs/                            # Documentation
│   ├── DEPLOYMENT.md               # Step-by-step deploy guide
│   ├── SETUP.md                    # Initial setup
│   └── troubleshooting.md          # Common issues
│
├── scripts/                         # Automation scripts
│   ├── deploy.ps1                  # Automated deployment (PowerShell)
│   └── test.ps1                    # End-to-end testing
│
├── README.md                        # This file
├── requirements.txt                 # Global Python dependencies
└── .env.example                     # Environment variables template
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI v2 configured with appropriate permissions
- AWS CDK (`npm install -g aws-cdk`)
- Bedrock AgentCore Toolkit (`pip install bedrock-agentcore-starter-toolkit`)
- Telegram Bot Token (da [@BotFather](https://t.me/BotFather))
- Azure App Registration (per Outlook MCP) *(opzionale)*

### Installazione

#### 1. Setup Progetto

```powershell
# Clone repository
git clone <repo-url>
cd asws-agentcore

# Installa dipendenze Python globali
pip install -r requirements.txt
pip install bedrock-agentcore-starter-toolkit strands-agents

# Copia e configura .env
copy .env.example .env
# Modifica .env con i tuoi valori (AWS_ACCOUNT_ID, TELEGRAM_BOT_TOKEN, etc)
```

#### 2. Deploy Infrastruttura Base (CDK)

```powershell
cd infrastructure/cdk-app

# Installa dipendenze CDK
npm install

# Bootstrap CDK (solo prima volta)
cdk bootstrap

# Deploy stack
cdk deploy --require-approval never

# Salva gli output (ARN Lambda, API Gateway URL, etc)
cdk outputs --json > outputs.json
```

Gli output includeranno:
- `TaskPostLambdaArn` - Lambda per creare task
- `TaskGetLambdaArn` - Lambda per query task
- `TelegramWebhookUrl` - URL webhook per Telegram

#### 3. Deploy Agenti su Bedrock AgentCore

**Orchestrator Agent**:
```powershell
cd agents/orchestrator

# Configura agent
agentcore configure -e agent.py --non-interactive

# Deploy
agentcore launch

# Salva ARN (mostrato nell'output)
# Esempio: arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/orchestrator-xyz
```

**Task Manager Agent**:
```powershell
cd ../task-manager

agentcore configure -e agent.py --non-interactive
agentcore launch
# Salva ARN
```

**Daily Briefing Agent**:
```powershell
cd ../daily-briefing

agentcore configure -e agent.py --non-interactive
agentcore launch
# Salva ARN
```

#### 4. Configura AgentCore Gateway per Secure Lambda Access

**📘 Guida Completa**: Vedi [docs/GATEWAY_SETUP.md](docs/GATEWAY_SETUP.md) per dettagli completi.

Il Gateway fornisce accesso sicuro e autenticato alle Lambda Task API tramite OAuth2.

```powershell
# Crea Gateway MCP
agentcore gateway create-mcp-gateway `
    --name TaskAPIGateway `
    --description "Gateway sicuro per Task API" `
    --region us-east-1

# Output: gateway-id, gateway-url, cognito credentials
# Salva questi valori per lo step 5
```

Aggiungi Lambda targets per POST e GET:

```powershell
# Target per save_task (POST)
agentcore gateway create-mcp-gateway-target `
    --gateway-arn <gateway-arn> `
    --gateway-url <gateway-url> `
    --role-arn <iam-role-arn> `
    --name save_task `
    --target-type lambda `
    --target-payload '{
      "arn": "<TaskPostLambdaArn>",
      "tools": [{
        "name": "save_task",
        "description": "Save tasks to database",
        "inputSchema": {
          "type": "object",
          "properties": {
            "tasks": {"type": "array"}
          }
        }
      }]
    }'

# Target per get_tasks (GET)
agentcore gateway create-mcp-gateway-target `
    --gateway-arn <gateway-arn> `
    --gateway-url <gateway-url> `
    --role-arn <iam-role-arn> `
    --name get_tasks `
    --target-type lambda `
    --target-payload '{
      "arn": "<TaskGetLambdaArn>",
      "tools": [{
        "name": "get_tasks",
        "description": "Retrieve tasks from database",
        "inputSchema": {
          "type": "object",
          "properties": {
            "due_date": {"type": "string"},
            "status": {"type": "string"}
          }
        }
      }]
    }'
```

#### 5. Configura Environment Variables

#### 5. Configura Environment Variables

Aggiorna `.env` con gli ARN degli agenti deployati e le credenziali Gateway:

```bash
# ARN dagli step precedenti
ORCHESTRATOR_AGENT_ARN=arn:aws:bedrock-agentcore:...
TASK_MANAGER_AGENT_ARN=arn:aws:bedrock-agentcore:...
DAILY_BRIEFING_AGENT_ARN=arn:aws:bedrock-agentcore:...

# Lambda ARN (da CDK output)
LAMBDA_TASK_POST_ARN=arn:aws:lambda:...
LAMBDA_TASK_GET_ARN=arn:aws:lambda:...

# AgentCore Gateway Configuration (dallo step 4)
GATEWAY_MCP_URL=https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-xxx
GATEWAY_CLIENT_ID=abcd1234efgh5678
GATEWAY_CLIENT_SECRET=secret-key-here
GATEWAY_TOKEN_ENDPOINT=https://task-api-gateway.auth.us-east-1.amazoncognito.com/oauth2/token
GATEWAY_SCOPE=invoke
```

#### 6. Aggiorna Orchestrator con Sub-Agent ARN

#### 6. Aggiorna Orchestrator con Sub-Agent ARN

L'orchestrator ha bisogno degli ARN degli altri agenti:

```powershell
cd agents/orchestrator

# Modifica .bedrock_agentcore.yaml e aggiungi:
# environmentVariables:
#   TASK_MANAGER_AGENT_ARN: "arn:..."
#   DAILY_BRIEFING_AGENT_ARN: "arn:..."

# Re-deploy con nuove variabili
agentcore launch --auto-update-on-conflict
```

Task Manager e Daily Briefing necessitano delle credenziali Gateway:

```powershell
cd ../task-manager

# Modifica .bedrock_agentcore.yaml e aggiungi:
# environmentVariables:
#   GATEWAY_MCP_URL: "https://..."
#   GATEWAY_CLIENT_ID: "..."
#   GATEWAY_CLIENT_SECRET: "..."
#   GATEWAY_TOKEN_ENDPOINT: "https://..."
#   GATEWAY_SCOPE: "invoke"

agentcore launch --auto-update-on-conflict

cd ../daily-briefing
# Ripeti lo stesso per daily-briefing
agentcore launch --auto-update-on-conflict
```

#### 7. Configura Telegram Webhook

#### 7. Configura Telegram Webhook

```powershell
# Imposta webhook
$botToken = "<TUO_TELEGRAM_BOT_TOKEN>"
$webhookUrl = "<TELEGRAM_WEBHOOK_URL_DA_CDK_OUTPUT>"

curl -X POST "https://api.telegram.org/bot$botToken/setWebhook" `
  -d "url=$webhookUrl"

# Verifica
curl "https://api.telegram.org/bot$botToken/getWebhookInfo"
```

#### 8. Test Deployment

```powershell
# Test orchestrator
agentcore invoke '{"prompt": "Ciao, cosa puoi fare?"}' -a orchestrator

# Test task manager
agentcore invoke '{"prompt": "Voglio imparare Python"}' -a task-manager

# Test daily briefing
agentcore invoke '{"prompt": "Dammi il briefing"}' -a daily-briefing

# Test su Telegram
# Invia un messaggio al tuo bot
```

---

## 📖 Usage

### Telegram Commands

```
/start       - Messaggio di benvenuto
/briefing    - Riassunto giornaliero
/tasks       - Lista tutti i task
/add         - Aggiungi nuovo obiettivo

<testo>      - Messaggio libero (analizzato dall'orchestrator)
```

### Esempi Pratici

**Creare task da obiettivo**:
```
Utente: "Voglio imparare AWS entro 3 mesi"

Agente: 
✅ Ho creato 5 task per il tuo obiettivo!

1. 📚 Completare AWS Cloud Practitioner (entro 2 settimane)
2. 🔧 Hands-on con EC2 e S3 (entro 1 mese)
3. 🏗️  Progetto pratico: Deploy app su AWS (entro 2 mesi)
4. 📖 Studiare architetture serverless (entro 2.5 mesi)
5. 🎓 Prepararsi per certificazione (entro 3 mesi)

Buon lavoro! 💪
```

**Briefing giornaliero**:
```
Utente: /briefing

Agente:
🌅 **Briefing - Lunedì 20 Gennaio 2025**

📋 **Task in Programma:** (4 task)

🔴 **Urgente/Alta Priorità:**
• Completare AWS Cloud Practitioner - ⏰ Scadenza: 2025-02-03
  📝 Studiare moduli 4-6 e fare quiz pratica

🟢 **Normale:**
• Setup ambiente AWS con EC2
• Review progetto Python
• Pianificare sprint settimanale

📧 **Email Importanti:** (3 non lette)
• Meeting update - 👤 Marco Rossi
• Q4 Report - 👤 HR Team

💡 **Suggerimenti:**
• ⚠️ Scadenza importante tra 14 giorni: certificazione AWS
• 💪 Ottimo lavoro! Hai completato 7 task questa settimana

---
_Comandi utili:_
• /tasks - Vedi tutti i task
• /add <obiettivo> - Aggiungi nuovi task
```

---

## 🔧 Development

### Test Locale Agenti

Ogni agente può essere testato localmente:

```powershell
cd agents/orchestrator
python agent.py

# In altro terminale
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Ciao, cosa puoi fare?", "user_id": "test"}'
```

### Deploy Singolo Agente

```powershell
cd agents/task-manager

# Configure
agentcore configure -e agent.py --runtime-arch ARM64

# Deploy/Update
agentcore launch --update

# Test
agentcore invoke --agent-runtime-arn <arn> --prompt "Test message"
```

### Logs e Monitoring

```powershell
# CloudWatch Logs
aws logs tail /aws/bedrock-agentcore/orchestrator --follow
aws logs tail /aws/lambda/TaskPost --follow

# Agent Runtime Status
aws bedrock-agentcore describe-agent-runtime --agent-runtime-arn <arn>

# DynamoDB Table Scan
aws dynamodb scan --table-name PersonalTasks --limit 10
```

---

## 📚 Documentazione

- **[GATEWAY_SETUP.md](docs/GATEWAY_SETUP.md)**: Configurazione AgentCore Gateway (OAuth2 + MCP)
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Guida completa al deployment
- **[SETUP.md](docs/SETUP.md)**: Setup iniziale e configurazione
- **[troubleshooting.md](docs/troubleshooting.md)**: Risoluzione problemi comuni

---

## 🛠️ Tecnologie Utilizzate

| Componente | Tecnologia | Scopo |
|------------|-----------|-------|
| **Agent Framework** | Strands Agents | Orchestrazione tool e LLM |
| **Agent Runtime** | AWS Bedrock AgentCore | Container runtime pay-per-use |
| **LLM Model** | Claude Sonnet 4 | Reasoning e natural language |
| **Database** | DynamoDB | Task persistence |
| **API** | AWS Lambda + API Gateway | Task CRUD operations |
| **Bot Interface** | Telegram Bot API | User interaction |
| **External Tools** | MCP (Model Context Protocol) | Outlook integration |
| **IaC** | AWS CDK (TypeScript) | Infrastructure deployment |
| **Containerization** | Docker (ARM64) | Agent packaging |
| **Scheduling** | EventBridge | Daily briefing trigger |

---

## 🧪 Testing

### Test Locale Agenti

Ogni agente può essere testato localmente prima del deploy:

```powershell
cd agents/orchestrator
python agent.py

# In altro terminale
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Ciao, cosa puoi fare?", "user_id": "test"}'
```

### Test Remoto

```powershell
# Test orchestrator deployato
agentcore invoke '{"prompt": "Ciao"}' -a orchestrator

# Test con session ID per memory
agentcore invoke '{"prompt": "Ricordi cosa ho detto prima?"}' -a orchestrator -s session-123
```

### Test API Lambda

```powershell
# Test POST task
aws lambda invoke --function-name <TaskPostLambdaArn> \
  --payload '{"body": "{\"tasks\": [{\"title\": \"Test task\"}]}"}' \
  response.json

# Test GET task
aws lambda invoke --function-name <TaskGetLambdaArn> \
  --payload '{"queryStringParameters": {"limit": "10"}}' \
  response.json
```

---

## 🔒 Security

- **IAM Roles**: Least privilege per ogni Lambda/Agent
- **VPC**: Opzionale per MCP server
- **Secrets Manager**: Credenziali Telegram e Azure
- **API Keys**: MCP server authenticato
- **Encryption**: DynamoDB encryption at rest

---

## 💡 Roadmap

- [ ] Multi-utente con autenticazione
- [ ] Dashboard web con React
- [ ] Integrazione Google Calendar via MCP
- [ ] Agente per meeting notes
- [ ] Voice interface con Whisper
- [ ] Analytics e insights
- [ ] Mobile app (React Native)

---

## 🤝 Contributing

Pull requests benvenute! Per modifiche importanti, apri prima una issue.

---

## 📄 License

MIT License - Vedi [LICENSE](LICENSE) per dettagli

---

## 👤 Author

Riccardo Laface - AWS Bedrock AgentCore Specialist

---

## 🙏 Acknowledgments

- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents](https://strandsagents.com)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Anthropic Claude](https://www.anthropic.com/claude)

---

**🎉 Buon organizing con i tuoi AI agents! 🚀**
