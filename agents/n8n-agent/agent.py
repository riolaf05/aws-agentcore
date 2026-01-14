from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent()

LOVABLE_AUTH_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4OGVmZTcxNC0xZDc4LTQwYTUtOWQ3NC1hMDYwZjIxZjQxMmMiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6IjRhZDc5Nzg4LTEzZDAtNGJhNC05MzIzLTYxOTE5YWRjMjAyZSIsImlhdCI6MTc2NTg5OTE0MH0.bl676ebrxFNVLNY2iBgyScBeh06GjHbeDTLi2_Jb9s8"
GATEWAY_URL = "https://riomg.app.n8n.cloud/mcp-server/http"

system_prompt = """
    Sei un assistente AI utile.
    Il tuo compito è connetterti ad un server MCP su n8n e utilizzare i tool dedicati per eseguire operazioni basate sul prompt dell'utente.
    Le operazioni che puoi eseguire includono: 
     - lettura di email da Gmail
     - lettura dell'ora e della data attuali
     - gestione di file su Google Drive
     - ricerca novità da pagine Instagram selezionate
    """

# def fetch_access_token(client_id, client_secret, token_url):
#     response = requests.post(
#         token_url,
#         data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
#         headers={'Content-Type': 'application/x-www-form-urlencoded'}
#     )
#     return response.json()['access_token']

def _invoke_agent(
    bedrock_model,
    mcp_client,
    prompt
):
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=tools
        )
        return agent(prompt)

def _create_streamable_http_transport(headers=None):
    url = GATEWAY_URL
    headers = {**headers} if headers else {}
    headers[""] = f"bearer {LOVABLE_AUTH_KEY}"
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
def invoke(payload):
    """Your AI agent function"""

    breakpoint()

    mcp_client = MCPClient(_create_streamable_http_transport)

    user_message = payload.get("prompt", "Hello! How can I help you today?")
    response = _invoke_agent(
        bedrock_model=_get_bedrock_model("us.anthropic.claude-sonnet-4-20250514-v1:0"),
        mcp_client=mcp_client,
        prompt=user_message
    )
    return response

if __name__ == "__main__":
    app.run()