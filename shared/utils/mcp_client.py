"""
Helper per invocare un server MCP esterno tramite HTTPS con x-api-key.
Gestisce la comunicazione con server MCP esterni tramite API REST.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# AWS clients
secretsmanager_client = boto3.client('secretsmanager')


class MCPClient:
    """
    Client per comunicare con server MCP esterni via HTTPS.
    """
    
    def __init__(self, secret_name: Optional[str] = None):
        """
        Inizializza il client MCP.
        
        Args:
            secret_name: Nome del secret AWS Secrets Manager contenente URL e API key
        """
        self.secret_name = secret_name or os.environ.get('MCP_SECRET_NAME')
        self.mcp_url = None
        self.api_key = None
        self._load_credentials()
    
    def _load_credentials(self):
        """
        Carica URL e API key da AWS Secrets Manager o variabili d'ambiente.
        """
        try:
            if self.secret_name:
                # Carica da Secrets Manager
                logger.info(f"Loading MCP credentials from secret: {self.secret_name}")
                response = secretsmanager_client.get_secret_value(SecretId=self.secret_name)
                secret = json.loads(response['SecretString'])
                self.mcp_url = secret.get('url')
                self.api_key = secret.get('apiKey')
            else:
                # Fallback a variabili d'ambiente
                logger.info("Loading MCP credentials from environment variables")
                self.mcp_url = os.environ.get('MCP_SERVER_URL')
                self.api_key = os.environ.get('MCP_API_KEY')
            
            if not self.mcp_url or not self.api_key:
                raise ValueError("MCP URL or API key not configured")
            
            logger.info(f"MCP client configured for URL: {self.mcp_url}")
            
        except ClientError as e:
            logger.error(f"Error loading MCP credentials from Secrets Manager: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading MCP credentials: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Restituisce gli headers HTTP per le richieste MCP.
        """
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'User-Agent': 'AWS-AgentCore-MCP-Client/1.0'
        }
    
    def invoke_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Invoca un tool sul server MCP esterno.
        
        Args:
            tool_name: Nome del tool da invocare
            arguments: Argomenti del tool
            timeout: Timeout della richiesta in secondi
            
        Returns:
            Risposta del server MCP
        """
        try:
            endpoint = f"{self.mcp_url}/tools/{tool_name}"
            
            payload = {
                'name': tool_name,
                'arguments': arguments
            }
            
            logger.info(f"Invoking MCP tool: {tool_name} at {endpoint}")
            logger.debug(f"Tool arguments: {json.dumps(arguments)}")
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=self._get_headers(),
                timeout=timeout
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"MCP tool {tool_name} executed successfully")
            logger.debug(f"Tool result: {json.dumps(result)}")
            
            return {
                'success': True,
                'result': result
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling MCP tool {tool_name}")
            return {
                'success': False,
                'error': f"Timeout calling tool {tool_name}"
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error calling MCP tool {tool_name}: {e}")
            return {
                'success': False,
                'error': f"HTTP error: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_tools(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Ottiene la lista di tool disponibili sul server MCP.
        
        Args:
            timeout: Timeout della richiesta in secondi
            
        Returns:
            Lista di tool disponibili
        """
        try:
            endpoint = f"{self.mcp_url}/tools"
            
            logger.info(f"Listing MCP tools from {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=timeout
            )
            
            response.raise_for_status()
            
            tools = response.json()
            logger.info(f"Retrieved {len(tools.get('tools', []))} MCP tools")
            
            return {
                'success': True,
                'tools': tools.get('tools', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing MCP tools: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'tools': []
            }
    
    def invoke_prompt(
        self, 
        prompt_name: str, 
        arguments: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Invoca un prompt sul server MCP esterno.
        
        Args:
            prompt_name: Nome del prompt da invocare
            arguments: Argomenti opzionali del prompt
            timeout: Timeout della richiesta in secondi
            
        Returns:
            Risposta del prompt
        """
        try:
            endpoint = f"{self.mcp_url}/prompts/{prompt_name}"
            
            payload = {
                'name': prompt_name,
                'arguments': arguments or {}
            }
            
            logger.info(f"Invoking MCP prompt: {prompt_name} at {endpoint}")
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=self._get_headers(),
                timeout=timeout
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"MCP prompt {prompt_name} executed successfully")
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error calling MCP prompt {prompt_name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_resources(
        self, 
        resource_uri: Optional[str] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Ottiene risorse dal server MCP.
        
        Args:
            resource_uri: URI opzionale della risorsa specifica
            timeout: Timeout della richiesta in secondi
            
        Returns:
            Risorse disponibili
        """
        try:
            endpoint = f"{self.mcp_url}/resources"
            if resource_uri:
                endpoint = f"{endpoint}/{resource_uri}"
            
            logger.info(f"Getting MCP resources from {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=timeout
            )
            
            response.raise_for_status()
            
            resources = response.json()
            logger.info("Retrieved MCP resources successfully")
            
            return {
                'success': True,
                'resources': resources
            }
            
        except Exception as e:
            logger.error(f"Error getting MCP resources: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'resources': {}
            }


def create_mcp_client(secret_name: Optional[str] = None) -> MCPClient:
    """
    Factory function per creare un client MCP.
    
    Args:
        secret_name: Nome del secret AWS Secrets Manager
        
    Returns:
        Istanza configurata di MCPClient
    """
    return MCPClient(secret_name=secret_name)


# Esempio di utilizzo
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Esempio di utilizzo del client
    try:
        client = create_mcp_client()
        
        # Lista tool disponibili
        tools_response = client.list_tools()
        if tools_response['success']:
            print("Available tools:")
            for tool in tools_response['tools']:
                print(f"  - {tool.get('name')}: {tool.get('description')}")
        
        # Esempio di invocazione tool
        # result = client.invoke_tool(
        #     'example_tool',
        #     {'param1': 'value1'}
        # )
        # print(f"Tool result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
