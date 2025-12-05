# Troubleshooting Guide

Soluzioni ai problemi comuni della Personal Assistant Suite.

## 🔴 Errori Bedrock Agents

### "Agent not found" o "InvalidAgentId"

**Causa:** Agent ID non configurato o errato.

**Soluzione:**
1. Verifica che gli agenti siano stati creati nella console Bedrock
2. Copia gli Agent ID dalla console
3. Aggiorna environment variables nelle Lambda:
   ```bash
   aws lambda update-function-configuration \
     --function-name PersonalAssistant-Orchestrator \
     --environment Variables={
       BEDROCK_AGENT_ID_TASK_MANAGER=<agent-id>,
       BEDROCK_AGENT_ID_DAILY_BRIEFING=<agent-id>
     }
   ```

### "AccessDeniedException" quando invoco agente

**Causa:** IAM permissions mancanti.

**Soluzione:**
Aggiungi policy alla Lambda role:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeAgent",
    "bedrock:Retrieve"
  ],
  "Resource": "*"
}
```

### Agent risponde lentamente

**Causa:** Timeout Lambda troppo basso o agent complex.

**Soluzione:**
1. Aumenta timeout Lambda (min 60s)
2. Ottimizza prompt dell'agente
3. Riduci complessità action groups

## 🔴 Errori Lambda

### "Task execution failed: DynamoDB access denied"

**Soluzione:**
```bash
# Verifica IAM role della Lambda
aws lambda get-function-configuration \
  --function-name PersonalAssistant-TaskPost

# Aggiorna permissions
# (CDK dovrebbe farlo automaticamente, ma verifica)
```

### "Lambda timeout" errori frequenti

**Soluzione:**
1. Aumenta timeout:
   ```typescript
   timeout: Duration.seconds(60)  // in CDK stack
   ```
2. Ottimizza codice Lambda (riduci chiamate API)
3. Usa Lambda layers per dipendenze pesanti

### "Unable to import module" errore

**Causa:** Dipendenze non packaged correttamente.

**Soluzione:**
```bash
cd lambdas/task-api

# Crea package
pip install -r requirements.txt -t ./package
cd package
zip -r ../deployment-package.zip .
cd ..
zip -g deployment-package.zip *.py

# Re-deploy
aws lambda update-function-code \
  --function-name PersonalAssistant-TaskPost \
  --zip-file fileb://deployment-package.zip
```

## 🔴 Errori DynamoDB

### "ValidationException: The table does not exist"

**Soluzione:**
```bash
# Verifica tabella
aws dynamodb describe-table --table-name PersonalTasks

# Se non esiste, re-deploy CDK stack
cd infrastructure/cdk-app
cdk deploy
```

### "ProvisionedThroughputExceededException"

**Causa:** Troppi request (non dovrebbe accadere con Pay-per-request).

**Soluzione:**
Verifica billing mode:
```bash
aws dynamodb describe-table --table-name PersonalTasks \
  --query 'Table.BillingModeSummary'
```

## 🔴 Errori Telegram

### Bot non risponde

**Checklist:**
1. ✓ Webhook configurato?
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   ```

2. ✓ Lambda riceve chiamate?
   ```bash
   aws logs tail /aws/lambda/PersonalAssistant-TelegramWebhook --follow
   ```

3. ✓ Chat ID autorizzato?
   Verifica `AUTHORIZED_USERS` env variable

4. ✓ Orchestrator Lambda invocabile?
   Test manuale:
   ```bash
   aws lambda invoke \
     --function-name PersonalAssistant-Orchestrator \
     --payload '{"body":"{\"message\":\"test\",\"user_id\":\"123\"}"}' \
     response.json
   ```

### "Webhook already set to a different URL"

**Soluzione:**
```bash
# Rimuovi webhook
curl -X POST https://api.telegram.org/bot<TOKEN>/deleteWebhook

# Imposta nuovo
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d "url=<NEW_WEBHOOK_URL>"
```

### "Unauthorized" errore

**Causa:** Bot token errato o scaduto.

**Soluzione:**
1. Verifica token su BotFather
2. Aggiorna secret in AWS Secrets Manager
3. Restart Lambda (deploy nuovo)

## 🔴 Errori MCP Server

### "Connection refused" quando agenti chiamano MCP

**Causa:** MCP server non raggiungibile.

