# Comandi Gateway per Eventi e Luoghi

## 1. Deploy Infrastruttura

Prima deploya la nuova infrastruttura con CDK:

```powershell
cd infrastructure\cdk-app
cdk deploy
```

Salva gli ARN delle Lambda dall'output:

### Eventi
- `EventPostLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventPost
- `EventGetLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventGet
- `EventUpdateLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventUpdate
- `EventDeleteLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventDelete

### Luoghi
- `PlacePostLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlacePost
- `PlaceGetLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceGet
- `PlaceUpdateLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceUpdate
- `PlaceDeleteLambdaArn`: arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceDelete

---

## 2. Gateway Targets per EVENTI

### 2.1 POST Event (post-event)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name post-event `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventPost",
      "toolSchema": {
        "inlinePayload": [{
          "name": "post-event",
          "description": "Crea un nuovo evento. Il campo nome è obbligatorio. IMPORTANTE: Se l'\''utente non ha già fornito una descrizione dettagliata, DEVI PRIMA invocare l'\''agente researcher (ARN: arn:aws:bedrock-agentcore:us-east-1:879338784410:agent/researcher-agent) per recuperare informazioni dettagliate sull'\''evento online, e poi includere queste informazioni nella descrizione.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "nome": {"type": "string", "description": "Nome dell'\''evento (obbligatorio)"},
              "data": {"type": "string", "description": "Data dell'\''evento (formato YYYY-MM-DD)"},
              "luogo": {"type": "string", "description": "Dove si svolge l'\''evento"},
              "descrizione": {"type": "string", "description": "Descrizione dettagliata dell'\''evento. Usa le informazioni recuperate dall'\''agente researcher."}
            },
            "required": ["nome"]
          }
        }]
      }
    }'
```

### 2.2 GET Event (get-event)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-event `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventGet",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get-event",
          "description": "Recupera eventi esistenti. Puoi filtrare per nome, luogo, data o recuperare un evento specifico tramite event_id.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "event_id": {"type": "string", "description": "ID specifico dell'\''evento da recuperare"},
              "nome": {"type": "string", "description": "Filtra per nome evento (contiene)"},
              "luogo": {"type": "string", "description": "Filtra per luogo (contiene)"},
              "data_inizio": {"type": "string", "description": "Filtra eventi da questa data (formato YYYY-MM-DD)"},
              "data_fine": {"type": "string", "description": "Filtra eventi fino a questa data (formato YYYY-MM-DD)"},
              "limit": {"type": "number", "description": "Numero massimo di risultati (default: 100)"}
            }
          }
        }]
      }
    }'
```

### 2.3 UPDATE Event (update-event)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name update-event `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventUpdate",
      "toolSchema": {
        "inlinePayload": [{
          "name": "update-event",
          "description": "Aggiorna un evento esistente. Richiede event_id e almeno un campo da aggiornare.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "event_id": {"type": "string", "description": "ID dell'\''evento da aggiornare (obbligatorio)"},
              "nome": {"type": "string", "description": "Nuovo nome dell'\''evento"},
              "data": {"type": "string", "description": "Nuova data (formato YYYY-MM-DD)"},
              "luogo": {"type": "string", "description": "Nuovo luogo"},
              "descrizione": {"type": "string", "description": "Nuova descrizione"}
            },
            "required": ["event_id"]
          }
        }]
      }
    }'
```

### 2.4 DELETE Event (delete-event)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name delete-event `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventDelete",
      "toolSchema": {
        "inlinePayload": [{
          "name": "delete-event",
          "description": "Elimina un evento esistente tramite il suo event_id.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "event_id": {"type": "string", "description": "ID dell'\''evento da eliminare"}
            },
            "required": ["event_id"]
          }
        }]
      }
    }'
```

---

## 3. Gateway Targets per LUOGHI

### 3.1 POST Place (post-place)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name post-place `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlacePost",
      "toolSchema": {
        "inlinePayload": [{
          "name": "post-place",
          "description": "Crea un nuovo luogo. Il campo nome è obbligatorio. Categorie disponibili: ristorante, sport, agriturismo, museo, teatro, cinema, bar, hotel, parco, altro.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "nome": {"type": "string", "description": "Nome del luogo (obbligatorio)"},
              "descrizione": {"type": "string", "description": "Descrizione del luogo"},
              "categoria": {"type": "string", "description": "Categoria del luogo: ristorante, sport, agriturismo, museo, teatro, cinema, bar, hotel, parco, altro"},
              "indirizzo": {"type": "string", "description": "Indirizzo completo del luogo"}
            },
            "required": ["nome"]
          }
        }]
      }
    }'
