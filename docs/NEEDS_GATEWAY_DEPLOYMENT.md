# Needs API Gateway Deployment Guide

Guida completa per il deploy della Needs API Lambda nel AgentCore Gateway e integrazione con l'agente `needs-reader`.

## Panoramica Architettura

```
┌──────────────────┐
│  Needs Reader    │
│     Agent        │
└────────┬─────────┘
         │ (OAuth2)
         ▼
┌──────────────────────────────┐
│  AgentCore Gateway MCP       │
│  - Authentication (Cognito)  │
│  - Tool Management           │
│  - Request Routing           │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────┐
│  Needs API Lambda    │
│  - GET /needs        │
│  - GET /needs/{id}   │
│  - GET /search/{q}   │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│   MongoDB           │
│   (matchguru db)     │
│   (needs collection) │
└──────────────────────┘
```

## Step 1: Lambda Esistente

⚠️ **IMPORTANTE**: La Lambda esiste già con il seguente nome:

- **Function Name**: `mg-matchguru-needs-search-dev`
- **ARN**: `arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev`
- **Runtime**: Python 3.11

Non è necessario creare una nuova Lambda. Utilizza quella esistente per il gateway.



## Step 2: Verificare il Gateway MCP

### 2.1 Prerequisiti

```bash
# Installa il toolkit se non lo hai ancora
pip install bedrock-agentcore-starter-toolkit
```

### 2.2 Verificare/Creare il Gateway

Se il gateway esiste già, verifica il suo stato:

```bash
agentcore gateway list-mcp-gateways --region us-east-1
```

Se non esiste, crealo:

```bash
agentcore gateway create-mcp-gateway \
    --name matchguru-gateway \
    --region us-east-1
```

**Output atteso:**
```json
{
  "gatewayArn": "arn:aws:bedrock-agentcore:us-east-1:879338784410:mcp-gateway/gateway-abc123",
  "gatewayId": "gateway-abc123",
  "gatewayUrl": "https://bedrock-agentcore.us-east-1.amazonaws.com/gateways/gateway-abc123",
  "status": "ACTIVE",
  "cognitoDetails": {
    "userPoolId": "us-east-1_XYZ123",
    "clientId": "abcd1234efgh5678",
    "clientSecret": "secret-key-here",
    "tokenEndpoint": "https://matchguru-gateway.auth.us-east-1.amazoncognito.com/oauth2/token",
    "scope": "invoke"
  }
}
```

📝 **Salva questi valori:**
- `gatewayUrl` → `GATEWAY_MCP_URL`
- `cognitoDetails.clientId` → `GATEWAY_CLIENT_ID`
- `cognitoDetails.clientSecret` → `GATEWAY_CLIENT_SECRET`
- `cognitoDetails.tokenEndpoint` → `GATEWAY_TOKEN_ENDPOINT`

### 2.3 Gateway IAM Role

Verificare che il ruolo IAM del gateway abbia i permessi per invocare la Lambda:

```bash
# Ruolo del gateway (fornito da AgentCore)
GATEWAY_ROLE_ARN="arn:aws:bedrock-agentcore:us-east-1:879338784410:mcp-gateway/gateway-abc123"

# Assicurati che abbia il permesso per invocare la Lambda
aws iam put-role-policy \
    --role-name <gateway-role-name> \
    --policy-name NeedsLambdaInvokePolicy \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": "lambda:InvokeFunction",
        "Resource": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev"
      }]
    }' \
    --region us-east-1
```

## Step 3: Configurare i Target Lambda nel Gateway

**Lambda da usare:**
- **Name**: `mg-matchguru-needs-search-dev`
- **ARN**: `arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev`

### 3.1 Target - List All Needs

```bash
GATEWAY_ARN="arn:aws:bedrock-agentcore:us-east-1:879338784410:mcp-gateway/gateway-xxx"
GATEWAY_URL="https://matchguru-gateway-xxx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
GATEWAY_ROLE_ARN="arn:aws:iam::879338784410:role/gateway-execution-role"

agentcore gateway create-mcp-gateway-target \
    --gateway-arn "$GATEWAY_ARN" \
    --gateway-url "$GATEWAY_URL" \
    --role-arn "$GATEWAY_ROLE_ARN" \
    --name list_all_needs \
    --target-type lambda \
    --target-payload '{
      "arn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev",
      "tools": [{
        "name": "list_all_needs",
        "description": "List all available needs from MongoDB database. Returns up to 1000 needs with complete details including title, description, required role, company, and location.",
        "inputSchema": {
          "type": "object",
          "properties": {}
        }
      }]
    }' \
    --region us-east-1
```

