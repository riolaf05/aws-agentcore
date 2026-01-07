# WebSocket Client Node.js - Connessione ad AgentCore Runtime

## Parametri dell'Agente

```javascript
const AGENT_CONFIG = {
  agentId: "websocket_agent-56173zBzI2",
  agentArn: "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/websocket_agent-56173zBzI2",
  region: "us-east-1",
  accountId: "879338784410"
};
```

## Setup Node.js

```bash
npm install @aws-sdk/client-bedrock-agent-runtime
npm install ws
```

## Implementazione Client WebSocket

```javascript
const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agent-runtime");
const crypto = require('crypto');

// Configurazione client AWS
const client = new BedrockAgentRuntimeClient({ 
  region: "us-east-1"
});

// Funzione per invocare l'agente con streaming
async function invokeAgentWithStreaming(prompt, sessionId = null) {
  // Genera session ID se non fornito
  if (!sessionId) {
    sessionId = crypto.randomUUID();
  }

  const params = {
    agentId: "websocket_agent-56173zBzI2",
    agentAliasId: "TSTALIASID", // Usa l'alias del tuo agente
    sessionId: sessionId,
    inputText: prompt
  };

  try {
    console.log(`📡 Invocazione agente con session: ${sessionId}`);
    console.log(`💬 Prompt: ${prompt}\n`);
    
    const command = new InvokeAgentCommand(params);
    const response = await client.send(command);

    // Processa gli eventi in streaming
    console.log("🔄 Streaming risposta:\n");
    
    for await (const event of response.completion) {
      if (event.chunk) {
        const chunk = event.chunk.bytes;
        const text = new TextDecoder().decode(chunk);
        process.stdout.write(text); // Stampa in tempo reale
      }
    }
    
    console.log("\n\n✅ Streaming completato");
    return sessionId;
    
  } catch (error) {
    console.error("❌ Errore:", error);
    throw error;
  }
}

// Esempio di utilizzo
async function main() {
  try {
    // Prima invocazione
    const sessionId = await invokeAgentWithStreaming(
      "Ciao! Come stai?"
    );
    
    // Seconda invocazione nella stessa sessione
    await new Promise(resolve => setTimeout(resolve, 1000));
    await invokeAgentWithStreaming(
      "Mostrami i task aperti",
      sessionId
    );
    
  } catch (error) {
    console.error("Errore nel main:", error);
  }
}

main();
```

## Test Rapido

```javascript
// test-websocket.js
const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agent-runtime");

const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });

async function quickTest() {
  const response = await client.send(new InvokeAgentCommand({
    agentId: "websocket_agent-56173zBzI2",
    agentAliasId: "TSTALIASID",
    sessionId: "test-" + Date.now(),
    inputText: "Ciao!"
  }));

  for await (const event of response.completion) {
    if (event.chunk?.bytes) {
      process.stdout.write(new TextDecoder().decode(event.chunk.bytes));
    }
  }
}

quickTest();
```

## Esecuzione

```bash
node test-websocket.js
```

## Note Importanti

1. **WebSocket Automatico**: AgentCore Runtime gestisce automaticamente la connessione WebSocket. Non serve implementare un WebSocket client diretto.

2. **Streaming**: L'implementazione con `async def` e `yield event` nell'agente Python garantisce lo streaming automatico degli eventi.

3. **Session Management**: Usa lo stesso `sessionId` per mantenere il contesto della conversazione.

4. **Credenziali AWS**: Assicurati che le credenziali AWS siano configurate (`aws configure` o variabili d'ambiente).

5. **Alias**: Verifica l'alias dell'agente con:
   ```bash
   agentcore status --agent websocket_agent
   ```

## Eventi Disponibili

Lo stream può contenere diversi tipi di eventi:
- `chunk`: Pezzi di testo della risposta
- `trace`: Informazioni di debug (opzionale)
- `returnControl`: Richieste di input (per agenti interattivi)

## Gestione Errori

```javascript
try {
  await invokeAgentWithStreaming(prompt);
} catch (error) {
  if (error.name === 'ResourceNotFoundException') {
    console.error("Agente non trovato");
  } else if (error.name === 'ThrottlingException') {
    console.error("Troppi requests, attendi e riprova");
  } else {
    console.error("Errore:", error.message);
  }
}
```
