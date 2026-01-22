# 🤖 Comandi Orchestrator per Goal Notes

## 📋 Lista Completa Comandi Supportati

### 1. 🆕 **Cercare un Obiettivo per Nome**
```
"Cerca l'obiettivo Q1"
"Mostrami l'obiettivo Aumentare fatturato Q1"
"Dammi i dettagli dell'obiettivo per Reply"
```
**Cosa fa:**
- Orchestrator invoca `project-goal-writer-reader`
- Agent usa `search-goal` per cercare per titolo
- Ritorna goal_id + tutti i dettagli incluso note_history

---

### 2. ✨ **Aggiungere una Nota a un Obiettivo**
```
"Aggiungi una nota all'obiettivo Q1: Ho contattato 10 nuovi lead"
"Aggiorna l'obiettivo Aumentare fatturato con nota: completata analisi di mercato"
"Nota sull'obiettivo Progetto AI: in corso integrazione del modello"
```
**Cosa fa:**
1. Orchestrator invoca `project-goal-writer-reader`
2. Agent:
   - Esegue `search-goal` per trovare l'obiettivo per nome
   - Riceve il `goal_id`
   - Usa `update-goal` per aggiungere la nota
3. Lambda aggiunge nota a `note_history` con:
   - timestamp automatico
   - source = "agent"
   - testo della nota

**Note nel database:**
```json
{
  "timestamp": "2025-01-20T14:30:00",
  "note": "Ho contattato 10 nuovi lead",
  "source": "agent"
}
```

---

### 3. 📊 **Aggiornare Obiettivo con Nota**
```
"Completa l'obiettivo Progetto Dashboard e aggiungi nota: deployment in produzione"
"Cambia priorità dell'obiettivo Q1 a URGENTE e aggiungi nota: deadline si avvicina"
"Cancella l'obiettivo old-goal con nota: non più rilevante"
```
**Cosa fa:**
- Agent esegue search-goal → update-goal
- Modifica parametri (status, priority, etc.) + aggiunge nota
- Una sola richiesta combine tutto

**Payload alla lambda:**
```json
{
  "goal_id": "xxx",
  "status": "completed",
  "note": "deployment in produzione",
  "note_source": "agent"
}
```

---

### 4. 📋 **Visualizzare Note di un Obiettivo**
```
"Mostrami le note dell'obiettivo Q1"
"Che aggiornamenti ci sono sull'obiettivo Progetto AI?"
"Visualizza lo storico dell'obiettivo Aumentare fatturato"
```
**Cosa fa:**
- Agent esegue search-goal o get-goal
- Recupera `note_history`
- Formatta e visualizza note con timestamp e source

**Output user-friendly:**
```
Obiettivo: Aumentare fatturato Q1
Status: active | Priorità: high

📋 Storico Aggiornamenti:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent - 20 Gen 2025, 14:30
Ho contattato 10 nuovi lead

👤 Frontend - 19 Gen 2025, 09:15
Completata analisi di mercato

👤 Frontend - 15 Gen 2025, 10:00
Nota iniziale: strategie da implementare
```

---

### 5. 🔍 **Cercare Obiettivi per Ambito con Note**
```
"Mostrami tutti gli obiettivi per Reply e le loro note"
"Quali obiettivi urgenti ho per MatchGuru?"
"Elenca gli obiettivi completati per Reply"
```
**Cosa fa:**
- Agent usa get-goal con filtri (ambito, status, priorita)
- Recupera tutti gli obiettivi matching
- Mostra titolo, status, last note, deadline

---

### 6. 💡 **Scenario: Conversazione Multi-turno**

#### User (Turno 1):
```
"Crea un nuovo obiettivo per aumentare il fatturato"
```
→ Orchestrator → project-goal-writer-reader → post-goal

#### User (Turno 2):
```
"Aggiungi una nota: ho iniziato a contattare clienti"
```
→ Orchestrator → search-goal + update-goal

#### User (Turno 3):
```
"Quali sono le note? Mostrami gli ultimi aggiornamenti"
```
→ Orchestrator → search-goal → formatta note_history

#### User (Turno 4):
```
"Cambia priorità a urgente e aggiungi nota che è critical"
```
→ Orchestrator → update-goal con status + note

---

## 🎯 Esempi Realistici

### Scenario 1: Gestione Progetto Reply
```
User: "Ho una nuova task per Reply. Aumentare fatturato del 20%"
Agent:
  ✓ post-goal(ambito="Reply", titolo="Aumentare fatturato 20%", 
              scadenza="2025-03-31", priorita="high", 
              note="Nuovo obiettivo strategico")

User: "Aggiornami. Ho contattato 5 aziende leader"
Agent:
  ✓ search-goal(titolo="Aumentare fatturato")
  ✓ update-goal(goal_id=xxx, 
                note="Contattate 5 aziende leader", 
                note_source="agent")

User: "Che progress abbiamo?"
Agent:
  ✓ get-goal(goal_id=xxx)
  → Mostra: Titolo | Status: active | Priorità: high
           📋 2 note nello storico
           Deadline: 31 Mar 2025
           Last update: proprio ora
```

