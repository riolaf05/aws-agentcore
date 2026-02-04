import json
import uuid
import boto3

# Invoca project-goal-writer-reader per identificare l'obiettivo dal testo
agent_arn = "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/project_goal_writer_reader-61UCrz38Qt"
prompt = """Analizza il seguente testo e identifica il nome dell'obiettivo principale menzionato.
Rispondi SOLO con il nome dell'obiettivo come stringa semplice, senza spiegazioni.
Se non trovi nessun obiettivo, rispondi solo con la parola "vuoto".

Testo:
ciao, questo è un aggiornamento su ars alimentaria"""

# Initialize the Amazon Bedrock AgentCore client
agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Prepare the payload
payload = json.dumps({"prompt": prompt}).encode()

# Invoke the agent
response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=str(uuid.uuid4()),
    payload=payload,
    qualifier="DEFAULT"
)

content = []
for chunk in response.get("response", []):
    content.append(chunk.decode('utf-8'))
result = ''.join(content)
print("Raw response:")
print(result)
print("\nParsed:")
try:
    parsed = json.loads(result)
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
except:
    print(result)