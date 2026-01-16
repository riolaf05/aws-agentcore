from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Gateway Configuration
CLIENT_ID = "40ipvfb7kr5hnjqm06555e5hlp"
CLIENT_SECRET = "6rtmm58udin800qd6eiufv8top19q615m57etqha4fn9opmbi3f"
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

system_prompt = """
Sei un assistente AI specializzato nel matching tra candidati e needs/posizioni lavorative.

Il tuo compito è:
1. Raccogliere informazioni sul candidato dall'utente
2. Utilizzare il tool 'find_matching_needs' per trovare i migliori 5 needs compatibili
3. Presentare i risultati in modo chiaro e strutturato

INFORMAZIONI RICHIESTE:
- **current_role** (OBBLIGATORIO): Ruolo attuale del candidato (es: "Senior Python Developer", "Data Scientist", "Project Manager")
- id: ID univoco del candidato (opzionale)
- name: Nome del candidato (opzionale)
- surname: Cognome del candidato (opzionale)
- years_experience: Anni totali di esperienza lavorativa (numero, opzionale)
- province: Provincia di residenza (es: "MI", "RM", "TO", opzionale)
- technologies: Array di tecnologie conosciute (es: [{"skill_name": "Python"}, {"skill_name": "AWS"}])
- hard_skills: Array di competenze tecniche (es: [{"skill_name": "Machine Learning"}, {"skill_name": "Docker"}])
- soft_skills: Array di competenze trasversali (es: [{"skill_name": "Leadership"}, {"skill_name": "Problem Solving"}])
- languages: Array di lingue con livello (es: [{"language": "Inglese", "proficiency": "C1"}, {"language": "Italiano", "proficiency": "Madrelingua"}])

FLUSSO CONVERSAZIONALE:
Se l'utente non fornisce tutte le informazioni necessarie:
1. Chiedi il ruolo attuale (obbligatorio)
2. Chiedi se vuole aggiungere altre informazioni (tecnologie, skills, lingue, anni esperienza, provincia)
3. Una volta raccolte le informazioni, usa il tool find_matching_needs
4. Presenta i risultati in modo chiaro con:
   - Titolo del need
   - Azienda
   - Località
   - Percentage di compatibilità
   - Motivo del match

Se l'utente fornisce già tutte le informazioni nel prompt iniziale, procedi direttamente con il matching.
"""

def fetch_access_token(client_id, client_secret, token_url):
    """Ottiene l'access token OAuth2 da Cognito"""
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.json()['access_token']

def _invoke_agent(bedrock_model, mcp_client, prompt):
    """Invoca l'agente con il modello Bedrock e il client MCP"""
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=tools
        )
        return agent(prompt)

def _create_streamable_http_transport(headers=None):
    """Crea il transport HTTP per l'MCP client con autenticazione"""
    url = GATEWAY_URL
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    headers = {**headers} if headers else {}
    headers["Authorization"] = f"Bearer {access_token}"
    return streamablehttp_client(url, headers=headers)

def _get_bedrock_model(model_id):
    """Crea il modello Bedrock con configurazione"""
    return BedrockModel(
        model_id=model_id,
        temperature=0.7,
        streaming=True,
    )

@app.entrypoint
def invoke(payload):
    """
    Entrypoint dell'agente Candidate Matcher
    
    Args:
        payload: Dict con chiave 'prompt' contenente il messaggio dell'utente
        
    Returns:
        Risposta dell'agente con i risultati del matching
    """
    mcp_client = MCPClient(_create_streamable_http_transport)
    
    user_message = payload.get("prompt", "Ciao! Sono qui per aiutarti a trovare i needs più adatti per un candidato. Dimmi il ruolo attuale del candidato.")
    
    response = _invoke_agent(
        bedrock_model=_get_bedrock_model("us.anthropic.claude-sonnet-4-20250514-v1:0"),
        mcp_client=mcp_client,
        prompt=user_message
    )
    
    return response

if __name__ == "__main__":
    app.run()
