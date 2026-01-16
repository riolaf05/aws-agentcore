# AgentCore Gateway Setup Guide

## Panoramica

Questa guida spiega come configurare **AgentCore Gateway** per fornire accesso sicuro e autenticato alle Lambda Function del Task API. Il Gateway usa OAuth2 (Cognito) e MCP (Model Context Protocol) per esporre le Lambda come tools agentici.

## Perché Usare AgentCore Gateway?

✅ **Sicurezza**: Autenticazione OAuth2 automatica con Cognito  
✅ **Centralizzazione**: Un endpoint MCP per tutti i tools  
✅ **Semantic Search**: Ricerca semantica automatica sui tools  
✅ **Gestione IAM**: Ruoli e permessi automatici  
✅ **Monitoring**: Integrazione con AgentCore Observability  

## Sommario

1. [Prerequisiti](#prerequisiti)
2. [Step 1: Creare il Gateway MCP](#step-1-creare-il-gateway-mcp)
3. [Step 2: Creare IAM Role per il Gateway](#step-2-creare-iam-role-per-il-gateway)
4. [Step 3: Aggiungere Lambda Target - POST Task](#step-3-aggiungere-lambda-target---post-task)
5. [Step 4: Aggiungere Lambda Target - GET Tasks](#step-4-aggiungere-lambda-target---get-tasks)
6. [Step 4bis: Aggiungere Lambda Target - Candidate Matching](#step-4bis-aggiungere-lambda-target---candidate-matching-windows-powershell)
7. [Step 5: Aggiungere Lambda Target - List All Needs](#step-5-aggiungere-lambda-target---list-all-needs)
8. [Step 6: Aggiungere Lambda Target - Get Need by ID](#step-6-aggiungere-lambda-target---get-need-by-id)
9. [Step 7: Aggiungere Lambda Target - Search Needs by Keyword](#step-7-aggiungere-lambda-target---search-needs-by-keyword)
10. [Step 8: Verificare i Target del Gateway](#step-8-verificare-i-target-del-gateway)
11. [Configurare le Variabili d'Ambiente](#step-9-configurare-le-variabili-dambiente)
12. [Test del Gateway](#step-10-test-del-gateway)
13. [Troubleshooting](#troubleshooting)
14. [Best Practices](#best-practices)

## Architettura Gateway

```
┌─────────────────┐
│  Task Manager   │──┐
│     Agent       │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌──────────────────┐     ┌──────────────────┐
│ Daily Briefing  │──┼───▶│  AgentCore       │────▶│  Lambda Task API │
│     Agent       │  │    │    Gateway       │     │  (POST/GET)      │
└─────────────────┘  │    │                  │     └──────────────────┘
                     │    │  + OAuth2 Token  │              │
┌─────────────────┐  │    │  + IAM Roles     │              │
│  Orchestrator   │──┘    │  + MCP Protocol  │              ▼
│     Agent       │       └──────────────────┘     ┌──────────────────┐
└─────────────────┘                                │  DynamoDB Tasks  │
                                                   └──────────────────┘
```

## Prerequisiti

1. **AWS CLI** configurato con credenziali
2. **bedrock-agentcore-starter-toolkit** installato:
   ```bash
   pip install bedrock-agentcore-starter-toolkit
   ```
3. **Lambda Task API** deployate (POST e GET)
4. **Agenti** sviluppati e funzionanti

## Step 1: Creare il Gateway MCP

Crea il Gateway con il CLI di AgentCore:

```bash
agentcore gateway create-mcp-gateway \
    --name TaskAPIGateway \
    --region us-east-1
```

**Output:**
```json
{
  "gatewayArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:mcp-gateway/gateway-abc123",
  "gatewayId": "gateway-abc123",
  "gatewayUrl": "https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123",
  "status": "CREATING",
  "cognitoDetails": {
    "userPoolId": "us-east-1_XYZ123",
    "clientId": "abcd1234efgh5678",
    "clientSecret": "secret-key-here",
    "tokenEndpoint": "https://task-api-gateway.auth.us-east-1.amazoncognito.com/oauth2/token",
    "scope": "invoke"
  }
}
```

📝 **Salva questi valori**:
- `gatewayUrl` → variabile d'ambiente `GATEWAY_MCP_URL`
- `cognitoDetails.clientId` → variabile d'ambiente `GATEWAY_CLIENT_ID`
- `cognitoDetails.clientSecret` → variabile d'ambiente `GATEWAY_CLIENT_SECRET`
- `cognitoDetails.tokenEndpoint` → variabile d'ambiente `GATEWAY_TOKEN_ENDPOINT`
- `cognitoDetails.scope` → variabile d'ambiente `GATEWAY_SCOPE`

## Step 2: Creare IAM Role per il Gateway

Il Gateway necessita di permessi per invocare le Lambda:

```bash
# Crea il ruolo (o usa un ruolo esistente)
aws iam create-role \
    --role-name TaskAPIGatewayExecutionRole \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'

# Attach policy per Lambda invoke
aws iam put-role-policy \
    --role-name TaskAPIGatewayExecutionRole \
    --policy-name LambdaInvokePolicy \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": "lambda:InvokeFunction",
        "Resource": [
          "arn:aws:lambda:us-east-1:123456789012:function:TaskPostFunction",
          "arn:aws:lambda:us-east-1:123456789012:function:TaskGetFunction"
        ]
      }]
    }'
```

## Step 3: Aggiungere Lambda Target - POST Task

Configura il target per salvare task (POST):

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:mcp-gateway/gateway-abc123 \
    --gateway-url https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123 \
    --role-arn arn:aws:iam::123456789012:role/TaskAPIGatewayExecutionRole \
    --name save_task \
    --target-type lambda \
    --target-payload '{
      "arn": "arn:aws:lambda:us-east-1:123456789012:function:TaskPostFunction",
      "tools": [{
        "name": "save_task",
        "description": "Save tasks to DynamoDB database. Accepts a list of tasks with title, description, due_date, priority, category, and tags.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "tasks": {
              "type": "array",
              "description": "Array of tasks to save",
              "items": {
                "type": "object",
                "properties": {
                  "title": {"type": "string", "description": "Task title"},
                  "description": {"type": "string", "description": "Detailed description"},
                  "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                  "priority": {"type": "string", "description": "Priority: low, medium, high, urgent"},
                  "category": {"type": "string", "description": "Category: work, learning, health, personal, general"},
                  "tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"}
                },
                "required": ["title"]
              }
            }
          },
          "required": ["tasks"]
        }
      }]
    }'
```

## Step 4: Aggiungere Lambda Target - GET Tasks

Configura il target per recuperare task (GET):

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:mcp-gateway/gateway-abc123 \
    --gateway-url https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123 \
    --role-arn arn:aws:iam::123456789012:role/TaskAPIGatewayExecutionRole \
    --name get_tasks \
    --target-type lambda \
    --target-payload '{
      "arn": "arn:aws:lambda:us-east-1:123456789012:function:TaskGetFunction",
      "tools": [{
        "name": "get_tasks",
        "description": "Retrieve tasks from DynamoDB database with filters for due date and status.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "due_date": {
              "type": "string",
              "description": "Date filter: today, tomorrow, week, month"
            },
            "status": {
              "type": "string",
              "description": "Status filter (comma-separated): pending, in_progress, completed"
            },
            "limit": {
              "type": "string",
              "description": "Maximum number of tasks to return"
            }
          }
        }
      }]
    }'
```

## Step 5: Verificare il Gateway

Controlla che il Gateway sia attivo:

```bash
agentcore gateway list-mcp-gateways --region us-east-1
```

Descrizione del Gateway:

```bash
agentcore gateway get-mcp-gateway \
    --gateway-id gateway-abc123 \
    --region us-east-1
```

## Step 6: Configurare le Variabili d'Ambiente

Aggiungi al file `.env` o al Dockerfile degli agenti:

```bash
# AgentCore Gateway Configuration
GATEWAY_MCP_URL=https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123
GATEWAY_CLIENT_ID=abcd1234efgh5678
GATEWAY_CLIENT_SECRET=secret-key-here
GATEWAY_TOKEN_ENDPOINT=https://task-api-gateway.auth.us-east-1.amazoncognito.com/oauth2/token
GATEWAY_SCOPE=invoke
```

## Step 7: Test del Gateway

Test con `curl`:

```bash
# 1. Ottieni OAuth2 token
TOKEN=$(curl -X POST https://task-api-gateway.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=abcd1234efgh5678&client_secret=secret-key-here&scope=invoke" \
  | jq -r '.access_token')

# 2. Chiama tool save_task
curl -X POST https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "save_task",
      "arguments": {
        "tasks": [{
          "title": "Test Gateway",
          "description": "Testing AgentCore Gateway integration",
          "due_date": "2025-06-01",
          "priority": "medium",
          "category": "work"
        }]
      }
    }
  }'

# 3. Chiama tool get_tasks
curl -X POST https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_tasks",
      "arguments": {
        "due_date": "today",
        "status": "pending"
      }
    }
  }'
```

## Step 8: Deploy degli Agenti

Ricompila e rideploya gli agenti con le nuove variabili d'ambiente:

```bash
# Task Manager
cd agents/task-manager
agentcore configure --agent-name task-manager --region us-east-1
agentcore launch --agent-name task-manager --region us-east-1 \
  --env GATEWAY_MCP_URL=<gateway-url> \
  --env GATEWAY_CLIENT_ID=<client-id> \
  --env GATEWAY_CLIENT_SECRET=<client-secret> \
  --env GATEWAY_TOKEN_ENDPOINT=<token-endpoint> \
  --env GATEWAY_SCOPE=invoke

# Daily Briefing
cd ../daily-briefing
agentcore configure --agent-name daily-briefing --region us-east-1
agentcore launch --agent-name daily-briefing --region us-east-1 \
  --env GATEWAY_MCP_URL=<gateway-url> \
  --env GATEWAY_CLIENT_ID=<client-id> \
  --env GATEWAY_CLIENT_SECRET=<client-secret> \
  --env GATEWAY_TOKEN_ENDPOINT=<token-endpoint> \
  --env GATEWAY_SCOPE=invoke \
  --env MCP_SERVER_URL=<outlook-mcp-url> \
  --env MCP_API_KEY=<outlook-api-key>
```

## Gestione del Gateway

### Listare tutti i Gateway

```bash
agentcore gateway list-mcp-gateways --region us-east-1
```

### Listare i Target di un Gateway

```bash
agentcore gateway list-mcp-gateway-targets \
    --gateway-id gateway-abc123 \
    --region us-east-1
```

### Eliminare un Target

```bash
agentcore gateway delete-mcp-gateway-target \
    --gateway-id gateway-abc123 \
    --target-id target-xyz789 \
    --region us-east-1
```

### Eliminare il Gateway

```bash
agentcore gateway delete-mcp-gateway \
    --gateway-id gateway-abc123 \
    --region us-east-1
```

## Step 4bis: Aggiungere Lambda Target - Candidate Matching (Windows PowerShell)

Configura il target per il matching candidati-needs usando la Lambda `mg-matchguru-candidate-match-dev`:

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name candidate-matching `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-candidate-match-dev",
      "toolSchema": {
        "inlinePayload": [{
          "name": "find_matching_needs",
          "description": "Trova i migliori needs per un candidato usando embeddings vettoriali e similarità coseno. Analizza skills, esperienza, lingue e preferenze. Restituisce top 5 needs ordinati per compatibilità con similarity score percentuale.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "candidate": {
                "type": "object",
                "description": "Oggetto candidato con skills, esperienze, lingue e preferenze",
                "properties": {
                  "id": {"type": "string", "description": "ID univoco del candidato"},
                  "name": {"type": "string", "description": "Nome del candidato"},
                  "surname": {"type": "string", "description": "Cognome del candidato"},
                  "current_role": {"type": "string", "description": "Ruolo attuale del candidato"},
                  "years_experience": {"type": "number", "description": "Anni totali di esperienza"},
                  "province": {"type": "string", "description": "Provincia di residenza (es: MI, RM)"},
                  "technologies": {"type": "array", "description": "Tecnologie conosciute", "items": {"type": "object", "properties": {"skill_name": {"type": "string"}}}},
                  "hard_skills": {"type": "array", "description": "Competenze tecniche specifiche", "items": {"type": "object", "properties": {"skill_name": {"type": "string"}}}},
                  "soft_skills": {"type": "array", "description": "Competenze trasversali", "items": {"type": "object", "properties": {"skill_name": {"type": "string"}}}},
                  "languages": {"type": "array", "description": "Lingue conosciute con livello di proficiency", "items": {"type": "object", "properties": {"language": {"type": "string"}, "proficiency": {"type": "string"}}}}
                },
                "required": ["current_role"]
              }
            },
            "required": ["candidate"]
          }
        }]
      }
    }'
```

**Note sulla configurazione:**
- **Gateway ARN**: Usa `/gateway/` (non `/mcp-gateway/`)
- **Gateway URL**: Formato `<gateway-id>.gateway.bedrock-agentcore.<region>.amazonaws.com/mcp`
- **Role ARN**: Usa il ruolo di esecuzione del gateway (`agentcore-taskapigateway-role`)
- **Region**: Specifica sempre `--region us-east-1`
- **Target Payload**: Usa `lambdaArn` e `toolSchema.inlinePayload` (array di tool)

**Output atteso:**
```
✅Target is ready
Target ID: YAFODWZS0O
Name: candidate-matching
Status: READY
```

## Step 5: Aggiungere Lambda Target - List All Needs

Configura il target per elencare tutti i needs disponibili:

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name list-all-needs `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev",
      "toolSchema": {
        "inlinePayload": [{
          "name": "list_all_needs",
          "description": "List all available needs from MongoDB database. Returns up to 1000 needs with complete details including title, description, required role, company, and location.",
          "inputSchema": {
            "type": "object",
            "properties": {}
          }
        }]
      }
    }'
```

## Step 6: Aggiungere Lambda Target - Get Need by ID

Configura il target per recuperare un need specifico per ID:

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-need-by-id `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get_need_by_id",
          "description": "Retrieve a specific need by its unique ID. Returns detailed information including title, description, role requirements, company, salary range, and location.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "id": {
                "type": "string",
                "description": "The unique identifier of the need to retrieve (MongoDB ObjectId or custom ID)"
              }
            },
            "required": ["id"]
          }
        }]
      }
    }'
```

## Step 7: Aggiungere Lambda Target - Search Needs by Keyword

Configura il target per cercare needs per parola chiave:

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name search-needs-by-keyword `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev",
      "toolSchema": {
        "inlinePayload": [{
          "name": "search_needs_by_keyword",
          "description": "Search for needs by keyword. Searches across multiple fields including title, description, role name, company, and city. Returns up to 100 matching needs with full details.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string",
                "description": "Search keyword or phrase (e.g., 'Python developer', 'Senior manager', 'Milano'). Case-insensitive search across title, description, role, company, and location."
              }
            },
            "required": ["query"]
          }
        }]
      }
    }'
```

## Step 8: Verificare i Target del Gateway

Elenca tutti i target configurati:

```powershell
agentcore gateway list-mcp-gateway-targets `
    --gateway-id taskapigateway-vveeifneus `
    --region us-east-1
```

Dovresti vedere:
- `save_task` (Step 3)
- `get_tasks` (Step 4)
- `candidate-matching` (Step 4bis)
- `list-all-needs` (Step 5)
- `get-need-by-id` (Step 6)
- `search-needs-by-keyword` (Step 7)

### Eliminare il Gateway (originale)

```bash
agentcore gateway delete-mcp-gateway \
    --gateway-id gateway-abc123 \
    --region us-east-1
```

## Troubleshooting

### Errore: "Unauthorized" durante tool call

**Causa**: Token OAuth2 scaduto o credenziali errate  
**Soluzione**:
1. Verifica `GATEWAY_CLIENT_ID` e `GATEWAY_CLIENT_SECRET`
2. Controlla che il token endpoint sia corretto
3. Richiedi un nuovo token

### Errore: "AccessDenied" su Lambda invoke

**Causa**: IAM role del Gateway non ha permessi  
**Soluzione**:
1. Verifica il ruolo IAM: `aws iam get-role-policy --role-name TaskAPIGatewayExecutionRole --policy-name LambdaInvokePolicy`
2. Aggiungi ARN Lambda mancanti alla policy

### Gateway non trova i tools

**Causa**: Target non configurato correttamente  
**Soluzione**:
1. Lista i target: `agentcore gateway list-mcp-gateway-targets`
2. Verifica che il `target-payload` contenga il tool schema
3. Ricrea il target con lo schema corretto

### Performance lenta

**Causa**: Cold start Lambda o token caching mancante  
**Soluzione**:
1. Il `GatewayClient` in Python ha token caching automatico
2. Considera Lambda Provisioned Concurrency per hot start
3. Monitora con AgentCore Observability

## Best Practices

1. **Secret Management**: Usa AWS Secrets Manager per `GATEWAY_CLIENT_SECRET`
2. **Token Caching**: Il client Python cache i token per 55 minuti
3. **Error Handling**: Implementa retry con exponential backoff
4. **Monitoring**: Attiva CloudWatch Logs per il Gateway
5. **Testing**: Testa ogni target separatamente prima di integrare
6. **Semantic Search**: Abilita per tutti i Gateway con `--enable-semantic-search`

## Risorse

- [AgentCore Gateway Documentation](https://aws.github.io/bedrock-agentcore-starter-toolkit/api-reference/gateway/)
- [Gateway Integration Examples](https://aws.github.io/bedrock-agentcore-starter-toolkit/examples/gateway-integration.md)
- [OAuth2 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)

## Prossimi Passi

✅ Gateway configurato per Task API  
⏭️ Deploy MCP server per Outlook integration  
⏭️ Configurare EventBridge per Daily Briefing scheduler  
⏭️ Setup Telegram webhook per interfaccia utente  
