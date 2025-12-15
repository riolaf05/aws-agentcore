# Agent per la scrittura di task in DynamoDB tramite Gateway MCP
# Utilizza Strands Agents con integrazione MCP Client per chiamare Lambda functions
# I tool vengono recuperati dinamicamente dal Gateway MCP

from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp
import logging
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import os
import requests

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenziali Cognito per OAuth2
CLIENT_ID = "40ipvfb7kr5hnjqm06555e5hlp"
CLIENT_SECRET = "6rtmm58udin800qd6eiufv8top19q615m57etqha4fn9opmbi3f"
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"


def get_token(client_id: str, client_secret: str, token_url: str) -> str:
    """
    Ottiene un access token OAuth2 da AWS Cognito.
    
    Args:
        client_id: Client ID dell'app Cognito
        client_secret: Client secret dell'app Cognito
        token_url: URL del token endpoint Cognito
    
    Returns:
        Access token JWT
    """
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    response.raise_for_status()
    return response.json()['access_token']


def create_streamable_http_transport(mcp_url: str, access_token: str):
    """
    Crea un trasporto HTTP streamabile per comunicare con il Gateway MCP.
    
    Args:
        mcp_url: URL del Gateway MCP
        access_token: Token OAuth2 per l'autenticazione
    
    Returns:
        Trasporto HTTP configurato con autenticazione Bearer
    """
    return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def get_full_tools_list(client):
    """
    List tools w/ support for pagination
    """
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True
            pagination_token = tmp_tools.pagination_token
    return tools


# URL del Gateway MCP
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

# Crea l'applicazione BedrockAgentCore
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload, context):
    """
    Entrypoint dell'agente TaskWriter.
    L'agente utilizza automaticamente i tool recuperati dal Gateway MCP.
    Mantiene la connessione MCP aperta per tutta la durata dell'invocazione.
    """
    logger.info(f"TaskWriter Agent invocato - Session: {context.session_id if context else 'unknown'}")
    
    # Ottieni token OAuth2 per ogni invocazione (possono scadere)
    logger.info("Ottenendo token OAuth2 da Cognito...")
    access_token = get_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    logger.info("Token OAuth2 ottenuto con successo")
    
    # Crea il client MCP
    logger.info(f"Connessione al Gateway MCP: {GATEWAY_URL}")
    mcp_client = MCPClient(lambda: create_streamable_http_transport(GATEWAY_URL, access_token))
    
    try:
        # IMPORTANTE: Mantieni la connessione MCP aperta per tutta l'invocazione
        mcp_client.__enter__()
        
        # Crea il modello Bedrock
        model = BedrockModel(
            model_id="us.amazon.nova-pro-v1:0",
            temperature=0.7
        )
        
        # Recupera i tool dal Gateway MCP
        tools = get_full_tools_list(mcp_client)
        logger.info(f"Found the following tools: {[tool.tool_name for tool in tools]}")
        
        # Crea l'agente Strands con i tool MCP
        agent = Agent(
            name="TaskWriter",
            description="Agente per gestire task in DynamoDB tramite Gateway MCP",
            model=model,
            tools=tools
        )
        logger.info(f"Agente creato con {len(tools)} tool dal Gateway MCP")
        
        # Estrai il messaggio utente dal payload
        user_message = payload.get('prompt', '')
        logger.info(f"Prompt utente: {user_message}")
        
        # Chiama l'agente - la connessione MCP è ancora aperta
        result = agent(user_message)
        logger.info("Risposta generata con successo")
        return result
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {str(e)}", exc_info=True)
        return {
            "role": "assistant",
            "content": [{
                "text": f"Mi dispiace, si è verificato un errore: {str(e)}"
            }]
        }
    finally:
        # Chiudi la connessione MCP al termine dell'invocazione
        try:
            mcp_client.__exit__(None, None, None)
            logger.info("Connessione MCP chiusa")
        except Exception as e:
            logger.warning(f"Errore durante chiusura MCP client: {e}")

if __name__ == "__main__":
    app.run()
