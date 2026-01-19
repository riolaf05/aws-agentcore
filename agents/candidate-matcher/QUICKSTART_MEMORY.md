# 🚀 Quick Start - Memory Setup & Test

## ⚙️ Prerequisito: Permessi IAM

Prima di iniziare, assicurati che la **IAM execution role dell'agente** abbia i permessi per accedere alla memoria.

**Cosa fa questa role?**
- È la role IAM che l'agente assume quando viene eseguito su AWS
- Senza permessi corretti, l'agente NON può leggere o scrivere nella memoria
- Il nome della role è visibile nel file `.bedrock_agentcore.yaml` sotto `aws.execution_role`

**Permessi necessari:**
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:ListEvents",      // Legge cronologia conversazioni
    "bedrock-agentcore:CreateEvent",     // Salva nuovi messaggi
    "bedrock-agentcore:GetMemory",       // Info configurazione memoria
    "bedrock-agentcore:ListMemories"     // Elenca memorie disponibili
  ],
  "Resource": "arn:aws:bedrock-agentcore:REGION:ACCOUNT:memory/MEMORY_ID"
}
```

**Applicazione automatica:**

Lo script `setup_memory.py` crea automaticamente il file `memory-policy.json`. Dopo aver creato la memoria, esegui:

```bash
# Trova il nome della tua execution role
grep "execution_role:" .bedrock_agentcore.yaml

# Applica i permessi (sostituisci ROLE_NAME con la tua role)
aws iam put-role-policy \
  --role-name AmazonBedrockAgentCoreSDKRuntime-us-east-1-xxxxxx \
  --policy-name CandidateMatcherMemoryAccess \
  --policy-document file://memory-policy.json
```

> ⚠️ **Senza questi permessi vedrai errori `AccessDeniedException` nei log!**

---

## In 5 Minuti: Setup della Memory

### 1️⃣ Setup automatico (30 secondi)

```bash
cd agents/candidate-matcher
python setup_memory.py
```

Output:
```
======================================================================
🧠 Bedrock AgentCore Memory Setup - Candidate Matcher
======================================================================

✅ Memory creata con successo!

   Memory ID: mem-8f2a5d7c9e1b4f3a
   Region: us-east-1
   Status: ACTIVE

💾 Configurazione salvata in .env
```

### 2️⃣ Carica le variabili

```bash
source .env  # macOS/Linux
# Oppure su Windows:
# type .env | findstr MEMORY
# export MEMORY_ID=mem-xxxxxxx
```

### 3️⃣ Deploy (2-5 minuti)

```bash
agentcore launch
```

Output finale:
```
✅ Agent deployed successfully
   Agent ID: agent-xxxxx
   Status: ACTIVE
```

---

## 🧪 Test della Memory

### Test 1: Single Message (senza memory)

```bash
agentcore invoke '{"prompt":"Sono Marco, sviluppatore Python con 8 anni di esperienza"}'
```

### Test 2: Multi-Turn with Memory ⭐

```bash
# Crea una sessione unica
SESSION_ID="test-$(date +%s)"

echo "Turno 1: Presentazione..."
agentcore invoke '{"prompt":"Sono Marco, sviluppatore Python","session_id":"'$SESSION_ID'"}'

echo "Turno 2: Memory viene caricata..."
agentcore invoke '{"prompt":"8 anni di esperienza, so AWS e Docker","session_id":"'$SESSION_ID'"}'

echo "Turno 3: Continua naturalmente..."
agentcore invoke '{"prompt":"Parlo inglese fluentemente","session_id":"'$SESSION_ID'"}'
```

**Aspettative:**
- Turno 1: L'agente introduce sé stesso
- Turno 2: **Vedi `📚 Caricati X messaggi dalla memoria`** ✅
- Turno 3: L'agente non ripete domande, continua naturalmente

### Test 3: Matching Completo

```bash
SESSION="full-interview-$(date +%s)"

# Turno 1: Ruolo attuale
agentcore invoke '{
  "prompt": "Ciao, sono Paolo. Sono un Senior Data Scientist con 10 anni di esperienza",
  "session_id": "'$SESSION'",
  "candidate_id": "paolo-data-scientist"
}'

# Turno 2: Skills aggiuntive
agentcore invoke '{
  "prompt": "Conosco Python, R, SQL, e ho esperienza con ML e Big Data",
  "session_id": "'$SESSION'",
  "candidate_id": "paolo-data-scientist"
}'