**Soluzione:**
1. Se locale: verifica server running
   ```bash
   cd mcp-server
   python server.py
   ```

2. Se remoto: verifica URL e networking
   ```bash
   curl https://your-mcp-server.com/health
   ```

3. Verifica security groups (se su AWS)

### "Authentication failed" su Outlook API

**Checklist:**
1. ✓ Azure AD app configurata?
2. ✓ Client secret valido? (non scaduto)
3. ✓ Permessi API granted?
4. ✓ Tenant ID corretto?

**Test OAuth flow:**
```bash
curl -X POST "https://login.microsoftonline.com/<TENANT_ID>/oauth2/v2.0/token" \
  -d "client_id=<CLIENT_ID>" \
  -d "client_secret=<CLIENT_SECRET>" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "grant_type=client_credentials"
```

### "Invalid API key" su MCP server

**Soluzione:**
```bash
# Verifica API key
aws secretsmanager get-secret-value \
  --secret-id personal-assistant/mcp-api-key

# Aggiorna in Lambda env variables
aws lambda update-function-configuration \
  --function-name PersonalAssistant-DailyBriefing \
  --environment Variables={MCP_API_KEY=<new-key>}
```

## 🔴 Errori API Gateway

### "403 Forbidden" su API calls

**Causa:** CORS o authorization.

**Soluzione:**
1. Verifica CORS configurato nel CDK
2. Check API Gateway authorizers
3. Test diretto:
   ```bash
   curl -v https://api-id.execute-api.region.amazonaws.com/prod/tasks
   ```

### "502 Bad Gateway"

**Causa:** Lambda error o timeout.

**Soluzione:**
1. Check CloudWatch logs della Lambda
2. Verifica timeout settings
3. Test Lambda direttamente (bypass API Gateway)

## 🔴 Errori Costi Inaspettati

### Costi Bedrock più alti del previsto

**Analisi:**
```bash
# Check invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --start-time 2024-12-01T00:00:00Z \
  --end-time 2024-12-05T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

**Ottimizzazione:**
1. Riduci max_tokens nei prompt
2. Implementa caching risposte comuni
3. Limita invocazioni (rate limiting)

### DynamoDB costi elevati

**Soluzione:**
1. Verifica che sia Pay-per-request mode
2. Ottimizza query (usa GSI)
3. Implementa TTL per vecchi task

## 🔴 Problemi Performance

### Agenti troppo lenti

**Ottimizzazioni:**
1. **Prompt engineering:**
   - Prompt più concisi
   - Chiare istruzioni
   - Few-shot examples

2. **Lambda:**
   - Aumenta memory (→ più CPU)
   - Usa Lambda SnapStart
   - Warm-up con EventBridge

3. **Database:**
   - Query ottimizzate con GSI
   - Batch operations
   - Connection pooling

### Daily briefing timeout

**Soluzione:**
```python
# In agent.py, parallelizza chiamate
import asyncio

async def generate_briefing_async():
    tasks_future = asyncio.create_task(get_tasks())
    emails_future = asyncio.create_task(get_emails())
    
    tasks, emails = await asyncio.gather(tasks_future, emails_future)
    # ... rest of logic
```

## 📞 Ottenere Aiuto

Se il problema persiste:

1. **Check logs CloudWatch** per error details
2. **Enable debug logging:**
   ```bash
   aws lambda update-function-configuration \
     --function-name <function-name> \
     --environment Variables={LOG_LEVEL=DEBUG}
   ```

3. **Test componenti isolatamente:**
   - Lambda singole
   - Bedrock agents
   - MCP server
   - DynamoDB queries

4. **Consulta AWS Support** per problemi specifici AWS

5. **Community:**
   - AWS re:Post
   - Stack Overflow (tag: aws-bedrock, aws-cdk)

## 🐛 Debug Checklist

Quando qualcosa non funziona:

- [ ] CloudWatch Logs verificati
- [ ] Environment variables corrette
- [ ] IAM permissions adeguate
- [ ] Networking (security groups, VPC)
- [ ] Secrets aggiornati e accessibili
- [ ] API endpoints raggiungibili
- [ ] Quota AWS non superata
- [ ] Test componente isolato funziona
- [ ] Configurazione CDK synced con deploy

---

**Tip:** Abilita AWS X-Ray per distributed tracing e diagnosi avanzata.
