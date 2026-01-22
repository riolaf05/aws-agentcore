# 🚀 Deployment & Verification Checklist

## 📋 Pre-Deployment

### Code Review
- [ ] Verificare syntax Python (search_goal.py, post_goal.py, update_goal.py)
- [ ] Verificare syntax JavaScript (app.js)
- [ ] Verificare syntax CSS (modal-styles.css)
- [ ] Verificare HTML valido (index.html)
- [ ] Verificare nessun hardcoded password/token

### Dependencies
- [ ] Verificare boto3 versione in Lambda requirements.txt
- [ ] Verificare Python 3.9+ in Lambda runtime
- [ ] Verificare Flask versione nel backend
- [ ] Verificare CORS abilitato nel backend

---

## 🔧 Deployment Steps

### 1️⃣ AWS Lambda Deployment

#### New Lambda Function: search_goal
```bash
# 1. Pacchettizza il codice
cd lambdas/goal-api
zip search_goal.zip search_goal.py

# 2. Upload a AWS
aws lambda create-function \
  --function-name PersonalAssistant-GoalSearch \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler search_goal.lambda_handler \
  --zip-file fileb://search_goal.zip \
  --environment Variables="{GOALS_TABLE_NAME=PersonalGoals}"

# ✅ Salva ARN:
GOAL_SEARCH_LAMBDA_ARN="arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalSearch"
```

#### Update Existing Lambdas
```bash
# post_goal.py
zip post_goal.zip post_goal.py
aws lambda update-function-code \
  --function-name PersonalAssistant-GoalPost \
  --zip-file fileb://post_goal.zip

# update_goal.py
zip update_goal.zip update_goal.py
aws lambda update-function-code \
  --function-name PersonalAssistant-GoalUpdate \
  --zip-file fileb://update_goal.zip
```

#### Verify Deployments
```bash
# Test search_goal
aws lambda invoke \
  --function-name PersonalAssistant-GoalSearch \
  --payload '{"titolo":"Q1"}' \
  response.json
cat response.json

# Test post_goal con nota
aws lambda invoke \
  --function-name PersonalAssistant-GoalPost \
  --payload '{
    "ambito":"Reply",
    "titolo":"Test",
    "scadenza":"2025-03-31",
    "note":"Test note"
  }' \
  response.json

# Test update_goal con nota
GOAL_ID=$(cat response.json | jq -r '.goal_id')
aws lambda invoke \
  --function-name PersonalAssistant-GoalUpdate \
  --payload "{
    \"goal_id\":\"$GOAL_ID\",
    \"note\":\"Updated note\"
  }" \
  response.json
cat response.json | jq '.goal.note_history'
```

- [ ] search_goal.py deployed
- [ ] post_goal.py updated
- [ ] update_goal.py updated
- [ ] Tutti i test Lambda passano

### 2️⃣ Backend Deployment

```bash
# 1. Update backend.py con ARN
# ✏️ Modifica in backend.py:
GOAL_SEARCH_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalSearch"

# 2. Deploy backend
cd chat-frontend
python backend.py &  # o tramite Docker/systemd
```

#### Test Backend Endpoints
```bash
# Test /api/goals/search
curl "http://localhost:5000/api/goals/search?titolo=Q1"
# ✅ Atteso: { count, goals: [...] }

# Test /api/goals/<id>/notes
GOAL_ID="abc-123"
curl -X POST "http://localhost:5000/api/goals/$GOAL_ID/notes" \
  -H "Content-Type: application/json" \
  -d '{"note":"Test note","note_source":"frontend"}'
# ✅ Atteso: { message: "success", goal: {...} }

# Test PUT /api/goals con nota
curl -X PUT "http://localhost:5000/api/goals" \
  -H "Content-Type: application/json" \
  -d "{
    \"goal_id\":\"$GOAL_ID\",
    \"note\":\"Updated\",
    \"note_source\":\"frontend\"
  }"
# ✅ Atteso: goal con note_history aggiornata
```

- [ ] Backend avvia senza errori
- [ ] /api/goals/search funziona
- [ ] /api/goals/<id>/notes funziona
- [ ] PUT /api/goals con nota funziona

### 3️⃣ Frontend Deployment

```bash
# 1. Deploy files aggiornati
cd chat-frontend
# - index.html (modal aggiornato)
# - app.js (logica note aggiornata)
# - modal-styles.css (stili note aggiunti)

# Opzione A: Static file server
python -m http.server 8000

# Opzione B: Docker
docker build -t personal-copilot-frontend .
docker run -p 8000:80 personal-copilot-frontend

# Opzione C: Nginx/Apache - upload files
scp index.html app.js modal-styles.css user@server:/var/www/html/
```

#### Test Frontend
```
1. Apri http://localhost:8000 nel browser
2. Login con credenziali test
3. Naviga a "Obiettivi"
4. Clicca "Modifica" su un obiettivo
5. ✅ Verifica:
   - Modal si apre
   - Nuovo textarea "Aggiungi nota" presente
   - Se goal ha note: storico visibile
   - Note mostrano timestamp e badge fonte
   - Button "Salva" funziona
6. Aggiungi una nota e salva
7. ✅ Verifica nota appare nello storico
```

