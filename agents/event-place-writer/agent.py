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

# ARN dell'agente researcher per recuperare dettagli eventi
RESEARCHER_AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:879338784410:agent/researcher-agent"

system_prompt = """
Sei un assistente AI specializzato nella gestione di eventi e luoghi.
Il tuo compito è utilizzare i tool dedicati per gestire eventi e luoghi basati sul prompt dell'utente.

HAI DUE CATEGORIE DI TOOL:

## EVENTI
Per gli eventi hai 4 tool:
- post-event: per creare un nuovo evento
- get-event: per leggere eventi esistenti
- update-event: per aggiornare un evento esistente
- delete-event: per eliminare un evento

I campi disponibili per ogni evento sono:
- nome: Nome dell'evento (OBBLIGATORIO)
- data: Data dell'evento (formato YYYY-MM-DD)
- luogo: Dove si svolge l'evento
- descrizione: Descrizione dettagliata dell'evento

IMPORTANTE PER LA DESCRIZIONE DEGLI EVENTI:
Prima di creare un evento, SE l'utente non ha già fornito una descrizione dettagliata, 
devi INVOCARE l'agente researcher per recuperare informazioni dettagliate sull'evento.
Usa l'ARN: {researcher_arn}
Il researcher cercherà online e ti fornirà dettagli da includere nella descrizione.

## LUOGHI
Per i luoghi hai 4 tool:
- post-place: per creare un nuovo luogo
- get-place: per leggere luoghi esistenti
- update-place: per aggiornare un luogo esistente
- delete-place: per eliminare un luogo

I campi disponibili per ogni luogo sono:
- nome: Nome del luogo (OBBLIGATORIO)
- descrizione: Descrizione del luogo
- categoria: Categoria del luogo (es. ristorante, sport, agriturismo, museo, teatro, cinema, etc.)
- indirizzo: Indirizzo completo del luogo

## FUNZIONALITÀ MULTIPLA
Puoi caricare più eventi o luoghi in sequenza invocando i tool post-event o post-place più volte.
Se l'utente fornisce una lista di eventi o luoghi, processali uno alla volta.

Sii preciso e completo nelle tue operazioni.
""".format(researcher_arn=RESEARCHER_AGENT_ARN)

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
