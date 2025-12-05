#!/usr/bin/env pwsh
# Script per testare i componenti della suite

param(
    [string]$Component = "all"
)

Write-Host "🧪 Personal Assistant Suite - Test Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Load .env
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1]
            $value = $matches[2]
            [System.Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

function Test-TaskAPI {
    Write-Host "🔍 Testing Task API..." -ForegroundColor Yellow
    
    # Get stack outputs
    Push-Location infrastructure/cdk-app
    $outputs = cdk output PersonalAssistantStack --json 2>$null | ConvertFrom-Json
    Pop-Location
    
    $endpoint = $outputs.TaskApiEndpoint
    
    if (-not $endpoint) {
        Write-Host "✗ Could not get API endpoint. Is stack deployed?" -ForegroundColor Red
        return
    }
    
    Write-Host "  Endpoint: $endpoint" -ForegroundColor Cyan
    
    # Test POST
    Write-Host "  Testing POST /tasks..." -ForegroundColor Cyan
    $body = @{
        tasks = @(
            @{
                title = "Test Task $(Get-Date -Format 'HH:mm:ss')"
                description = "Automated test task"
                priority = "high"
                category = "test"
                due_date = (Get-Date).AddDays(7).ToString("yyyy-MM-dd")
            }
        )
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$endpoint/tasks" -Method Post -Body $body -ContentType "application/json"
        Write-Host "  ✓ POST successful. Created $($response.created_count) tasks" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ POST failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test GET
    Write-Host "  Testing GET /tasks..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "$endpoint/tasks?limit=5" -Method Get
        Write-Host "  ✓ GET successful. Found $($response.count) tasks" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ GET failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

function Test-MCPServer {
    Write-Host "🔍 Testing MCP Server..." -ForegroundColor Yellow
    
    $mcpUrl = $env:MCP_SERVER_URL
    if (-not $mcpUrl) {
        $mcpUrl = "http://localhost:8000"
    }
    
    Write-Host "  URL: $mcpUrl" -ForegroundColor Cyan
    
    # Test health
    Write-Host "  Testing /health..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "$mcpUrl/health" -Method Get
        Write-Host "  ✓ Health check passed: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Health check failed. Is server running?" -ForegroundColor Red
        Write-Host "    Start with: cd mcp-server && python server.py" -ForegroundColor Gray
        return
    }
    
    # Test tools list
    Write-Host "  Testing /tools..." -ForegroundColor Cyan
    try {
        $headers = @{
            Authorization = "Bearer $env:MCP_API_KEY"
        }
        $response = Invoke-RestMethod -Uri "$mcpUrl/tools" -Method Get -Headers $headers
        Write-Host "  ✓ Tools endpoint: $($response.tools.Count) tools available" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Tools endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

function Test-TelegramBot {
    Write-Host "🔍 Testing Telegram Bot..." -ForegroundColor Yellow
    
    $token = $env:TELEGRAM_BOT_TOKEN
    if (-not $token) {
        Write-Host "  ✗ TELEGRAM_BOT_TOKEN not set" -ForegroundColor Red
        return
    }
    
    # Get bot info
    Write-Host "  Getting bot info..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getMe" -Method Get
        Write-Host "  ✓ Bot: @$($response.result.username)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Invalid bot token" -ForegroundColor Red
        return
    }
    
    # Check webhook
    Write-Host "  Checking webhook..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getWebhookInfo" -Method Get
        if ($response.result.url) {
            Write-Host "  ✓ Webhook configured: $($response.result.url)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠  No webhook configured" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Failed to check webhook" -ForegroundColor Red
    }
    
    Write-Host ""
}

function Test-Lambdas {
    Write-Host "🔍 Testing Lambda Functions..." -ForegroundColor Yellow
    
    $lambdas = @(
        "PersonalAssistant-TaskPost",
        "PersonalAssistant-TaskGet",
        "PersonalAssistant-Orchestrator",
        "PersonalAssistant-TaskManager",
        "PersonalAssistant-DailyBriefing",
        "PersonalAssistant-TelegramWebhook"
    )
    
    foreach ($lambda in $lambdas) {
        Write-Host "  Checking $lambda..." -ForegroundColor Cyan
        try {
            $config = aws lambda get-function-configuration --function-name $lambda 2>&1 | ConvertFrom-Json
            Write-Host "  ✓ $lambda exists (state: $($config.State))" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ $lambda not found or error" -ForegroundColor Red
        }
    }
    
    Write-Host ""
}

function Test-DynamoDB {
    Write-Host "🔍 Testing DynamoDB..." -ForegroundColor Yellow
    
    $tableName = "PersonalTasks"
    
    Write-Host "  Checking table $tableName..." -ForegroundColor Cyan
    try {
        $table = aws dynamodb describe-table --table-name $tableName 2>&1 | ConvertFrom-Json
        Write-Host "  ✓ Table exists (status: $($table.Table.TableStatus))" -ForegroundColor Green
        Write-Host "    Items: checking..." -ForegroundColor Cyan
        
        $scan = aws dynamodb scan --table-name $tableName --select COUNT 2>&1 | ConvertFrom-Json
        Write-Host "  ✓ Item count: $($scan.Count)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Table not found or error" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Run tests based on component parameter
switch ($Component.ToLower()) {
    "api" { Test-TaskAPI }
    "mcp" { Test-MCPServer }
    "telegram" { Test-TelegramBot }
    "lambda" { Test-Lambdas }
    "dynamodb" { Test-DynamoDB }
    "all" {
        Test-DynamoDB
        Test-Lambdas
        Test-TaskAPI
        Test-MCPServer
        Test-TelegramBot
    }
    default {
        Write-Host "Unknown component: $Component" -ForegroundColor Red
        Write-Host "Usage: .\test.ps1 [-Component <api|mcp|telegram|lambda|dynamodb|all>]" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "✅ Tests complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "  - To test specific component: .\test.ps1 -Component api" -ForegroundColor White
Write-Host "  - Check CloudWatch logs for detailed errors" -ForegroundColor White
Write-Host "  - See docs/troubleshooting.md for common issues" -ForegroundColor White
Write-Host ""
