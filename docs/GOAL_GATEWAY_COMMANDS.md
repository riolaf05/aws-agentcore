# Comandi Gateway per Obiettivi (Goals)

## 1. Deploy Infrastruttura

Prima deploya la nuova infrastruttura:

```powershell
cd infrastructure\cdk-app
cdk deploy
```

Salva gli ARN delle Lambda dal output:
- `GoalPostLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalPost
- `GoalGetLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalGet

## 2. Crea Gateway Target per POST Goals (save-goal)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name save-goal `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalPost",
      "toolSchema": {
        "inlinePayload": [{
          "name": "save-goal",
          "description": "Crea un nuovo obiettivo strategico con metriche di progresso e sottotask. Ogni obiettivo appartiene a un ambito (es. Reply, MatchGuru) e ha scadenza, priorità e metriche di completamento.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "ambito": {
                "type": "string",
                "description": "Ambito/progetto di appartenenza (es. Reply, MatchGuru, Personale)"
              },
              "titolo": {
                "type": "string",
                "description": "Titolo breve e chiaro dell obiettivo"
              },
              "descrizione": {
                "type": "string",
                "description": "Descrizione dettagliata dell obiettivo e del valore atteso"
              },
              "scadenza": {
                "type": "string",
                "description": "Data di scadenza in formato YYYY-MM-DD"
              },
              "metriche": {
                "type": "object",
                "description": "Metriche di progresso (es. {completamento_percentuale: 0, target: 100, attuale: 0})"
              },
              "priorita": {
                "type": "string",
                "description": "Livello di priorità: low, medium, high, urgent"
              },
              "sottotask": {
                "type": "array",
                "description": "Lista di sotto-attività necessarie per raggiungere l obiettivo",
                "items": {
                  "type": "object",
                  "properties": {
                    "titolo": {"type": "string"},
                    "scadenza": {"type": "string"},
                    "completato": {"type": "boolean"}
                  }
                }
              }
            },
            "required": ["ambito", "titolo", "scadenza"]
          }
        }]
      }
    }'
```

## 3. Crea Gateway Target per GET Goals (get-goals)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-goals `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalGet",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get-goals",
          "description": "Recupera gli obiettivi strategici con filtri per ambito, status e priorità. Restituisce metriche di progresso e sottotask.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "ambito": {
                "type": "string",
                "description": "Filtra per ambito (es. Reply, MatchGuru)"
              },
              "status": {
                "type": "string",
                "description": "Filtra per stato: active, completed, cancelled"
              },
              "priorita": {
                "type": "string",
                "description": "Filtra per priorità: low, medium, high, urgent"
              },
              "goal_id": {
                "type": "string",
                "description": "ID specifico dell obiettivo da recuperare"
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
- `save-goal___save-goal`
- `get-goals___get-goals`

## 5. Test Lambda Locale (Opzionale)

### Test POST Goal

```powershell
cd ..\..\lambdas\goal-api

# Crea file test
@'
{
  "ambito": "Reply",
  "titolo": "Aumentare fatturato Q1 2025",
  "descrizione": "Incrementare il fatturato del 20% nel primo trimestre",
  "scadenza": "2025-03-31",
  "metriche": {
    "completamento_percentuale": 0,
    "target_fatturato": 100000,
    "fatturato_attuale": 0
  },
  "priorita": "high",
  "sottotask": [
    {
      "titolo": "Pianificare campagna marketing",
      "scadenza": "2025-01-31",
      "completato": false
    },
    {
      "titolo": "Contattare 50 nuovi lead",
      "scadenza": "2025-02-15",
      "completato": false
    }
  ]
}
'@ | Out-File -Encoding UTF8 test_post.json

# Testa localmente (richiede AWS credentials)
python -c "import post_goal, json; print(json.dumps(post_goal.lambda_handler(json.load(open('test_post.json')), None), indent=2))"
```

### Test GET Goals

```powershell
# Testa recupero per ambito
python -c "import get_goal, json; print(json.dumps(get_goal.lambda_handler({'ambito': 'Reply'}, None), indent=2))"
```

## 6. Esempio Utilizzo con Orchestrator

Una volta configurati i target, l'orchestrator può usarli:

```
Crea un obiettivo per Reply: aumentare fatturato del 20% entro marzo
```

L'orchestrator delegherà al tool `save-goal`.

```
Mostrami tutti gli obiettivi attivi per Reply
```

L'orchestrator delegherà al tool `get-goals` con filtro `ambito=Reply` e `status=active`.
