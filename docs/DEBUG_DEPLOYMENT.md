# Debugging degli Errori di Deployment - Guida Completa

Questa guida spiega come debuggare i fallimenti di deployment degli agenti Bedrock AgentCore usando i log di CloudBuild.

## Flusso di Deployment e Possibili Fallimenti

Quando esegui `agentcore launch`, il processo passa per queste fasi:

```
1. QUEUED → 2. PROVISIONING → 3. DOWNLOAD_SOURCE → 4. INSTALL → 
5. PRE_BUILD → 6. BUILD (Docker Build) → 7. POST_BUILD (Docker Push) → 
8. UPLOAD_ARTIFACTS → 9. FINALIZING → 10. COMPLETED
```

Se una fase fallisce, il deployment si interrompe. Le fasi più critiche sono:
- **BUILD**: Construccione del Docker image
- **POST_BUILD**: Push dell'immagine a ECR

## Localizzare i Log

### Step 1: Trovare il Project Name

Controlla il `.bedrock_agentcore.yaml`:

```yaml
agents:
  candidate_matcher:
    codebuild:
      project_name: bedrock-agentcore-candidate_matcher-builder
```

### Step 2: Ottenere l'ID del Build

```powershell
# Trovare l'ultimo build ID
$buildId = aws codebuild list-builds-for-project `
    --project-name bedrock-agentcore-candidate_matcher-builder `
    --region us-east-1 `
    --query 'ids[0]' `
    --output text

Write-Host "Build ID: $buildId"
```

### Step 3: Ottenere i Dettagli del Build

```powershell
# Visualizzare lo stato e le fasi
aws codebuild batch-get-builds `
    --ids $buildId `
    --region us-east-1 `
    --query 'builds[0].[status,phases[*].[phaseType,phaseStatus,endTime]]' `
    --output text
```

Output atteso:
```
FAILED
SUBMITTED       SUCCEEDED       2026-01-16T13:38:36.416000+01:00
QUEUED          SUCCEEDED       2026-01-16T13:38:37.143000+01:00
PROVISIONING    SUCCEEDED       2026-01-16T13:38:44.984000+01:00
DOWNLOAD_SOURCE SUCCEEDED       2026-01-16T13:38:46.731000+01:00
BUILD           FAILED          2026-01-16T13:39:28.137000+01:00     ← ERRORE QUI
POST_BUILD      FAILED          2026-01-16T13:39:28.204000+01:00
```

### Step 4: Ottenere i Log di CloudWatch

Trova il CloudWatch log group e stream:

```powershell
# Ottenere i dettagli dei log
aws codebuild batch-get-builds `
    --ids $buildId `
    --region us-east-1 `
    --query 'builds[0].logs' `
    --output json | ConvertFrom-Json
```

Output:
```json
{
  "groupName": "/aws/codebuild/bedrock-agentcore-candidate_matcher-builder",
  "streamName": "ae66df1f-5021-48cd-98e0-705f8ce02897",
  "deepLink": "https://console.aws.amazon.com/cloudwatch/..."
}
```

### Step 5: Leggere i Log da CloudWatch

```powershell
# Leggere gli ultimi 30 eventi
aws logs get-log-events `
    --log-group-name "/aws/codebuild/bedrock-agentcore-candidate_matcher-builder" `
    --log-stream-name "ae66df1f-5021-48cd-98e0-705f8ce02897" `
    --region us-east-1 `
    --query 'events[-30:].message' `
    --output text
```

## Script Automatico di Debug

Crea un file `debug_build.ps1`:

```powershell
param(
    [string]$ProjectName = "bedrock-agentcore-candidate_matcher-builder",
    [string]$Region = "us-east-1"
)

Write-Host "🔍 Debugging CodeBuild" -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Yellow

# Ottenere l'ultimo build ID
$buildId = aws codebuild list-builds-for-project `
    --project-name $ProjectName `
    --region $Region `
    --query 'ids[0]' `
    --output text