### 3.2 Target - Get Need by ID

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn "$GATEWAY_ARN" \
    --gateway-url "$GATEWAY_URL" \
    --role-arn "$GATEWAY_ROLE_ARN" \
    --name get_need_by_id \
    --target-type lambda \
    --target-payload '{
      "arn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev",
      "tools": [{
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
    }' \
    --region us-east-1
```

### 3.3 Target - Search Needs by Keyword

```bash
agentcore gateway create-mcp-gateway-target \
    --gateway-arn "$GATEWAY_ARN" \
    --gateway-url "$GATEWAY_URL" \
    --role-arn "$GATEWAY_ROLE_ARN" \
    --name search_needs_by_keyword \
    --target-type lambda \
    --target-payload '{
      "arn": "arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev",
      "tools": [{
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
    }' \
    --region us-east-1
```

## Step 4: Configurare l'Agente needs-reader

### 4.1 Aggiornare le Credenziali

Nel file `agents/needs-reader/agent.py`, aggiorna le credenziali Cognito:

```bash
# Opzione 1: Variabili d'ambiente
export GATEWAY_CLIENT_ID="abcd1234efgh5678"
export GATEWAY_CLIENT_SECRET="secret-key-here"
export GATEWAY_TOKEN_ENDPOINT="https://needs-api-gateway.auth.us-east-1.amazoncognito.com/oauth2/token"
export GATEWAY_MCP_URL="https://your-gateway-url.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

# Opzione 2: Modificare il file agent.py direttamente
```

### 4.2 Testare l'Agente Localmente

```bash
cd agents/needs-reader
pip install -r requirements.txt

python agent.py <<EOF
{
    "prompt": "Mostrami tutti i need disponibili"
}
EOF
```

### 4.3 Deployare l'Agente su AgentCore Runtime

```bash
agentcore agent deploy \
    --name needs-reader \
    --region us-east-1 \
    --entrypoint invoke \
    --path agents/needs-reader/
```

## Step 5: Verificare il Deployment
WS Lambda invoke
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/needs", "requestContext": {"http": {"method": "GET"}}}' \
    response.json

# Visualizzare la risposta
cat response.json | jq .

# Cercare un need per ID
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/needs/12345", "requestContext": {"http": {"method": "GET"}}}' \
    response.json

# Cercare per parola chiave
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/search/Python%20Developer", "requestContext": {"http": {"method": "GET"}}}' \
    response.json
curl -X GET "https://your-api-id.execute-api.us-east-1.879338784410:mcp-gateway/gateway-xxxloper"

# Cercare per ID
curl -X GET "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/needs/12345"
```

### 5.2 Testare il Gateway MCP

```bash
# Elencare i tools disponibili nel gateway
agentcore gateway list-mcp-gateway-targets \
    --gateway-arn "arn:aws:bedrock-agentcore:us-east-1:123456789012:mcp-gateway/gateway-abc123"
```

### 5.3 Testare l'Agente

```bash
agentcore agent invoke \
    --name needs-reader \
    --payload '{"prompt": "Quali ruoli senior developer sono disponibili?"}'
```

## Step 6: Configurare le Variabili d'Ambiente

Crea un file `.env` nella cartella progetto:

```bash
# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# MongoDB
MONGODB_HOST=your-mongodb-host
MONGODB_PORT=27017
MONGODB_DB=matchguru
MONGODB_COLLECTION=needs
MONGODB_USER=needs_user
MONGODB_PASSWORD_PARAM=/matchguru/mongodb/password
USE_PARAMETER_STORE=false

# Gateway
GATEWAY_CLIENT_ID=abcd1234efgh5678
GATEWAY_CLIENT_SECRET=secret-key-here
GATEWAY_TOKEN_ENDPOINT=https://needs-api-gateway.auth.us-east-1.amazoncognito.com/oauth2/token
GATEWAY_MCP_URL=https://your-gateway.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp

# Agent
AGENT_NAME=needs-reader
BEDROCK_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
```

## Troubleshooting

### Errore: "Impossibile connettersi a MongoDB"

1. Verifica che MongoDB sia raggiungibile dalla Lambda
2. Controlla le variabili d'ambiente (`MONGODB_HOST`, `MONGODB_PORT`)
3. Verifica le credenziali MongoDB nel Secrets Manager
4. Assicurati che il Security Group permetta la connessione

### Errore: "Unauthorized" nel Gateway

1. Verifica `GATEWAY_CLIENT_ID` e `GATEWAY_CLIENT_SECRET`
2. Controlla il `GATEWAY_TOKEN_ENDPOINT`
3. Assicurati che il token non sia scaduto (viene rigenerato automaticamente)

### Errore: "Endpoint non trovato"

1. Verifica che il path della richiesta sia corretto
2. Controlla che i target lambda siano configurati nel gateway
3. Verifica i log della Lambda in CloudWatch

### Errore: "Errore lettura needs" nella risposta

1. Controlla che la collection MongoDB esista
2. Verifica i permessi di accesso a MongoDB
3. Guarda i log CloudWatch della Lambda per dettagli

## Monitoraggio

### Visualizzare i Log della Lambda

```bash
# Ultimi 100 righe
aws logs tail /aws/lambda/needs-api --follow

# Log specifico per un errore
aws logs filter-log-events \
    --log-group-name /aws/lambda/needs-api \
    --filter-pattern "ERROR"
```

### Metriche CloudWatch

```bash
# Invocazioni
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=needs-api \
    --statistics Sum \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-31T23:59:59Z \
    --period 86400
```

## Prossimi Passi

- ✅ Aggiungere cache per le ricerche frequenti
- ✅ Implementare paginazione per risultati grandi
- ✅ Aggiungere filtri avanzati (data, priorità, salario, etc.)
- ✅ Implementare logging strutturato
- ✅ Aggiungere metriche custom per monitoring
- ✅ Configurare auto-scaling per il Gateway

## Riferimenti Utili

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Bedrock Agents API](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [MongoDB Connection String URI](https://docs.mongodb.com/manual/reference/connection-string/)