---

### Scenario 2: Progetto con Multi-Agent Update
```
User: "Monitora il progetto Analisi IA"
Agent (Orchestrator) → invoke_agent("candidate_matcher", "...")
                    → invoke_agent("researcher", "...")

User: "Aggiungi nota con i risultati della ricerca"
Agent:
  ✓ search-goal(titolo="Analisi IA")
  ✓ update-goal(goal_id=xxx,
                note="Ricerca completata: 3 framework idonei trovati",
                note_source="agent")
  → Note aggiunta con timestamp
```

---

## 🔐 Validazioni Automatiche

### What the Backend Checks:
```python
# search-goal valida:
✓ titolo non vuoto
✓ titolo almeno 1 carattere
✓ limit <= 1000

# update-goal valida:
✓ goal_id esiste in DynamoDB
✓ Se note presente: testo non vuoto
✓ note_source in ["frontend", "agent"]

# post-goal valida:
✓ ambito, titolo, scadenza obbligatori
✓ priorita in [low, medium, high, urgent]
✓ scadenza formato YYYY-MM-DD
```

---

## 💬 Natural Language Variations

L'Orchestrator comprende variazioni:

```
❌ Non funziona
"Nota il Q1"
"Aggiungi goal note"

✅ Funziona
"Aggiungi una nota all'obiettivo Q1: ..."
"Aggiorna l'obiettivo Q1 con nota: ..."
"Nota sull'obiettivo Q1: ..."
"Mostrami le note di Q1"
"Che aggiornamenti ci sono su Q1?"
```

---

## 🚀 Tips & Tricks

### 1. **Batch Updates**
```
"Per l'obiettivo Reply Q1:
1. Aggiungi nota: lead contattati
2. Cambia priorità a high
3. Sposta scadenza a fine febbraio"
```
Agent esegue tutto in una singola update-goal call

### 2. **Ricerca Fuzzy**
```
"Mostrami gli aggiornamenti per l'obiettivo fatturato"
```
search-goal trova "Aumentare fatturato Q1" anche se digiti solo "fatturato"

### 3. **Timeline Tracking**
```
"Dammi la timeline dell'obiettivo Progetto X"
```
Agent formatta note_history come timeline cronologica

### 4. **Status Flow**
```
"Completa l'obiettivo e aggiungi nota finale"
```
Agent imposta status="completed" + aggiunge nota in una call

---

## ⚡ Performance Notes

- **Ricerca**: ~100ms (Scan completo di DynamoDB)
- **Update**: ~50ms (Put item)
- **History display**: ~200ms per 20 note

Per > 100 note per goal, considerare archivio separato

---

## 🔧 Troubleshooting

### Comando non funziona
```
❌ User: "Aggiungi nota"
✅ Aggiungi dettagli: "Aggiungi nota all'obiettivo Q1: ..."
```

### Nota non appare
1. Verifica che goal esista: `"Mostra l'obiettivo <nome>"`
2. Verifica note_history: controlla frontend modal di edit
3. Controlla timestamp: la nota dovrebbe avere timestamp ISO

### Goal non trovato
1. Prova nome diverso: `"Cerca obiettivi per Reply"`
2. Prova cercare per ambito: `"Mostrami gli obiettivi Reply"`

---

## 📞 Chat Examples

**User → Orchestrator:**
```
"Crea un obiettivo per aumentare il fatturato di Reply. 
 Scadenza fine marzo. Alta priorità. Nota iniziale: 
 contattare aziende leader"
```

**Agent Path:**
```
invoke_agent("project_goal_writer_reader", 
  "Crea un obiettivo con:
   - ambito: Reply
   - titolo: Aumentare fatturato
   - scadenza: 2025-03-31
   - priorita: high
   - nota: contattare aziende leader")
```

**Backend:**
```
POST /goals
{
  ambito: "Reply",
  titolo: "Aumentare fatturato",
  scadenza: "2025-03-31",
  priorita: "high",
  note: "contattare aziende leader"
}

Response:
{
  goal_id: "123abc",
  note_history: [{
    timestamp: "2025-01-20T10:00:00",
    note: "contattare aziende leader",
    source: "frontend"  ← actually agent, but marks as frontend for now
  }]
}
```

---

## ✅ Checklist per Testing

- [ ] Creare obiettivo con nota iniziale
- [ ] Cercare obiettivo per titolo
- [ ] Aggiungere nota via agent
- [ ] Visualizzare note_history
- [ ] Aggiornare status + nota
- [ ] Verificare timestamp
- [ ] Verificare source badge
- [ ] Testare variazioni linguistiche
- [ ] Testare con ambito filter
- [ ] Testare delete + nota

