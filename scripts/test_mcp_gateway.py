import requests
import json
from dotenv import load_dotenv
load_dotenv(override=True)
import os

CLIENT_ID = os.getenv("GATEWAY_CLIENT_ID") 
CLIENT_SECRET = os.getenv("GATEWAY_CLIENT_SECRET")
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )

  return response.json()['access_token']

def call_tool(gateway_url, access_token, tool_name, arguments):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": "call-tool-request",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    response = requests.post(gateway_url, headers=headers, json=payload)
    return response.json()


def list_tools(gateway_url, access_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": "list-tools-request",
        "method": "tools/list"
    }
    
    response = requests.post(gateway_url, headers=headers, json=payload)
    return response.json()

## usage example

access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
gateway_url = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

list_response = list_tools(gateway_url, access_token)
print("Available tools:")
print(json.dumps(list_response, indent=2))

result = call_tool(
    gateway_url, 
    access_token, 
    "save-task___save-task",  # Format: <{TargetId}__{ToolName}>
    {
        "tasks": [
            {
                "title": "Implementare nuova feature",
                "description": "Sviluppare il modulo di autenticazione per l'applicazione",
                "priority": "high",
                "status": "in_progress",
                "due_date": "2024-12-31",
                "category": "work",
                "tags": ["python", "authentication"]
            },
            {
                "title": "Studiare Python async",
                "description": "Approfondire asyncio e concurrent programming",
                "priority": "medium",
                "due_date": "2024-12-25",
                "category": "learning",
                "tags": ["python", "async"]
            }
        ]
    }
)
print("\nTool call result:")
print(json.dumps(result, indent=2))