- [ ] Frontend carica senza errori
- [ ] Modal edit si apre
- [ ] Textarea nota presente
- [ ] Storico note visibile
- [ ] Aggiunta nota funziona
- [ ] Note_history si aggiorna

### 4️⃣ Agent Deployment

#### Orchestrator Update
```bash
cd agents/orchestrator

# 1. Verifica system prompt aggiornato
# ✅ Deve contenere esempi di comandi con note

# 2. Deploy (tramite CLI bedrock-agentcore)
bedrock-agentcore deploy
# o
docker build -t orchestrator .
docker push ECR_REPO/orchestrator:latest
```

#### Project-Goal-Writer-Reader Update
```bash
cd agents/project-goal-writer-reader

# 1. Verifica system prompt aggiornato
# ✅ Deve avere flusso di lavoro per search-goal + update-goal

# 2. Deploy
bedrock-agentcore deploy
# o
docker build -t project-goal-writer-reader .
docker push ECR_REPO/project-goal-writer-reader:latest
```

#### Test Agents
```
1. Via Orchestrator chat:
   "Crea un obiettivo Test"
   ✅ Goal creato

2. Cerca goal:
   "Mostra l'obiettivo Test"
   ✅ Dettagli visualizzati

3. Aggiungi nota:
   "Aggiungi nota all'obiettivo Test: primo aggiornamento"
   ✅ Agent:
      - Cerca goal per titolo
      - Riceve goal_id
      - Aggiorna con nota
      - Conferma all'utente

4. Visualizza note:
   "Mostrami gli aggiornamenti dell'obiettivo Test"
   ✅ Agent mostra storico note
      con timestamp e source badge
```

- [ ] Orchestrator deployment successful
- [ ] Project-goal-writer-reader deployment successful
- [ ] Comandi orchestrator funzionano
- [ ] Agent trova goal per titolo
- [ ] Agent aggiunge nota
- [ ] Note_source = "agent" in database

---

## ✅ Integration Testing

### Test Scenario 1: Create + Note Frontend
```
1. Frontend: Nuovo obiettivo
   POST /api/goals con note="Nota iniziale"
   ✅ Goal creato con note_history[0]

2. Frontend: Modifica goal
   GET /api/goals?goal_id=xxx
   ✅ Note storia caricata nel modal

3. Frontend: Aggiungi nota
   PUT /api/goals con note="Aggiornamento"
   ✅ note_history[1] aggiunto
```

- [ ] Scenario 1 completo

### Test Scenario 2: Search + Update Agent
```
1. Orchestrator: "Aggiungi nota a Q1"
   Agent invoca search-goal(titolo="Q1")
   ✅ Riceve goal_id

2. Agent invoca update-goal(goal_id, note, source="agent")
   ✅ note_history aggiornato con source="agent"

3. Frontend: Modifica goal
   ✅ Vede nota con badge 🤖 Agent
```

- [ ] Scenario 2 completo

### Test Scenario 3: Filter + Display
```
1. Creare 3 goals con note diverse
2. Frontend: Filtra per ambito
   ✅ Goals caricati con note

3. Orchestrator: Mostra note di goal
   ✅ Agent formatta nota_history
```

- [ ] Scenario 3 completo

### Test Scenario 4: Update Multiple Fields + Note
```
1. Frontend: Modifica status + priorita + aggiungi nota
   PUT /api/goals con tutti parametri
   ✅ Goal aggiornato
   ✅ note_history aggiunto

2. Verifica che nota ha timestamp corretto
   ✅ Source = "frontend"
```

- [ ] Scenario 4 completo

---

## 🧪 Performance Testing

### Load Test - Note History
```bash
# Test con 100 note per goal
GOAL_ID="test-heavy"
for i in {1..100}; do
  curl -X PUT http://localhost:5000/api/goals \
    -H "Content-Type: application/json" \
    -d "{
      \"goal_id\":\"$GOAL_ID\",
      \"note\":\"Note numero $i\"
    }"
done

# Tempo atteso: < 50ms per update
# Size atteso: < 400KB (DynamoDB limit)
```

- [ ] Update con molte note < 100ms
- [ ] DynamoDB item size < 400KB
- [ ] Search ritorna risultati < 200ms

---

## 🔒 Security Verification

### Input Validation
```bash
# Test: SQL injection attempt (non applicabile a DynamoDB ma test anyway)
curl "http://localhost:5000/api/goals/search?titolo='; DROP--"
✅ Deve ritornare risultati di ricerca normali o array vuoto

# Test: XSS in nota
curl -X PUT http://localhost:5000/api/goals \
  -H "Content-Type: application/json" \
  -d "{
    \"goal_id\":\"xxx\",
    \"note\":\"<script>alert('xss')</script>\"
  }"
✅ Frontend deve escapare il testo (escapeHtml)

# Test: Invalid JSON
curl -X PUT http://localhost:5000/api/goals \
  -d "{invalid json}"
✅ Deve ritornare 400 Bad Request
```