```

### 3.2 GET Place (get-place)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-place `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceGet",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get-place",
          "description": "Recupera luoghi esistenti. Puoi filtrare per nome, categoria, indirizzo o recuperare un luogo specifico tramite place_id.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "place_id": {"type": "string", "description": "ID specifico del luogo da recuperare"},
              "nome": {"type": "string", "description": "Filtra per nome luogo (contiene)"},
              "categoria": {"type": "string", "description": "Filtra per categoria (ristorante, sport, agriturismo, museo, teatro, cinema, bar, hotel, parco, altro)"},
              "indirizzo": {"type": "string", "description": "Filtra per indirizzo/posizione (contiene)"},
              "limit": {"type": "number", "description": "Numero massimo di risultati (default: 100)"}
            }
          }
        }]
      }
    }'
```

### 3.3 UPDATE Place (update-place)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name update-place `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceUpdate",
      "toolSchema": {
        "inlinePayload": [{
          "name": "update-place",
          "description": "Aggiorna un luogo esistente. Richiede place_id e almeno un campo da aggiornare.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "place_id": {"type": "string", "description": "ID del luogo da aggiornare (obbligatorio)"},
              "nome": {"type": "string", "description": "Nuovo nome del luogo"},
              "descrizione": {"type": "string", "description": "Nuova descrizione"},
              "categoria": {"type": "string", "description": "Nuova categoria"},
              "indirizzo": {"type": "string", "description": "Nuovo indirizzo"}
            },
            "required": ["place_id"]
          }
        }]
      }
    }'
```

### 3.4 DELETE Place (delete-place)

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name delete-place `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceDelete",
      "toolSchema": {
        "inlinePayload": [{
          "name": "delete-place",
          "description": "Elimina un luogo esistente tramite il suo place_id.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "place_id": {"type": "string", "description": "ID del luogo da eliminare"}
            },
            "required": ["place_id"]
          }
        }]
      }
    }'
```

---

## 4. Verifica Configurazione

Dopo aver eseguito tutti i comandi, verifica che i target siano stati creati:

```powershell
agentcore gateway list-mcp-gateway-targets `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --region us-east-1
```

Dovresti vedere 8 nuovi target:
- `post-event`
- `get-event`
- `update-event`
- `delete-event`
- `post-place`
- `get-place`
- `update-place`
- `delete-place`

---

## 5. Test con l'Agente

L'agente `event-place-writer` può ora utilizzare questi tool. Esempi di prompt:

### Eventi
```
"Crea un evento chiamato AWS Summit Milano per il 15 giugno 2024 a Milano Convention Center"

"Cerca informazioni sull'AWS re:Invent 2024 e crea un evento con tutti i dettagli"

"Mostrami tutti gli eventi di Milano"

"Cancella l'evento AWS Summit"
```

### Luoghi
```
"Aggiungi il ristorante La Pergola a Roma, categoria ristorante, indirizzo Via Cadlolo 101"

"Trova tutti i ristoranti"

"Aggiungi questi luoghi: 1) Stadio San Siro, categoria sport, Milano 2) Teatro alla Scala, categoria teatro, Milano"

"Filtra i luoghi per categoria museo"
```

---

## 6. Caricamento Multiplo

L'agente supporta il caricamento multiplo. Puoi dare prompt come:

```
"Aggiungi questi 3 eventi:
1. AWS Summit Milano, 15/06/2024
2. Google Cloud Next, 10/07/2024
3. Microsoft Build, 20/05/2024"
```

L'agente invocherà il tool `post-event` tre volte per creare tutti gli eventi.

---

## Note Importanti

1. **Descrizione Eventi**: L'agente invocherà automaticamente il researcher per recuperare dettagli sugli eventi quando l'utente non fornisce una descrizione completa.

2. **Categorie Luoghi**: Assicurati di usare una delle categorie predefinite: ristorante, sport, agriturismo, museo, teatro, cinema, bar, hotel, parco, altro.

3. **Filtri Frontend**: Il frontend supporta filtri per posizione e categoria per facilitare la ricerca.

4. **Tabelle DynamoDB**: Le lambda richiedono le tabelle `PersonalEvents` e `PersonalPlaces`. Aggiungi queste tabelle nel CDK stack.
