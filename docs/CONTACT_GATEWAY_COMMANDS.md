# Comandi Gateway per Contatti (Contacts)

## 1. Deploy Infrastruttura

Prima deploya la nuova infrastruttura:

```powershell
cd infrastructure\cdk-app
cdk deploy
```

Salva gli ARN delle Lambda dal output:
- `ContactPostLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactPost
- `ContactGetLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactGet
- `ContactUpdateLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactUpdate
- `ContactDeleteLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactDelete

## 2. Crea Gateway Target per POST Contacts (post-contact)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name post-contact `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactPost",
      "toolSchema": {
        "inlinePayload": [{
          "name": "post-contact",
          "description": "Crea un nuovo contatto con informazioni personali e professionali. Tutti i campi sono opzionali.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "nome": {"type": "string", "description": "Nome del contatto"},
              "cognome": {"type": "string", "description": "Cognome del contatto"},
              "email": {"type": "string", "description": "Indirizzo email"},
              "telefono": {"type": "string", "description": "Numero di telefono"},
              "descrizione": {"type": "string", "description": "Ruolo o descrizione (es. CEO di TechCompany)"},
              "dove_conosciuto": {"type": "string", "description": "Dove/quando hai conosciuto la persona"},
              "note": {"type": "string", "description": "Note aggiuntive"},
              "url": {"type": "string", "description": "URL LinkedIn o altro profilo social"},
              "tipo": {
                "description": "Tipo di contatto (investitore, startupper, fornitore, etc.)",
                "type": "string"
              }
            }
          }
        }]
      }
    }'
```

## 3. Crea Gateway Target per GET Contacts (get-contact)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-contact `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactGet",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get-contact",
          "description": "Recupera contatti con filtri per nome, cognome, email o luogo di conoscenza.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "nome": {"type": "string", "description": "Filtra per nome (ricerca parziale)"},
              "cognome": {"type": "string", "description": "Filtra per cognome"},
              "email": {"type": "string", "description": "Filtra per email"},
              "dove_conosciuto": {"type": "string", "description": "Filtra per luogo/evento di conoscenza"},
              "contact_id": {"type": "string", "description": "ID specifico del contatto da recuperare"},
              "limit": {"type": "number", "description": "Numero massimo di risultati (default: 100)"}
            }
          }
        }]
      }
    }'
```

## 4. Crea Gateway Target per UPDATE Contacts (update-contact)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name update-contact `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactUpdate",
      "toolSchema": {
        "inlinePayload": [{
          "name": "update-contact",
          "description": "Aggiorna un contatto esistente. Solo i campi forniti vengono modificati.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "contact_id": {"type": "string", "description": "ID del contatto da aggiornare (obbligatorio)"},
              "nome": {"type": "string", "description": "Nuovo nome"},
              "cognome": {"type": "string", "description": "Nuovo cognome"},
              "email": {"type": "string", "description": "Nuova email"},
              "telefono": {"type": "string", "description": "Nuovo telefono"},
              "descrizione": {"type": "string", "description": "Nuova descrizione"},
              "dove_conosciuto": {"type": "string", "description": "Aggiorna dove conosciuto"},
              "note": {"type": "string", "description": "Nuove note"},
              "url": {"type": "string", "description": "Nuovo URL"},
              "tipo": {
                "description": "Tipo di contatto (investitore, startupper, fornitore, etc.)",
                "type": "string"
              }
            },
            "required": ["contact_id"]
          }
        }]
      }
    }'
```

## 5. Crea Gateway Target per DELETE Contacts (delete-contact)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name delete-contact `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactDelete",
      "toolSchema": {
        "inlinePayload": [{
          "name": "delete-contact",
          "description": "Elimina un contatto esistente dal database.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "contact_id": {"type": "string", "description": "ID del contatto da eliminare"}
            },
            "required": ["contact_id"]
          }
        }]
      }
    }'
```

## 6. Verifica Gateway Targets

```powershell
cd ..\..\scripts
python test_mcp_gateway.py
```

Dovresti vedere i nuovi tool:
- `post-contact___post-contact`
- `get-contact___get-contact`
- `update-contact___update-contact`
- `delete-contact___delete-contact`

## 7. Esempio Utilizzo con Orchestrator

Una volta configurati i target, l'orchestrator può usarli:

```
Aggiungi un contatto: Mario Rossi, email mario.rossi@example.com, conosciuto al AWS Summit 2024
```

L'orchestrator delegherà al contact-writer-reader agent che userà il tool `post-contact`.

```
Mostrami tutti i contatti conosciuti al AWS Summit
```

L'orchestrator delegherà al tool `get-contact` con filtro `dove_conosciuto=AWS Summit`.
