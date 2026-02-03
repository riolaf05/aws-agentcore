# Project Updates Extractor Agent

Agent specializzato nell'estrazione strutturata di aggiornamenti da testi narrativi di progetto.

## Funzionalità

Analizza testi di aggiornamento progetto ed estrae automaticamente:

- **✅ Avanzamenti**: progressi completati, milestone raggiunte, funzionalità rilasciate
- **📝 Cose da fare**: attività pianificate, task pendenti, prossimi passi
- **⚠️ Punti di attenzione**: rischi, problemi, blocchi, criticità

## Input/Output

**Input**: Testo narrativo di aggiornamento progetto (string)

**Output**: JSON con struttura:
```json
{
  "avanzamenti": ["punto 1", "punto 2", ...],
  "cose_da_fare": ["task 1", "task 2", ...],
  "punti_attenzione": ["rischio 1", "problema 2", ...]
}
```

## Deploy

```bash
# Build Docker image
docker build -t project-updates-extractor .

# Deploy to AgentCore
aws bedrock-agentcore deploy-agent \
  --name project-updates-extractor \
  --docker-image project-updates-extractor:latest
```

## Test locale

```python
from src.agent import extract_project_updates

text = """
Nel corso dell'ultima settimana il team ha completato 
l'integrazione tra il modulo di gestione candidati e 
il sistema di shortlist...
"""

result = extract_project_updates(text)
print(result)
```

## Integrazione

Utilizzato nel flusso di upload della Knowledge Base per:
1. Identificare l'obiettivo associato al documento
2. Estrarre aggiornamenti strutturati dal testo
3. Salvare gli aggiornamenti nell'obiettivo tramite goal-notes-writer agent
