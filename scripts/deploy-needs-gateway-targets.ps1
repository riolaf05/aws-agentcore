# PowerShell script to deploy Needs API targets to TaskAPIGateway
# This script adds three Lambda tools to the TaskAPIGateway:
# 1. list_all_needs - List all available needs
# 2. search_needs_by_keyword - Search needs by keyword
# 3. get_need_by_id - Get specific need by ID

param(
    [string]$Region = "us-east-1"
)

# Configuration
$GatewayName = "TaskAPIGateway"
$GatewayArn = "arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus"
$GatewayUrl = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
$ExecutionRoleArn = "arn:aws:iam::879338784410:role/AgentCoreGatewayExecutionRole"

$TargetDefinitions = @(
    @{
        "name" = "list_all_needs"
        "description" = "List all available needs from MongoDB database"
        "payloadFile" = "gateway-target-list-needs.json"
    },
    @{
        "name" = "search_needs_by_keyword"
        "description" = "Search for needs by keyword across multiple fields"
        "payloadFile" = "gateway-target-search-keyword.json"
    },
    @{
        "name" = "get_need_by_id"
        "description" = "Retrieve a specific need by its unique ID"
        "payloadFile" = "gateway-target-get-by-id.json"
    }
)

Write-Host "============================================"
Write-Host "Deploying Needs API Targets to Gateway"
Write-Host "============================================"
Write-Host "Gateway: $GatewayName"
Write-Host "Gateway ARN: $GatewayArn"
Write-Host "Region: $Region"
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Deploy each target
foreach ($target in $TargetDefinitions) {
    Write-Host "Deploying target: $($target.name)"
    Write-Host "Description: $($target.description)"
    
    $payloadPath = Join-Path $ScriptDir $target.payloadFile
    
    if (-not (Test-Path $payloadPath)) {
        Write-Host "ERROR: Payload file not found: $payloadPath" -ForegroundColor Red
        continue
    }
    
    # Read the payload
    $payload = Get-Content $payloadPath -Raw
    
    # Create the target using agentcore CLI
    try {
        Write-Host "  Creating target with payload from: $($target.payloadFile)"
        
        $output = agentcore gateway create-mcp-gateway-target `
            --gateway-arn $GatewayArn `
            --gateway-url $GatewayUrl `
            --role-arn $ExecutionRoleArn `
            --name $target.name `
            --target-type lambda `
            --target-payload $payload `
            --region $Region `
            2>&1
        
        Write-Host "  ✓ Target '$($target.name)' created successfully" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host "  ✗ Error creating target '$($target.name)': $_" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "============================================"
Write-Host "Deployment Complete"
Write-Host "============================================"
Write-Host ""
Write-Host "Verifying deployed targets..."
Write-Host ""

# List all targets
$targets = agentcore gateway list-mcp-gateway-targets `
    --gateway-arn $GatewayArn `
    --region $Region 2>&1

Write-Host "Active Targets:"
Write-Host $targets