- [ ] Validazione input funziona
- [ ] XSS prevention funziona
- [ ] Error handling corretto

### Data Privacy
```bash
# Verifica nessun dato sensibile nei log
grep -r "password\|token\|secret" lambdas/goal-api/
grep -r "password\|token\|secret" chat-frontend/
✅ Nessun risultato
```

- [ ] Nessun secret nei codice
- [ ] Log non contiene dati sensibili

---

## 📊 Monitoring & Logging

### CloudWatch Setup
```bash
# Verificare log groups per Lambda
aws logs describe-log-groups --query 'logGroups[].logGroupName'
✅ Deve includere:
  /aws/lambda/PersonalAssistant-GoalSearch
  /aws/lambda/PersonalAssistant-GoalPost
  /aws/lambda/PersonalAssistant-GoalUpdate

# Check logs
aws logs tail /aws/lambda/PersonalAssistant-GoalSearch --follow
```

- [ ] Log group per search_goal creato
- [ ] Log group per post_goal aggiornato
- [ ] Log group per update_goal aggiornato

### Metrics
```bash
# Creare CloudWatch Alarms
aws cloudwatch put-metric-alarm \
  --alarm-name goal-search-errors \
  --alarm-description "Alert on search_goal errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=PersonalAssistant-GoalSearch
```

- [ ] Alarms configurati per Lambda errors
- [ ] Alarms configurati per DynamoDB throttling

---

## 🧹 Rollback Plan

### Se deployment fallisce:
```bash
# 1. Rollback Lambda
aws lambda update-function-code \
  --function-name PersonalAssistant-GoalSearch \
  --zip-file fileb://BACKUP/search_goal_v1.zip

# 2. Rollback Frontend (serve versione precedente)
git revert HEAD
# o restore da backup

# 3. Rollback Backend ARN
# Commenta GOAL_SEARCH_LAMBDA_ARN o usa versione precedente
python backend.py --version=v1

# 4. Rollback Agents
bedrock-agentcore rollback --agent orchestrator --version previous
```

- [ ] Backup dei file precedenti salvati
- [ ] Versioni Lambda taggate
- [ ] Git tags per frontend versioni

---

## 📝 Post-Deployment Checks

### Day 1
- [ ] Controllare CloudWatch logs per errori
- [ ] Testare frontend search manuale
- [ ] Testare agent con note
- [ ] Verificare DynamoDB query metrics
- [ ] Controllare database size growth

### Week 1
- [ ] Raccogliere feedback utenti
- [ ] Controllare error rate trend
- [ ] Verificare performance metrics
- [ ] Aggiornare documentazione se necessario
- [ ] Pianificare follow-up features

### Ongoing
- [ ] Monitora CloudWatch alarms
- [ ] Backup DynamoDB regular
- [ ] Aggiorna Lambda dependencies
- [ ] Monitora costs AWS

---

## 📞 Support & Escalation

### Errori Comuni

**Error: Lambda function not found**
```
→ Verificare ARN in backend.py
→ Verificare function name spelling
→ Verificare region (us-east-1)
```

**Error: DynamoDB Scan timeout**
```
→ Reduce limit parameter
→ Aggiungere index (se necessario)
→ Ottimizzare FilterExpression
```

**Error: Note non appare nel frontend**
```
→ Verificare console browser (Network tab)
→ Verificare response status 200
→ Verificare note_history nel response JSON
→ Controllare escapeHtml() funzione
```

**Error: Agent non trova goal**
```
→ Prova titolo esatto (case-sensitive)
→ Controlla database via AWS Console
→ Verificare search-goal response
→ Aumenta limit parameter
```

---

## ✅ Final Verification Checklist

### Functionality
- [ ] Creare goal con nota iniziale
- [ ] Ricercare goal per titolo
- [ ] Aggiungere nota a goal esistente
- [ ] Visualizzare storico note
- [ ] Aggiornare goal + nota simultaneamente
- [ ] Agent trova goal per titolo
- [ ] Agent aggiunge nota
- [ ] Frontend mostra badge agent/frontend
- [ ] Timestamp formattati correttamente
- [ ] Note text preserva white-space

### Performance
- [ ] Search < 200ms
- [ ] Update < 50ms
- [ ] Frontend carica < 1s
- [ ] 100 note per goal < 400KB size

### Security
- [ ] Nessun XSS
- [ ] Nessun SQL injection
- [ ] Nessun secret in logs
- [ ] Error messages generici

### UI/UX
- [ ] Modal responsive
- [ ] Note textarea accessibile
- [ ] Storico scrollabile
- [ ] Badge chiaramente visibili
- [ ] Feedback user (success/error messages)

---

## 🎉 Deployment Complete!

When all checks are complete:

```
✅ Implementazione Goal Notes COMPLETA
✅ Deployment completato con successo
✅ Tutti i test passano
✅ Documentazione aggiornata
✅ Team informato e addestrato

→ Sistema pronto per production use!
```

---

**Last Updated**: 2025-01-20
**Status**: Ready for Deployment

