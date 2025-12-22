# AWS Cognito Authentication Setup

Questa guida ti aiuta a configurare l'autenticazione AWS Cognito per il Personal Assistant.

## 📋 Step 1: Deploy CDK Stack con Cognito

```powershell
cd infrastructure/cdk-app
cdk deploy
```

Copia gli output del deploy:
- `UserPoolId` (es: `us-east-1_XXXXXXXXX`)
- `UserPoolClientId` (es: `XXXXXXXXXXXXXXXXXXXXXXXXXX`)
- `IdentityPoolId` (opzionale)

## 📋 Step 2: Aggiorna la Configurazione Frontend

Apri `chat-frontend/app.js` e aggiorna le costanti:

```javascript
const CONFIG = {
    // ... altri config
    COGNITO_USER_POOL_ID: 'us-east-1_XXXXXXXXX',  // <-- Incolla qui UserPoolId
    COGNITO_CLIENT_ID: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',  // <-- Incolla qui UserPoolClientId
    COGNITO_REGION: 'us-east-1'
};
```

## 📋 Step 3: Crea il Primo Utente Admin

Usa lo script PowerShell per creare un utente:

```powershell
# Esempio
.\scripts\create-cognito-user.ps1 `
    -UserPoolId "us-east-1_XXXXXXXXX" `
    -Username "admin" `
    -Email "admin@example.com" `
    -TemporaryPassword "TempPass123!"
```

Oppure usa AWS CLI direttamente:

```powershell
aws cognito-idp admin-create-user `
    --user-pool-id us-east-1_XXXXXXXXX `
    --username admin `
    --user-attributes Name=email,Value=admin@example.com Name=email_verified,Value=true `
    --temporary-password TempPass123! `
    --message-action SUPPRESS `
    --region us-east-1
```

## 📋 Step 4: Primo Login

1. Vai su `http://localhost:5000` (o l'URL del tuo frontend)
2. Login con:
   - **Username**: `admin`
   - **Password temporanea**: `TempPass123!`
3. Ti verrà chiesto di cambiare la password
4. Inserisci una nuova password sicura (min 8 caratteri, uppercase, lowercase, numeri)

## 🔐 Password Policy

Il User Pool ha le seguenti policy:
- Minimo 8 caratteri
- Almeno 1 lettera maiuscola
- Almeno 1 lettera minuscola
- Almeno 1 numero
- Simboli opzionali

## 👥 Creare Altri Utenti

Ripeti lo Step 3 per ogni nuovo utente, cambiando username ed email.

## 🔧 Gestione Utenti via Console AWS

1. Vai su AWS Console → Cognito
2. Seleziona il User Pool `PersonalAssistantUsers`
3. Nella sezione "Users" puoi:
   - Vedere tutti gli utenti
   - Disabilitare/abilitare utenti
   - Resettare password
   - Eliminare utenti

## 🔄 Reset Password Utente

Se un utente ha dimenticato la password:

```powershell
aws cognito-idp admin-set-user-password `
    --user-pool-id us-east-1_XXXXXXXXX `
    --username admin `
    --password "NewTempPass123!" `
    --permanent false `
    --region us-east-1
```

L'utente dovrà cambiarla al prossimo login.

## 🚨 Troubleshooting

### Errore "Cognito non configurato"
- Verifica di aver aggiornato `COGNITO_USER_POOL_ID` e `COGNITO_CLIENT_ID` in `app.js`
- Controlla che il CDK deploy sia completato con successo

### Errore "NotAuthorizedException"
- Username o password errati
- L'utente potrebbe essere disabilitato (controlla in AWS Console)

### Errore "UserNotFoundException"
- L'utente non esiste nel User Pool
- Crea l'utente con lo script dello Step 3

### Il primo login non funziona
- Assicurati di usare la password temporanea esatta
- Se chiesto, inserisci una password che rispetta la policy

## 📚 Risorse Aggiuntive

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Amazon Cognito Identity SDK for JavaScript](https://github.com/aws-amplify/amplify-js/tree/main/packages/amazon-cognito-identity-js)
