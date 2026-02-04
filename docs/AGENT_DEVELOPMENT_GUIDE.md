# Agent Development Guide

**Guida completa per sviluppare e debuggare agent in AWS Bedrock AgentCore**

Questa guida raccoglie tutte le best practices, pattern comuni, e tecniche di debugging per creare agent funzionanti nel framework AWS Bedrock AgentCore.

---

## Indice

1. [Setup e Struttura Base](#setup-e-struttura-base)
2. [Librerie e Dipendenze](#librerie-e-dipendenze)
3. [Pattern di Codice Comuni](#pattern-di-codice-comuni)
4. [Modelli e Configurazione](#modelli-e-configurazione)
5. [Gestione Input/Output](#gestione-inputoutput)
6. [Accorgimenti Particolari](#accorgimenti-particolari)
7. [Deployment](#deployment)
8. [Debugging](#debugging)
9. [Troubleshooting Comuni](#troubleshooting-comuni)
10. [Checklist Pre-Deployment](#checklist-pre-deployment)

---

## Setup e Struttura Base

### Struttura Directory Agent

```
agents/
└── nome-agent/
    ├── agent.py           # Codice principale dell'agent
    ├── requirements.txt   # Dipendenze Python
    ├── Dockerfile        # (Opzionale) Per deployment custom
    └── README.md         # Documentazione agent-specifica
```

### File `agent.py` - Template Base

```python
from strands_agents import Agent
from bedrock_agentcore import app
from bedrock_agentcore.llms import BedrockModel
from pydantic import BaseModel, Field
import json
import re
from typing import List, Optional

# Definisci schema output con Pydantic
class OutputSchema(BaseModel):
    """Schema per output strutturato"""
    campo1: List[str] = Field(description="Descrizione campo 1")
    campo2: List[str] = Field(description="Descrizione campo 2")

# Configura modello
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    temperature=0.2,
    streaming=False
)

# System prompt per l'agent
system_prompt = """
Sei un agent specializzato in [descrizione compito].

Regole:
1. [Regola 1]
2. [Regola 2]
3. Rispondi SOLO con JSON valido nel formato specificato
"""

# Crea agent
agent = Agent(model=model, system_prompt=system_prompt)

# Entry point OBBLIGATORIO
@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    Entry point dell'agent.
    
    Args:
        payload: Dict con parametri di input
        
    Returns:
        Dict con risultati elaborati
    """
    try:
        # Estrai input dal payload
        input_text = payload.get("text", "")
        
        if not input_text:
            return {"error": "Input 'text' mancante nel payload"}
        
        # Costruisci prompt per l'agent
        user_prompt = f"""
Analizza il seguente testo:

{input_text}

Rispondi con JSON valido nel formato:
{OutputSchema.schema_json(indent=2)}
"""
        
        # Invoca agent
        response = agent(user_prompt)
        
        # Parse response (gestisce dict e stringhe)
        result_text = response
        if isinstance(response, dict):
            if "content" in response and isinstance(response["content"], list):
                result_text = response["content"][0].get("text", "")
            elif "text" in response:
                result_text = response["text"]
        
        # Rimuovi markdown code fences se presenti
        result_text = re.sub(r"^```[a-zA-Z]*\n", "", result_text.strip())
        result_text = re.sub(r"\n```$", "", result_text.strip())
        
        # Parse JSON
        result_dict = json.loads(result_text)
        
        # Valida con Pydantic
        validated_output = OutputSchema(**result_dict)
        
        # Return come dict
        return validated_output.model_dump()
        
    except json.JSONDecodeError as e:
        return {"error": f"Errore parsing JSON: {str(e)}", "raw_response": result_text}
    except Exception as e:
        return {"error": f"Errore nell'elaborazione: {str(e)}"}
```

---

## Librerie e Dipendenze

### File `requirements.txt` Standard

```txt
strands-agents==1.24.0
strands-agents-tools==0.2.17
bedrock-agentcore==1.1.1
boto3>=1.42.7
requests>=2.31.0
pydantic>=2.0.0
```

### Librerie Chiave

| Libreria | Scopo | Note |
|----------|-------|------|
| `strands-agents` | Framework agent base | Versione 1.24.0 testata e funzionante |
| `bedrock-agentcore` | Runtime AWS AgentCore | Fornisce decorator `@app.entrypoint` |
| `bedrock-agentcore.llms` | Interfaccia modelli Bedrock | Classe `BedrockModel` |
| `pydantic` | Validazione output strutturato | Schema-based validation |
| `boto3` | SDK AWS | Per invocazioni cross-agent |

---

## Pattern di Codice Comuni

### 1. Decorator Entry Point

**❌ SBAGLIATO** (Pattern vecchio non supportato):
```python
@agent.function()
def invoke(payload):
    pass
```

**✅ CORRETTO** (Pattern AgentCore):
```python
from bedrock_agentcore import app

@app.entrypoint
def invoke(payload: dict) -> dict:
    pass
```

### 2. Configurazione Modello

**✅ Modello Raccomandato** (supporta on-demand throughput):
```python
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    temperature=0.2,        # Bassa per output deterministico
    streaming=False         # True solo se necessario streaming
)
```

**❌ Evitare**:
```python
# Questo modello NON supporta on-demand throughput in tutte le regioni
model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"
```

### 3. Invocazione Agent

**✅ Pattern Corretto**:
```python
agent = Agent(model=model, system_prompt=system_prompt)

# Invoca con prompt utente
response = agent(user_prompt)
```

**❌ Pattern NON Supportato**:
```python
# Questo metodo non esiste
response = model.generate(prompt)
```

### 4. Parsing Response

Le response degli agent possono avere strutture diverse. Usa questo pattern robusto:

```python
def extract_text_from_response(response):
    """Estrae testo da vari formati di response"""
    
    # Caso 1: Response è già una stringa
    if isinstance(response, str):
        return response
    
    # Caso 2: Response è dict con struttura content[0].text
    if isinstance(response, dict):
        if "content" in response and isinstance(response["content"], list):
            if len(response["content"]) > 0:
                return response["content"][0].get("text", "")
        
        # Caso 3: Response è dict con campo text diretto
        if "text" in response:
            return response["text"]
    
    # Fallback: converti a stringa
    return str(response)
```

### 5. Rimozione Markdown Code Fences

Claude spesso wrappa JSON in markdown. Usa questo pattern:

```python
import re

def clean_json_response(text: str) -> str:
    """Rimuove markdown code fences da response JSON"""
    # Rimuove ```json o ```python o ``` all'inizio
    text = re.sub(r"^```[a-zA-Z]*\n", "", text.strip())
    # Rimuove ``` alla fine
    text = re.sub(r"\n```$", "", text.strip())
    return text
```

### 6. Validazione con Pydantic

```python
from pydantic import BaseModel, Field, ValidationError

class MyOutput(BaseModel):
    items: List[str] = Field(description="Lista di elementi")
    score: float = Field(ge=0, le=1, description="Punteggio 0-1")

try:
    validated = MyOutput(**json_dict)
    return validated.model_dump()
except ValidationError as e:
    return {"error": f"Validazione fallita: {e}"}
```

---

## Modelli e Configurazione

### Modelli Disponibili

| Model ID | Region | On-Demand | Note |
|----------|--------|-----------|------|
| `us.anthropic.claude-sonnet-4-20250514-v1:0` | us-east-1 | ✅ | **RACCOMANDATO** |
| `anthropic.claude-3-5-sonnet-20241022-v2:0` | us-east-1 | ❌ | Richiede provisioned throughput |
| `anthropic.claude-3-5-haiku-20241022-v1:0` | us-east-1 | ✅ | Per task semplici |

### Parametri Temperatura

```python
# Output deterministico (estrazione dati, classificazione)
temperature=0.2

# Output creativo (generazione testo, brainstorming)
temperature=0.7

# Output molto deterministico
temperature=0.0
```

### Streaming vs Non-Streaming

```python
# Non-streaming (default, più semplice)
streaming=False
# Usa quando: output breve, JSON strutturato, parsing necessario

# Streaming (per response lunghe)
streaming=True
# Usa quando: output molto lungo, UI interattiva, real-time feedback
```

---

## Gestione Input/Output

### Payload Input Standard

Gli agent ricevono sempre un `dict` come payload:

```python
@app.entrypoint
def invoke(payload: dict) -> dict:
    # Estrai parametri con default
    text = payload.get("text", "")
    language = payload.get("language", "it")
    max_results = payload.get("max_results", 10)
    
    # Valida input obbligatori
    if not text:
        return {"error": "Parametro 'text' obbligatorio"}
```

### Output Schema Best Practices

**✅ Schema Chiaro e Tipizzato**:
```python
class ProjectUpdates(BaseModel):
    """Aggiornamenti estratti da testo progetto"""
    avanzamenti: List[str] = Field(
        description="Lista degli avanzamenti completati"
    )
    cose_da_fare: List[str] = Field(
        description="Lista delle attività ancora da completare"
    )
    punti_attenzione: List[str] = Field(
        description="Lista dei punti che richiedono attenzione"
    )
```

**❌ Schema Vago**:
```python
class Output(BaseModel):
    data: dict  # Troppo generico
    result: str  # Cosa contiene?
```

### Error Handling

Restituisci sempre un dict con chiave "error" in caso di fallimento:

```python
try:
    result = process_data(input_data)
    return {"success": True, "result": result}
except Exception as e:
    return {
        "success": False,
        "error": str(e),
        "error_type": type(e).__name__
    }
```

---

## Accorgimenti Particolari

### 1. System Prompt Efficaci

**✅ Buon System Prompt**:
```python
system_prompt = """
Sei un agent specializzato nell'estrazione di informazioni da testi di aggiornamento progetti.

COMPITO:
Analizza il testo fornito ed estrai:
1. Avanzamenti: attività completate o progressi fatti
2. Cose da fare: attività pianificate o ancora da completare  
3. Punti di attenzione: problemi, rischi, blocchi

REGOLE:
- Estrai solo informazioni esplicitamente presenti nel testo
- Ogni elemento deve essere una frase completa e chiara
- Non inventare o inferire informazioni non presenti
- Se una categoria è vuota, restituisci array vuoto []

FORMATO OUTPUT:
Rispondi SOLO con JSON valido nel seguente formato (senza markdown):
{
  "avanzamenti": ["...", "..."],
  "cose_da_fare": ["...", "..."],
  "punti_attenzione": ["...", "..."]
}
"""
```

**❌ System Prompt Vago**:
```python
system_prompt = "Analizza il testo e dimmi cosa c'è"
```

### 2. Gestione Lingua

Per agent multilingua:

```python
system_prompt = """
Sei un agent multilingua. Rispondi SEMPRE nella stessa lingua del testo input.

Input in italiano → Output in italiano
Input in inglese → Output in inglese
"""
```

### 3. Limiti Token e Context Window

```python
# Claude Sonnet 4 ha 200K token context window
# Ma per performance ottimali:
MAX_INPUT_LENGTH = 50000  # caratteri (~12.5K token)

if len(input_text) > MAX_INPUT_LENGTH:
    # Tronca o chunka l'input
    input_text = input_text[:MAX_INPUT_LENGTH]
```

### 4. Retry Logic (Optional)

Per invocazioni robuste:

```python
import time
from typing import Optional

def invoke_with_retry(agent, prompt: str, max_retries: int = 3) -> Optional[dict]:
    """Invoca agent con retry automatico"""
    for attempt in range(max_retries):
        try:
            response = agent(prompt)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

---

## Deployment

### 1. Build Locale (Testing)

```bash
# Naviga alla directory dell'agent
cd agents/nome-agent/

# Attiva ambiente virtuale
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt

# Test locale (se supportato)
python agent.py
```

### 2. Deploy su AgentCore

```bash
# Deploy nuovo agent
agentcore deploy nome-agent

# Attendi completamento build
# Verifica su CloudWatch Logs
```

### 3. Update Agent Esistente

```bash
# Dopo modifiche al codice
agentcore deploy nome-agent

# Il sistema:
# 1. Crea nuovo CodeBuild
# 2. Builda immagine Docker
# 3. Pusha su ECR
# 4. Aggiorna runtime
```

### 4. Verifica Deployment

```bash
# Lista agent deployati
agentcore list agents

# Mostra info agent specifico
agentcore describe agent nome-agent

# Test invocazione
agentcore invoke -a nome-agent '{"text": "test input"}'
```

---

## Debugging

### Livelli di Logging

1. **CodeBuild Logs**: Build e packaging container
2. **Runtime Logs**: Esecuzione agent e errori runtime

### 1. CodeBuild Logs (Build Failures)

**Quando usare**: Agent non si deploya, errori di build

```bash
# Ottieni Build ID dall'output del deploy
$buildId = "bedrock-agentcore-nome-agent-builder:uuid"

# Mostra tutti i log
$logInfo = aws codebuild batch-get-builds --ids $buildId --region us-east-1 --query 'builds[0].logs' --output json | ConvertFrom-Json
aws logs get-log-events --log-group-name $logInfo.groupName --log-stream-name $logInfo.streamName --region us-east-1 --start-from-head --query 'events[*].message' --output text

# Filtra solo errori
aws logs get-log-events --log-group-name $logInfo.groupName --log-stream-name $logInfo.streamName --region us-east-1 --start-from-head --query 'events[*].message' --output text | Select-String -Pattern "error|Error|ERROR|failed|Failed|FAILED" -Context 3
```

**Errori Comuni**:
- `ModuleNotFoundError`: Dipendenza mancante in requirements.txt
- `SyntaxError`: Errori Python nel codice
- `FileNotFoundError`: File richiesto non trovato nel container

### 2. Runtime Logs (Execution Failures)

**Quando usare**: Agent si deploya ma fallisce durante l'invocazione

```bash
# Trova Log Group Name
# Formato: /aws/bedrock-agentcore/runtimes/{agent-runtime-id}

# Mostra ultimi log
aws logs tail /aws/bedrock-agentcore/runtimes/nome-agent-abcd1234-DEFAULT --region us-east-1 --follow

# Filtra errori
aws logs filter-log-events --log-group-name /aws/bedrock-agentcore/runtimes/nome-agent-abcd1234-DEFAULT --region us-east-1 --filter-pattern "ERROR"

# Filtra per timestamp
aws logs filter-log-events --log-group-name /aws/bedrock-agentcore/runtimes/nome-agent-abcd1234-DEFAULT --region us-east-1 --start-time 1706947200000
```

**Errori Comuni**:
- `ValidationException`: Modello non supportato o parametri invalidi
- `JSONDecodeError`: Response non è JSON valido
- `KeyError`: Campo mancante nel payload
- `Timeout`: Agent impiega troppo tempo (default 30s)

### 3. Test Locale Pre-Deploy

Aggiungi al tuo `agent.py`:

```python
if __name__ == "__main__":
    # Test locale
    test_payload = {
        "text": "Test input per l'agent"
    }
    
    result = invoke(test_payload)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

Esegui:
```bash
python agent.py
```

### 4. Logging Strutturato

Aggiungi logging dettagliato nel codice:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.entrypoint
def invoke(payload: dict) -> dict:
    logger.info(f"📥 Received payload: {payload}")
    
    try:
        result = process(payload)
        logger.info(f"✅ Success: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        return {"error": str(e)}
```

### 5. Debug Response Parsing

Quando il JSON parsing fallisce:

```python
try:
    result_dict = json.loads(result_text)
except json.JSONDecodeError as e:
    # Log raw response per debug
    logger.error(f"Raw response that failed parsing:\n{result_text}")
    logger.error(f"JSON error: {str(e)}")
    
    # Restituisci per analisi
    return {
        "error": "JSON parsing failed",
        "json_error": str(e),
        "raw_response": result_text[:500]  # Primi 500 char
    }
```

---

## Troubleshooting Comuni

### Problema: "Agent already exists"

**Causa**: Agent con stesso nome già deployato

**Soluzione**:
```bash
# Rideploy sovrascrive automaticamente
agentcore deploy nome-agent
```

### Problema: "Model ... doesn't support on-demand throughput"

**Causa**: Modello richiede provisioned throughput

**Soluzione**: Usa `us.anthropic.claude-sonnet-4-20250514-v1:0`

```python
model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    temperature=0.2,
    streaming=False
)
```

### Problema: "AttributeError: 'Agent' object has no attribute 'function'"

**Causa**: Decorator sbagliato

**Soluzione**: Usa `@app.entrypoint` non `@agent.function()`

### Problema: JSON Response con Markdown Code Fences

**Causa**: Claude wrappa JSON in ```json ... ```

**Soluzione**: Strip markdown prima del parsing

```python
import re

result_text = re.sub(r"^```[a-zA-Z]*\n", "", result_text.strip())
result_text = re.sub(r"\n```$", "", result_text.strip())
```

### Problema: Response è Dict Nested non Stringa

**Causa**: Response structure `{"content": [{"text": "..."}]}`

**Soluzione**: Estrai text con pattern robusto

```python
if isinstance(response, dict):
    if "content" in response and isinstance(response["content"], list):
        result_text = response["content"][0].get("text", "")
```

### Problema: Docker Build Ok ma Runtime Fallisce

**Causa**: Codice buildata prima delle modifiche

**Soluzione**: 
1. Fai modifiche al codice
2. Rideploy: `agentcore deploy nome-agent`
3. Attendi nuovo build
4. Test con nuova versione

### Problema: Agent Timeout

**Causa**: Elaborazione troppo lunga (>30s default)

**Soluzione**:
- Ottimizza prompt per response più brevi
- Riduci input size
- Considera chunking per input grandi

---

## Checklist Pre-Deployment

### ✅ Codice

- [ ] Uso `@app.entrypoint` decorator
- [ ] Import corretti da `bedrock_agentcore` e `strands_agents`
- [ ] Model ID corretto: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- [ ] System prompt chiaro e specifico
- [ ] Pydantic schema definito per output
- [ ] JSON parsing robusto (gestisce dict e markdown)
- [ ] Error handling completo con return dict
- [ ] Logging strutturato per debug

### ✅ Dependencies

- [ ] File `requirements.txt` presente
- [ ] Versioni librerie specificate
- [ ] `strands-agents==1.24.0`
- [ ] `bedrock-agentcore==1.1.1`
- [ ] Tutte le dipendenze custom incluse

### ✅ Testing

- [ ] Test locale con `python agent.py` funziona
- [ ] Payload di test validato
- [ ] Output schema validato con Pydantic
- [ ] Edge cases testati (input vuoto, malformato, etc.)

### ✅ Documentation

- [ ] README.md con descrizione agent
- [ ] Esempi input/output
- [ ] Dipendenze documentate
- [ ] Use cases documentati

### ✅ Deployment

- [ ] `agentcore deploy nome-agent` completato con successo
- [ ] CodeBuild logs verificati (no errori)
- [ ] Runtime ARN ottenuto
- [ ] Test invocazione con `agentcore invoke` funziona
- [ ] CloudWatch runtime logs verificati

---

## Best Practices Riassuntive

### DO ✅

1. **Usa sempre `@app.entrypoint`** per entry point
2. **Model ID raccomandato**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
3. **System prompt specifici** con esempi formato output
4. **Pydantic schemas** per validazione strutturata
5. **Error handling robusto** con dict return
6. **Logging dettagliato** per debug
7. **Test locale** prima di deploy
8. **Verifica CloudWatch logs** dopo deploy
9. **Gestisci markdown** nelle response JSON
10. **Documenta tutto** per manutenibilità

### DON'T ❌

1. ❌ Non usare decorator `@agent.function()`
2. ❌ Non usare modelli senza on-demand throughput
3. ❌ Non assumere formato response fisso (gestisci dict/string)
4. ❌ Non ignorare markdown code fences nel JSON
5. ❌ Non deployare senza test locale
6. ❌ Non ignorare errori di build/runtime logs
7. ❌ Non usare system prompt vaghi
8. ❌ Non dimenticare error handling
9. ❌ Non usare `model.generate()` (non esiste)
10. ❌ Non hardcodare valori senza fallback

---

## Comandi Utili Rapidi

```bash
# Deploy agent
agentcore deploy nome-agent

# Lista agent
agentcore list agents

# Describe agent
agentcore describe agent nome-agent

# Test invocazione
agentcore invoke -a nome-agent '{"text": "test"}'

# Tail runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/agent-id-DEFAULT --region us-east-1 --follow

# Filtra errori runtime
aws logs filter-log-events --log-group-name /aws/bedrock-agentcore/runtimes/agent-id-DEFAULT --region us-east-1 --filter-pattern "ERROR"

# CodeBuild logs (sostituisci $buildId)
$logInfo = aws codebuild batch-get-builds --ids $buildId --region us-east-1 --query 'builds[0].logs' --output json | ConvertFrom-Json
aws logs get-log-events --log-group-name $logInfo.groupName --log-stream-name $logInfo.streamName --region us-east-1 --start-from-head --query 'events[*].message' --output text
```

---

## Riferimenti

- [DEPLOYMENT.md](DEPLOYMENT.md) - Guida deployment completa
- [DEBUG_DEPLOYMENT.md](DEBUG_DEPLOYMENT.md) - Troubleshooting deployment
- [MULTI_AGENT_SETUP.md](MULTI_AGENT_SETUP.md) - Orchestrazione multi-agent
- [QUICK_SUMMARY.md](QUICK_SUMMARY.md) - Overview progetto

---

**Versione**: 1.0  
**Ultima modifica**: 2026-02-03  
**Autore**: Estratto da sessioni di sviluppo reali con project-updates-extractor e altri agent

**Nota per AI**: Questo documento contiene pattern e best practices testati e validati. Segui questi pattern per evitare errori comuni e ridurre iteration di debug. I comandi e snippet forniti sono pronti all'uso nel contesto AWS Bedrock AgentCore.
