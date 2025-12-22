# Script per creare utenti in AWS Cognito User Pool
# Esegui questo script dopo il deploy CDK per creare il primo utente admin

param(
    [Parameter(Mandatory=$true)]
    [string]$UserPoolId,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$TemporaryPassword,
    
    [string]$Region = "us-east-1"
)

Write-Host "🔐 Creazione utente in Cognito User Pool..." -ForegroundColor Cyan
Write-Host "User Pool ID: $UserPoolId" -ForegroundColor Yellow
Write-Host "Username: $Username" -ForegroundColor Yellow
Write-Host "Email: $Email" -ForegroundColor Yellow

try {
    # Crea l'utente
    aws cognito-idp admin-create-user `
        --user-pool-id $UserPoolId `
        --username $Username `
        --user-attributes Name=email,Value=$Email Name=email_verified,Value=true `
        --temporary-password $TemporaryPassword `
        --message-action SUPPRESS `
        --region $Region

    Write-Host "✅ Utente creato con successo!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Credenziali:" -ForegroundColor Cyan
    Write-Host "   Username: $Username"
    Write-Host "   Password temporanea: $TemporaryPassword"
    Write-Host ""
    Write-Host "⚠️  Al primo login, l'utente dovrà cambiare la password." -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Errore nella creazione dell'utente: $_" -ForegroundColor Red
    exit 1
}