# Turno 3: Troverai i matching
agentcore invoke '{
  "prompt": "Sono pronto, cercami i migliori needs",
  "session_id": "'$SESSION'",
  "candidate_id": "paolo-data-scientist"
}'
```

---

## 📊 Visualizzare i Dati in Memoria

### Vedere tutti gli events

```bash
aws bedrock-agentcore list-events \
  --memory-id $(cat .env | grep MEMORY_ID | cut -d'=' -f2) \
  --actor-id candidate \
  --session-id $SESSION_ID \
  --region us-east-1 \
  --output json
```

### Contare i turni salvati

```bash
aws bedrock-agentcore list-events \
  --memory-id $(cat .env | grep MEMORY_ID | cut -d'=' -f2) \
  --actor-id candidate \
  --session-id $SESSION_ID \
  --region us-east-1 \
  --query 'length(events)' \
  --output text
```

---

## 🔧 Troubleshooting

### ❌ "MEMORY_ID not found"

**Soluzione:**
```bash
# Verifica che .env esiste
cat .env

# Se non esiste, ricrea
python setup_memory.py

# Carica manualmente
export MEMORY_ID=mem-xxxxxxx
```

### ❌ "Memory not in ACTIVE state"

**Soluzione:**
```bash
# Attendi 30-60 secondi e riprova
sleep 30
agentcore launch
```

### ❌ "Access Denied" su bedrock-agentcore

**Soluzione:**
```bash
# Verifica credenziali AWS
aws sts get-caller-identity

# Verifica IAM permissions
aws iam get-role --role-name agentcore-taskapigateway-role
```

### ❌ Memory vuota anche dopo i test

**Causa possibile:** Session ID diversi ad ogni esecuzione

**Soluzione:**
```bash
# Sempre usa lo stesso SESSION_ID
SESSION_ID="test-123"  # Fisso

# Turno 1
agentcore invoke '{"prompt":"...", "session_id":"'$SESSION_ID'"}'

# Turno 2 - STESSO SESSION_ID
agentcore invoke '{"prompt":"...", "session_id":"'$SESSION_ID'"}'
```

---

## 📚 Documentazione Completa

| File | Argomento |
|------|-----------|
| [README.md](./README.md) | Overview generale dell'agente |
| [MEMORY_SETUP.md](./MEMORY_SETUP.md) | Setup dettagliato della memory |
| [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md) | Come funziona internamente |

---

## 💡 Comportamento Atteso

### Senza Memory

```
USER 1: "Sono Marco, sviluppatore Python"
AGENT:  "Marco, sei sviluppatore Python"

USER 2: "8 anni di esperienza"
AGENT:  "Capito. Qual è il tuo ruolo attuale?" ❌ Ridondante!
```

### Con Memory ✅

```
USER 1: "Sono Marco, sviluppatore Python"
AGENT:  "Marco, sei sviluppatore Python"
        [Salva in memoria]

USER 2: "8 anni di esperienza"
AGENT:  "📚 Caricati 2 messaggi dalla memoria"
        "Perfetto Marco! Con 8 anni, sei senior.
         Conosci anche AWS?"
        [Salva nuovo turno]
```

---

## ⚡ Performance

| Operazione | Tempo |
|-----------|-------|
| Carica memoria | ~200ms |
| Salva turno | ~100ms |
| Risposta agente | ~2-5s |
| **Totale per turno** | **~3-6s** |

---

## 🎯 Prossimi Step

✅ **Fatto**: Setup della memory
✅ **Fatto**: Deploy dell'agente
⏭️ **Next**: Test multi-turno della conversazione
⏭️ **Advanced**: Passare a LTM (Long-Term Memory)
⏭️ **Integration**: Aggiungere a orchestrator agent

---

## 📞 Need Help?

Se la memory non funziona:

1. Verifica il file `.env`:
   ```bash
   cat .env
   ```

2. Controlla se la memory è ACTIVE:
   ```bash
   aws bedrock-agentcore get-memory \
     --memory-id $(cat .env | grep MEMORY_ID | cut -d'=' -f2) \
     --region us-east-1
   ```

3. Verifica i permessi IAM:
   ```bash
   aws iam list-attached-role-policies \
     --role-name agentcore-taskapigateway-role
   ```

4. Leggi i log completi di deployment:
   ```bash
   agentcore launch --verbose
   ```