if ($buildId -eq "None") {
    Write-Host "❌ Nessun build trovato" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build ID: $buildId" -ForegroundColor Green

# Ottenere lo stato del build
$buildInfo = aws codebuild batch-get-builds `
    --ids $buildId `
    --region $Region `
    --query 'builds[0]'  `
    --output json | ConvertFrom-Json

Write-Host ""
Write-Host "📊 Status: $($buildInfo.buildStatus)" -ForegroundColor $(
    if ($buildInfo.buildStatus -eq 'SUCCEEDED') { 'Green' } else { 'Red' }
)

# Mostrare le fasi
Write-Host ""
Write-Host "🔄 Fasi del Build:" -ForegroundColor Cyan
foreach ($phase in $buildInfo.phases) {
    $color = if ($phase.phaseStatus -eq 'SUCCEEDED') { 'Green' } 
             elseif ($phase.phaseStatus -eq 'FAILED') { 'Red' }
             else { 'Yellow' }
    Write-Host "  $($phase.phaseType): $($phase.phaseStatus)" -ForegroundColor $color
}

# Ottenere i log
$logs = $buildInfo.logs
Write-Host ""
Write-Host "📝 Leggendo i log da CloudWatch..." -ForegroundColor Cyan

$logEvents = aws logs get-log-events `
    --log-group-name $logs.cloudWatchLogs.groupName `
    --log-stream-name $logs.cloudWatchLogs.streamName `
    --region $Region `
    --query 'events[].message' `
    --output json | ConvertFrom-Json

# Cercare errori
Write-Host ""
Write-Host "⚠️ Errori Trovati:" -ForegroundColor Red
$errors = $logEvents | Where-Object {
    $_ -match "(ERROR|error|FAILED|failed|Error|exception|Exception)"
}

if ($errors.Count -eq 0) {
    Write-Host "  Nessun errore trovato nei log" -ForegroundColor Green
} else {
    foreach ($error in $errors) {
        Write-Host "  $error"
    }
}

# Link al CloudWatch console
Write-Host ""
Write-Host "🌐 Link al CloudWatch Logs:" -ForegroundColor Cyan
Write-Host $logs.deepLink

Write-Host ""
Write-Host "📋 Ultimi 50 log eventi:" -ForegroundColor Cyan
$logEvents | Select-Object -Last 50 | ForEach-Object { Write-Host "  $_" }
```

Uso:
```powershell
.\debug_build.ps1 -ProjectName bedrock-agentcore-candidate_matcher-builder
```

## Errori Comuni e Soluzioni

### ❌ 1. "An image does not exist locally" + Docker Push Failed

**Sintomo:**
```
An image does not exist locally with the tag: 879338784410.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore-candidate_matcher
docker push failed with exit status 1
```

**Causa:** Il BUILD phase è fallito (il Dockerfile non è stato buildato correttamente)

**Soluzione:** Cerca l'errore vero nei log del BUILD phase (prima del POST_BUILD)

### ❌ 2. Errori di pip install

**Sintomo:**
```
ModuleNotFoundError: No module named 'strands'
```

**Causa:** I package in `requirements.txt` non sono corretti o non esistono

**Soluzione:** Confronta con un agente funzionante:
```bash
# Agente funzionante
cat agents/needs-reader/requirements.txt

# Il tuo agente
cat agents/candidate-matcher/requirements.txt
```

Usa versioni specifiche:
```txt
strands-agents==1.19.0
strands-agents-tools==0.2.17
bedrock-agentcore==1.1.1
boto3>=1.42.7
requests>=2.31.0
mcp>=1.0.0
```

### ❌ 3. Errori di import in agent.py

**Sintomo:**
```
ImportError: cannot import name 'BedrockAgentCoreApp' from 'bedrock_agentcore'
```

**Causa:** Import sbagliato o versione incompatibile

**Soluzione:** Controlla gli import da un agente funzionante:
```bash
grep -n "^from\|^import" agents/needs-reader/agent.py
```

### ❌ 4. Errori di Docker build

**Sintomo:**
```
failed to solve with frontend dockerfile.v0: failed to create LLB definition: ...
```

**Causa:** Dockerfile ha sintassi errata

**Soluzione:** Valida il Dockerfile localmente:
```bash
docker build -f agents/candidate-matcher/Dockerfile .
```

### ❌ 5. ECR Repository non trovato

**Sintomo:**
```
Error response from daemon: manifest not found: repository does not exist or may require 'docker login'
```

**Causa:** ECR repo non esiste o IAM role non ha permessi

**Soluzione:**
```powershell
# Verificare che il repo esista
aws ecr describe-repositories `
    --repository-names bedrock-agentcore-candidate_matcher `
    --region us-east-1

# Creare il repo se non esiste
aws ecr create-repository `
    --repository-name bedrock-agentcore-candidate_matcher `
    --region us-east-1
```

## Script di Validazione Pre-Deployment

Crea `validate_agent.ps1`:

```powershell
param(
    [string]$AgentPath
)

Write-Host "✅ Validazione Agente: $AgentPath" -ForegroundColor Cyan

# 1. Verificare che i file essenziali esistono
Write-Host ""
Write-Host "📁 Verificando file essenziali..." -ForegroundColor Yellow

$requiredFiles = @(
    "agent.py",
    "requirements.txt",
    "Dockerfile",
    ".dockerignore",
    ".bedrock_agentcore.yaml"
)

foreach ($file in $requiredFiles) {
    $path = Join-Path $AgentPath $file
    if (Test-Path $path) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file MANCANTE" -ForegroundColor Red
    }
}

# 2. Validare Python
Write-Host ""
Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow

$reqPath = Join-Path $AgentPath "requirements.txt"
$content = Get-Content $reqPath
if ($content -match "strands-agents==") {
    Write-Host "  ✅ strands-agents con versione" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ strands-agents potrebbe non avere versione specifica" -ForegroundColor Yellow
}

if ($content -match "bedrock-agentcore==") {
    Write-Host "  ✅ bedrock-agentcore con versione" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ bedrock-agentcore potrebbe non avere versione specifica" -ForegroundColor Yellow
}

# 3. Validare Dockerfile
Write-Host ""
Write-Host "🐳 Verificando Dockerfile..." -ForegroundColor Yellow

$dockerPath = Join-Path $AgentPath "Dockerfile"
$docker = Get-Content $dockerPath

if ($docker -match "FROM.*amazonlinux") {
    Write-Host "  ✅ Base image corretto" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Base image potrebbe essere sbagliato" -ForegroundColor Yellow
}

if ($docker -match "python3.11") {
    Write-Host "  ✅ Python 3.11 specificato" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Python version non chiarato" -ForegroundColor Yellow
}

if ($docker -match "EXPOSE 8080") {
    Write-Host "  ✅ Porta 8080 esposta" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Porta non esposta" -ForegroundColor Yellow
}

# 4. Sintassi Python
Write-Host ""
Write-Host "🐍 Verificando sintassi Python..." -ForegroundColor Yellow

$agentPath = Join-Path $AgentPath "agent.py"
$pythonCheck = python -m py_compile $agentPath 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Sintassi Python corretta" -ForegroundColor Green
} else {
    Write-Host "  ❌ Errore di sintassi:" -ForegroundColor Red
    Write-Host $pythonCheck -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Validazione completata!" -ForegroundColor Green
```

Uso:
```powershell
.\validate_agent.ps1 -AgentPath "agents/candidate-matcher"
```

## Workflow Completo di Debug

1. **Avvia il deployment**
   ```powershell
   cd agents/candidate-matcher
   agentcore launch
   ```

2. **Se fallisce, copia il project name** da `.bedrock_agentcore.yaml`

3. **Esegui lo script di debug**
   ```powershell
   .\debug_build.ps1 -ProjectName bedrock-agentcore-candidate_matcher-builder
   ```

4. **Analizza gli errori** dalla sezione "⚠️ Errori Trovati"

5. **Correggi il problema**
   - Se è `requirements.txt`: aggiorna le versioni
   - Se è `Dockerfile`: valida localmente con `docker build`
   - Se è `agent.py`: correggi gli import

6. **Valida prima di ritentare**
   ```powershell
   .\validate_agent.ps1 -AgentPath "agents/candidate-matcher"
   ```

7. **Ritenta il deployment**
   ```powershell
   agentcore launch
   ```

## Comandi Utili

### Visualizzare tutti i build di un progetto
```powershell
aws codebuild list-builds-for-project `
    --project-name bedrock-agentcore-candidate_matcher-builder `
    --region us-east-1 `
    --query 'ids[*]' `
    --output text
```

### Eliminare un log group per pulire
```powershell
aws logs delete-log-group `
    --log-group-name "/aws/codebuild/bedrock-agentcore-candidate_matcher-builder" `
    --region us-east-1
```

### Visualizzare l'ultimo log senza offset
```powershell
aws logs tail /aws/codebuild/bedrock-agentcore-candidate_matcher-builder `
    --follow `
    --region us-east-1
```

### Comparare requirements.txt tra agenti
```powershell
Write-Host "Needs Reader:" -ForegroundColor Cyan
Get-Content agents/needs-reader/requirements.txt

Write-Host ""
Write-Host "Candidate Matcher:" -ForegroundColor Cyan
Get-Content agents/candidate-matcher/requirements.txt
```

## Best Practices

1. **Sempre valida prima di deployare**
   ```powershell
   .\validate_agent.ps1 -AgentPath "agents/candidate-matcher"
   ```

2. **Testa localmente il Docker build**
   ```bash
   docker build -t test-agent agents/candidate-matcher/
   ```

3. **Confronta con agenti funzionanti**
   - requirements.txt
   - Dockerfile
   - agent.py (imports)

4. **Controlla i log CloudWatch in tempo reale**
   - Usa il link fornito da agentcore launch
   - O usa `aws logs tail`

5. **Mantieni note sui fallimenti**
   - Quale fase è fallita?
   - Qual era l'errore esatto?
   - Come l'hai risolto?

## Risoluzione Rapida

Se il build fallisce durante POST_BUILD (docker push), l'errore vero è nella fase BUILD.
Scorri indietro nei log di CloudWatch e cerca:
- `#1 [builder ...]` - fase di build
- `Error`, `ERROR`, `error` - parole chiave di errore
- `ImportError`, `ModuleNotFoundError` - errori di import

Di solito il problema è in `requirements.txt` (versioni sbagliate) o in `agent.py` (import sbagliati).
