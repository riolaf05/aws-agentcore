# Agent Invoke API

Questa guida descrive la Lambda e l’API Gateway per invocare un AgentCore runtime (es. `candidate-matcher`) tramite una POST autenticata con `x-api-key`.

## ✅ Cosa è stato aggiunto

- **Lambda** `PersonalAssistant-AgentInvoke` che invoca Bedrock AgentCore Runtime.
- **API Gateway** REST con endpoint `POST /invoke`.
- **API key obbligatoria** via header `x-api-key`.
- **Variabili runtime** impostate via script PowerShell locale (non committate).

## 🧩 Variabili d’ambiente

La Lambda legge:

- `AGENT_RUNTIME_ARN` → ARN dell’agente runtime da invocare.
- `AGENT_INVOKE_API_KEY` → chiave API richiesta da API Gateway.
- `ENABLE_AGENT_INVOKE_API` → abilita/disabilita API (`true`/`false`).

## ▶️ Script PowerShell (locale)

Usa lo script locale per esportare le variabili nella shell:

- [scripts/set-agent-invoke-env.ps1](../scripts/set-agent-invoke-env.ps1)

Lo script è in `.gitignore`.

## 🔐 API Key

L’API richiede header:

- `x-api-key: <valore>`

Il valore attuale è impostato nello script e viene stampato come esempio di chiamata.

## 📡 Test rapido (curl)

Lo script stampa una curl pronta, ma puoi usare anche questa:

```powershell
curl.exe -X POST "https://b1r5dxxzok.execute-api.us-east-1.amazonaws.com/prod/invoke" `
  -H "Content-Type: application/json" `
  -H "x-api-key: <API_KEY>" `
  --data-raw '{"text":"Cerca una posizione lavorativa per un professionista senior in ambito digital e product con 10+ anni di esperienza, analytics, A/B testing, eCommerce, SEO, paid media, project/backlog management e KPI dashboarding."}'
```

Esempio payload:

```json
{
  "text": "Cerca una posizione lavorativa per un professionista senior in ambito digital e product con 10+ anni di esperienza..."
}
```

## ℹ️ Informazioni aggiuntive richieste dall’AI

Per completare il matching, l’agente richiede **almeno** il ruolo attuale, ad esempio:

- **Ruolo attuale** (obbligatorio): "Senior Digital Product Manager", "Digital Platform Manager", "Senior Product Analyst", ecc.

Opzionali (migliorano il matching):

- **Provincia** (es: MI, RM, TO)
- **Lingue** con livello (es: Inglese B2)
- **Nome/Cognome** (facoltativi, per personalizzare)

## 🔄 Deploy CDK

Esempio:

```powershell
cd infrastructure/cdk-app
cdk deploy
```

## 🔧 Disattivare/Riattivare l’API

- Imposta `ENABLE_AGENT_INVOKE_API=false` (via script o env) e rilancia `cdk deploy`.
- Per riattivare: `ENABLE_AGENT_INVOKE_API=true`.

## ℹ️ Output CDK

Output utile:

- `AgentInvokeApiUrl` → URL completo per la POST.
- `AgentInvokeLambdaArn` → ARN della Lambda.
