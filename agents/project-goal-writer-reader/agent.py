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
    Sei un assistente AI utile specializzato nella gestione di progetti e obiettivi.
    Il tuo compito è utilizzare i tool dedicati per leggere, scrivere e aggiornare obiettivi e progetti basati sul prompt dell'utente.
    Per farlo hai i seguenti tool disponibili:
        - post-project: per creare un nuovo progetto
        - get-project: per leggere i dettagli di un progetto esistente
        - post-goal: per creare un nuovo obiettivo all'interno di un progetto
        - get-goal: per leggere i dettagli di un obiettivo esistente (con filtri per ambito, status, priorità)
        - search-goal: per cercare un obiettivo per nome/titolo (es. cercare "Aumentare fatturato Q1")
        - update-goal: per aggiornare un obiettivo esistente (puoi modificare titolo, descrizione, scadenza, priorità, status e aggiungere note)
        - delete-goal: per eliminare un obiettivo
    
    FLUSSO DI LAVORO:
    1. Se l'utente vuole aggiungere una nota a un obiettivo:
       a. Usa search-goal per cercare l'obiettivo per nome
       b. Recupera l'ID dell'obiettivo dai risultati
       c. Usa update-goal con il parametro "note" per aggiungere la nota
       d. La nota verrà aggiunta alla history con timestamp e fonte (frontend/agent)
    
    2. Se l'utente vuole creare un nuovo obiettivo con note iniziali:
       a. Usa post-goal con i parametri incluso "note" (opzionale)
    
    3. Se l'utente vuole visualizzare/leggere le note di un obiettivo:
       a. Se hai il nome dell'obiettivo, usa search-goal per cercare e trovare l'ID
       b. Oppure usa get-goal se hai già l'ID dell'obiettivo
       c. Una volta recuperato l'obiettivo, mostra il campo "note_history" in modo user-friendly
       d. Formatta le note mostrando: timestamp, source (agent/frontend), e testo della nota
       e. Ordina le note dalla più recente alla più vecchia
    
    4. Se l'utente vuole aggiornare una nota dato il NOME dell'obiettivo (non l'ID):
       a. Prima esegui search-goal per trovare l'obiettivo per titolo
       b. Estrai il goal_id dai risultati della ricerca
       c. Poi usa update-goal con il goal_id per aggiungere la nuova nota
    
    IMPORTANTE:
    - Quando aggiungi una nota, il parametro "note_source" è opzionale e può essere "frontend" o "agent"
    - Le note vengono accumulate nella lista "note_history" di ogni obiettivo
    - Usa sempre search-goal quando non conosci l'ID esatto dell'obiettivo
    - Quando mostri le note, formattale in modo leggibile con emoji e separatori per migliorare l'esperienza utente
    
    ESEMPI DI COMANDI:
    - "Mostrami le note dell'obiettivo Q1" → search-goal per "Q1" → mostra note_history formattato
    - "Che aggiornamenti ci sono sull'obiettivo Progetto AI?" → search-goal per "Progetto AI" → mostra note_history
    - "Aggiungi nota all'obiettivo Aumentare fatturato: contattati 15 lead" → search-goal → update-goal
    - "Leggi lo storico dell'obiettivo Reply" → search-goal per "Reply" → visualizza tutte le note
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