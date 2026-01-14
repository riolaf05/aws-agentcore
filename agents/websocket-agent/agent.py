from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

CLIENT_ID = "40ipvfb7kr5hnjqm06555e5hlp"
CLIENT_SECRET = "6rtmm58udin800qd6eiufv8top19q615m57etqha4fn9opmbi3f"
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

system_prompt = """
You are a helpful AI assistant capable of answering questions and helping users with their requests.

Your capabilities:
- Answer user questions to the best of your ability using your knowledge
- Use the MCP gateway tools when you need to interact with external systems or APIs
- Distinguish between genuine questions/requests that need a response and casual conversation/greetings

Guidelines:
- For direct questions or action requests: Provide helpful, accurate responses
- For casual conversation or greetings (like "hi", "hello", "how are you"): Respond politely but briefly
- When you need to access external data or perform actions, use the available MCP gateway tools
- Be concise and helpful in your responses
"""

def fetch_access_token(client_id, client_secret, token_url):
    response = requests.post(
        token_url,
        data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.json()['access_token']

def _create_streamable_http_transport(headers=None):
    url = GATEWAY_URL
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    headers = {**headers} if headers else {}
    headers["Authorization"] = f"Bearer {access_token}"
    return streamablehttp_client(
        url,
        headers=headers
    )

def _get_bedrock_model(model_id):
    return BedrockModel(
        model_id=model_id,
        temperature=0.7,   
        streaming=True,
    )

@app.entrypoint
async def invoke(payload, context):
    """Agent entrypoint with WebSocket bi-directional streaming support"""
    mcp_client = MCPClient(_create_streamable_http_transport)

    user_message = payload.get("prompt", "Hello! How can I help you today?")
    
    print(f"Context: {context}")
    print(f"Processing message: {user_message}")
    
    # Create agent with streaming enabled
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=_get_bedrock_model("us.anthropic.claude-sonnet-4-20250514-v1:0"),
            system_prompt=system_prompt,
            tools=tools
        )
        
        # Stream agent responses using async generator
        agent_stream = agent.stream_async(user_message)
        
        async for event in agent_stream:
            yield event

if __name__ == "__main__":
    app.run()