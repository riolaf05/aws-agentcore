from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent()

# Configurazione gateway (credenziali dal TaskAPIGateway)
CLIENT_ID = "40ipvfb7kr5hnjqm06555e5hlp"
CLIENT_SECRET = "6rtmm58udin800qd6eiufv8top19q615m57etqha4fn9opmbi3f"
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

system_prompt = """
    Sei un assistente AI specializzato nella ricerca di opportunità professionali e esigenze aziendali.
    Il tuo compito è:
    1. Utilizzare il tool dedicato per cercare, leggere e analizzare "needs" (esigenze) nel database
    2. Fornire informazioni dettagliate su ruoli, competenze richieste, location e aziende
    3. Aiutare gli utenti a trovare le opportunità che meglio corrispondono ai loro criteri di ricerca
    
    Puoi effettuare le seguenti operazioni:
    - Elencare tutti i need disponibili
    - Cercare need per ID specifico
    - Cercare need per parola chiave (titolo, descrizione, ruolo, azienda, città)
    
    Sii preciso e utile nelle tue risposte, fornendo sempre i dettagli più rilevanti.
    """

def fetch_access_token(client_id, client_secret, token_url):
    response = requests.post(
        token_url,
        data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.json()['access_token']

def _invoke_agent(bedrock_model, mcp_client, prompt):
    """Invoca l'agente con il prompt fornito"""
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=tools
        )
        return agent(prompt)

def _create_streamable_http_transport(headers=None):
    """Crea il transport HTTP autenticato per il gateway MCP"""
    url = GATEWAY_URL
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    auth_headers = headers.copy() if headers else {}
    auth_headers["Authorization"] = f"Bearer {access_token}"
    return streamablehttp_client(url, headers=auth_headers)

def _get_bedrock_model(model_id):
    """Crea un'istanza del modello Bedrock"""
    return BedrockModel(
        model_id=model_id,
        temperature=0.7,   
        streaming=True,
    )

@app.entrypoint
def invoke(payload):
    """Punto di ingresso dell'agente"""
    mcp_client = MCPClient(_create_streamable_http_transport)

    user_message = payload.get("prompt", "Cosa puoi aiutarmi a trovare?")
    response = _invoke_agent(
        bedrock_model=_get_bedrock_model("us.anthropic.claude-sonnet-4-20250514-v1:0"),
        mcp_client=mcp_client,
        prompt=user_message
    )
    return response

if __name__ == "__main__":
    app.run()
