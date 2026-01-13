from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent()

CLIENT_ID = "40ipvfb7kr5hnjqm06555e5hlp"
CLIENT_SECRET = "6rtmm58udin800qd6eiufv8top19q615m57etqha4fn9opmbi3f"
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

system_prompt = """
Sei un assistente AI specializzato nella gestione dei contatti.
Il tuo compito è utilizzare i tool dedicati per leggere o scrivere contatti basati sul prompt dell'utente.
Per farlo hai 4 tool dedicati:
    - post-contact: per creare un nuovo contatto
    - get-contact: per leggere i dettagli di contatti esistenti
    - update-contact: per aggiornare un contatto esistente
    - delete-contact: per eliminare un contatto

I campi disponibili per ogni contatto sono (tutti opzionali):
- nome: Nome del contatto
- cognome: Cognome del contatto
- email: Indirizzo email
- telefono: Numero di telefono
- descrizione: Descrizione o ruolo (es. "CEO di TechCompany")
- tipo: Tipo di contatto - SEMPRE da includere se menzionato! (es. "investitore", "startupper", "fornitore", "imprenditore", "startup")
- dove_conosciuto: Dove/quando hai conosciuto la persona
- note: Note aggiuntive
- url: URL LinkedIn o altro profilo social

REGOLE CRITICHE:
1. Se l'utente menziona il tipo di contatto, DEVI SEMPRE includerlo nel campo "tipo"
2. Non ignorare mai il tipo anche se sono presenti altri campi
3. Esempi di tipi validi: "investitore", "imprenditore", "startup", "fornitore", "consulente", "partner", "cliente", "da seguire"

ESEMPI DI UTILIZZO:
- Utente: "Aggiungi Mario Rossi, investitore" → usa post-contact con nome="Mario", cognome="Rossi", tipo="investitore"
- Utente: "Crea contatto per Federico Colacicchi startupper" → usa post-contact con nome="Federico", cognome="Colacicchi", tipo="startupper"
- Utente: "Aggiorna Claudio a tipo imprenditore" → usa update-contact e INCLUDI tipo="imprenditore"
"""

def fetch_access_token(client_id, client_secret, token_url):
    response = requests.post(
        token_url,
        data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.json()['access_token']

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
def invoke(payload):
    """Your AI agent function"""
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