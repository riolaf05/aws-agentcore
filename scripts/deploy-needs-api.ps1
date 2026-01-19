# Deploy Needs API Agent Script
# Questo script configura l'agente needs-reader per usare la Lambda existente

param(
    [Parameter(Mandatory=$false)]
    [string]$AccountId = (aws sts get-caller-identity --query Account --output text),
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$LambdaName = "mg-matchguru-needs-search-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$GatewayName = "matchguru-gateway"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🚀 Needs API Agent Configuration" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lambda: $LambdaName (ARN: arn:aws:lambda:$Region`:$AccountId`:function:$LambdaName)" -ForegroundColor Yellow
Write-Host ""

# Verifica che AWS CLI sia installato
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI non trovato. Installa AWS CLI prima di continuare." -ForegroundColor Red
    exit 1
}

# Verifica che agentcore CLI sia installato
if (-not (Get-Command agentcore -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AgentCore CLI non trovato. Esegui: pip install bedrock-agentcore-starter-toolkit" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisiti verificati" -ForegroundColor Green
Write-Host ""

# Step 1: Verificare la Lambda
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "⚡ Step 1: Verifica Lambda" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow

try {
    $LambdaInfo = aws lambda get-function --function-name $LambdaName --region $Region 2>$null | ConvertFrom-Json
    Write-Host "✅ Lambda trovata: $LambdaName" -ForegroundColor Green
    Write-Host "   Runtime: $($LambdaInfo.Configuration.Runtime)"
    Write-Host "   Handler: $($LambdaInfo.Configuration.Handler)"
    Write-Host "   Memory: $($LambdaInfo.Configuration.MemorySize) MB"
}
catch {
    Write-Host "❌ Lambda non trovata: $LambdaName" -ForegroundColor Red
    Write-Host "Assicurati che la Lambda sia deployata nella regione $Region" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 2: Verificare/Creare il Gateway
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "🌐 Step 2: Gateway MCP" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow

$GatewayList = aws bedrock-agentcore list-mcp-gateways --region $Region 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue

$Gateway = $null
if ($GatewayList) {
    $Gateway = $GatewayList.Gateways | Where-Object { $_.Name -eq $GatewayName } | Select-Object -First 1
}

if ($Gateway) {
    Write-Host "✅ Gateway trovato: $($Gateway.Name)" -ForegroundColor Green
    Write-Host "   Status: $($Gateway.Status)"
    Write-Host "   ARN: $($Gateway.GatewayArn)"
    $GatewayArn = $Gateway.GatewayArn
}
else {
    Write-Host "⚠️  Gateway non trovato. Creazione..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Esegui il seguente comando:" -ForegroundColor Cyan
    Write-Host "  agentcore gateway create-mcp-gateway --name $GatewayName --region $Region" -ForegroundColor White
    Write-Host ""
    Write-Host "E salva i valori Cognito dal risultato." -ForegroundColor Yellow
    
    $Continue = Read-Host "Continua comunque? (s/n)"
    if ($Continue -ne "s") {
        exit 0
    }
}

Write-Host ""

# Step 3: Aggiornare l'agente
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "🤖 Step 3: Configurazione Agent" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow

$AgentFile = "agents\needs-reader\agent.py"

if (Test-Path $AgentFile) {
    Write-Host "✅ File agente trovato: $AgentFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Aggiorna le credenziali Cognito nel file agent.py:" -ForegroundColor Cyan
    Write-Host "  - GATEWAY_CLIENT_ID"
    Write-Host "  - GATEWAY_CLIENT_SECRET"
    Write-Host "  - GATEWAY_TOKEN_ENDPOINT"
    Write-Host "  - GATEWAY_MCP_URL"
    Write-Host ""
}

Write-Host ""

# Step 4: Configurare i Target Lambda
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "📋 Step 4: Gateway Targets" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "Esegui i seguenti comandi per aggiungere i target Lambda al gateway:" -ForegroundColor Cyan
Write-Host ""

$LambdaArn = "arn:aws:lambda:$Region`:$AccountId`:function:$LambdaName"

$Commands = @(
    "# Salva questi valori dal gateway:",
    "`$GATEWAY_ARN=`"arn:aws:bedrock-agentcore:$Region`:$AccountId`:mcp-gateway/gateway-xxx`"",
    "`$GATEWAY_URL=`"https://matchguru-gateway-xxx.gateway.bedrock-agentcore.$Region.amazonaws.com/mcp`"",
    "`$GATEWAY_ROLE_ARN=`"arn:aws:iam::$AccountId`:role/gateway-execution-role`"",
    "",
    "# Target 1: List all needs",
    "agentcore gateway create-mcp-gateway-target \",
    "    --gateway-arn `$GATEWAY_ARN \",
    "    --gateway-url `$GATEWAY_URL \",
    "    --role-arn `$GATEWAY_ROLE_ARN \",
    "    --name list_all_needs \",
    "    --target-type lambda \",
    "    --target-payload '{",
    "      `"arn`": `"$LambdaArn`",",
    "      `"tools`": [{",
    "        `"name`": `"list_all_needs`",",
    "        `"description`": `"List all available needs from MongoDB`",",
    "        `"inputSchema`": { `"type`": `"object`", `"properties`": {} }",
    "      }]",
    "    }' \",
    "    --region $Region",
    ""
)

foreach ($cmd in $Commands) {
    Write-Host $cmd -ForegroundColor White
}

Write-Host "Vedi docs/NEEDS_GATEWAY_DEPLOYMENT.md per i comandi completi" -ForegroundColor Yellow
Write-Host ""

# Step 5: Testing
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "✅ Testing" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "Testa la Lambda:" -ForegroundColor Cyan
Write-Host "  python scripts/test_needs_api.py" -ForegroundColor White
Write-Host ""
Write-Host "Testa l'agente:" -ForegroundColor Cyan
Write-Host "  cd agents/needs-reader" -ForegroundColor White
Write-Host "  python agent.py" -ForegroundColor White
Write-Host ""

Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Configuration Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
