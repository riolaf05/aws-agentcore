# Comandi Gateway per Progetti (Projects)

## 1. Deploy Infrastruttura

Prima deploya la nuova infrastruttura:

```powershell
cd infrastructure\cdk-app
cdk deploy
```

Salva gli ARN delle Lambda dal output:
- `ProjectPostLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectPost
- `ProjectGetLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectGet

## 2. Crea Gateway Target per POST Projects (save-project)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name save-project `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectPost",
      "toolSchema": {
        "inlinePayload": [{
          "name": "save-project",
          "description": "Registra un nuovo progetto software/tecnico con metadata completi. Include ambito di appartenenza, URL GitHub, tecnologie utilizzate e descrizione dettagliata.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "ambito": {
                "type": "string",
                "description": "Ambito/cliente/organizzazione di appartenenza (es. Reply, MatchGuru, Personale)"
              },
              "titolo": {
                "type": "string",
                "description": "Nome del progetto"
              },
              "github_url": {
                "type": "string",
                "description": "URL del repository GitHub (opzionale)"
              },
              "descrizione": {
                "type": "string",
                "description": "Descrizione dettagliata del progetto, obiettivi e caratteristiche principali"
              },
              "tag": {
                "type": "array",
                "description": "Lista di tecnologie/framework utilizzati (es. Python, AWS, React, Docker)",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["ambito", "titolo"]
          }
        }]
      }
    }'
```

## 3. Crea Gateway Target per GET Projects (get-projects)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-projects `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectGet",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get-projects",
          "description": "Recupera i progetti registrati con filtri per ambito e tecnologie. Ordina per data di creazione (più recenti prima).",
          "inputSchema": {
            "type": "object",
            "properties": {
              "ambito": {
                "type": "string",
                "description": "Filtra per ambito/cliente (es. Reply, MatchGuru)"
              },
              "tag": {
                "type": "string",
                "description": "Filtra per tecnologia specifica (es. Python, AWS, React)"
              },
              "project_id": {
                "type": "string",
                "description": "ID specifico del progetto da recuperare"
              },
              "limit": {
                "type": "number",
                "description": "Numero massimo di risultati (default: 100)"
              }
            }
          }
        }]
      }
    }'
```

## 4. Verifica Gateway Targets

```powershell
cd ..\..\scripts
python test_mcp_gateway.py
```

Dovresti vedere:
- `save-project___save-project`
- `get-projects___get-projects`

## 5. Test Lambda Locale (Opzionale)

### Test POST Project

```powershell
cd ..\..\lambdas\project-api

# Crea file test
@'
{
  "ambito": "Reply",
  "titolo": "Sistema Analytics Real-time",
  "github_url": "https://github.com/reply/analytics-system",
  "descrizione": "Piattaforma di analytics real-time con dashboard interattive per monitoraggio KPI aziendali. Integra stream processing e machine learning.",
  "tag": ["Python", "AWS Lambda", "DynamoDB", "React", "Apache Kafka", "TensorFlow"]
}
'@ | Out-File -Encoding UTF8 test_post.json

# Testa localmente (richiede AWS credentials)
python -c "import post_project, json; print(json.dumps(post_project.lambda_handler(json.load(open('test_post.json')), None), indent=2))"
```

### Test GET Projects

```powershell
# Testa recupero per ambito
python -c "import get_project, json; print(json.dumps(get_project.lambda_handler({'ambito': 'Reply'}, None), indent=2))"

# Testa recupero per tecnologia
python -c "import get_project, json; print(json.dumps(get_project.lambda_handler({'tag': 'Python'}, None), indent=2))"
```

## 6. Esempio Utilizzo con Orchestrator

Una volta configurati i target, l'orchestrator può usarli:

```
Registra un nuovo progetto per Reply: Sistema di Analytics real-time con Python, AWS e React
```

L'orchestrator delegherà al tool `save-project`.

```
Mostrami tutti i progetti Reply che usano Python
```

L'orchestrator delegherà al tool `get-projects` con filtri `ambito=Reply` e `tag=Python`.

```
Quanti progetti abbiamo registrati per MatchGuru?
```

L'orchestrator userà `get-projects` con `ambito=MatchGuru` e conterà i risultati.

## 7. Struttura Dati Progetto

```json
{
  "project_id": "auto-generato-uuid",
  "ambito": "Reply",
  "titolo": "Sistema Analytics Real-time",
  "github_url": "https://github.com/reply/analytics-system",
  "descrizione": "Piattaforma di analytics...",
  "tag": ["Python", "AWS Lambda", "DynamoDB", "React"],
  "data_creazione": "2025-12-17T10:30:00.000Z",
  "updated_at": "2025-12-17T10:30:00.000Z"
}
```
