const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agent-runtime");

const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });

async function quickTest() {
  const response = await client.send(new InvokeAgentCommand({
    agentId: "websocket_agent-56173zBzI2",
    agentAliasId: "56173zBzI2", // Alias reale dell'agente (modifica se hai un alias personalizzato)
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
