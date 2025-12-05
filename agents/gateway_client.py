"""
AgentCore Gateway Client - Secure Lambda Access

This module provides a client for interacting with AWS AgentCore Gateway
to securely invoke Lambda functions with OAuth2 authentication.

Based on official AWS AgentCore documentation:
https://aws.github.io/bedrock-agentcore-starter-toolkit/examples/gateway-integration.md
"""

import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging


class GatewayTokenManager:
    """Manages OAuth2 tokens with automatic refresh for AgentCore Gateway."""

    def __init__(self, client_id: str, client_secret: str, token_endpoint: str, scope: str):
        """
        Initialize the token manager.

        Args:
            client_id: OAuth2 client ID from Cognito
            client_secret: OAuth2 client secret from Cognito
            token_endpoint: Cognito token endpoint URL
            scope: OAuth2 scope (e.g., 'invoke')
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.scope = scope
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self.logger = logging.getLogger(__name__)

    def get_token(self) -> str:
        """
        Get a valid OAuth2 token, refreshing if needed.

        Returns:
            str: Valid access token

        Raises:
            Exception: If token retrieval fails
        """
        # Return cached token if still valid
        if self._token and self._expires_at and self._expires_at > datetime.now():
            return self._token

        self.logger.info("Fetching new OAuth2 token from Cognito...")

        # Fetch new token using client credentials flow
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.token_endpoint,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'scope': self.scope
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                response.raise_for_status()
                data = response.json()

                self._token = data['access_token']
                # Buffer expiry by 5 minutes to avoid edge cases
                expires_in = data.get('expires_in', 3600) - 300
                self._expires_at = datetime.now() + timedelta(seconds=expires_in)

                self.logger.info("✅ OAuth2 token retrieved successfully")
                return self._token

        except httpx.HTTPError as e:
            self.logger.error(f"Failed to retrieve OAuth2 token: {e}")
            raise Exception(f"OAuth2 token retrieval failed: {e}")


class GatewayClient:
    """
    Client for invoking tools through AgentCore Gateway with OAuth2 authentication.

    This client provides secure access to Lambda functions through AgentCore Gateway
    using MCP (Model Context Protocol) and OAuth2 bearer token authentication.
    """

    def __init__(
        self,
        gateway_url: str,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        scope: str = "invoke"
    ):
        """
        Initialize the Gateway client.

        Args:
            gateway_url: AgentCore Gateway MCP endpoint URL
            client_id: OAuth2 client ID from Cognito
            client_secret: OAuth2 client secret from Cognito
            token_endpoint: Cognito token endpoint URL
            scope: OAuth2 scope (default: 'invoke')
        """
        self.gateway_url = gateway_url
        self.token_manager = GatewayTokenManager(client_id, client_secret, token_endpoint, scope)
        self.logger = logging.getLogger(__name__)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool exposed through the Gateway.

        Args:
            tool_name: Name of the tool to invoke (e.g., 'save_task', 'get_tasks')
            arguments: Tool arguments as a dictionary

        Returns:
            Tool execution result

        Raises:
            Exception: If tool invocation fails
        """
        self.logger.info(f"Calling Gateway tool: {tool_name}")

        # Get valid OAuth2 token
        token = self.token_manager.get_token()

        # Make MCP tool call request
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.gateway_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                # Check for JSON-RPC error
                if 'error' in result:
                    error_msg = result['error']
                    self.logger.error(f"Tool error: {error_msg}")
                    raise Exception(f"Gateway tool error: {error_msg}")

                self.logger.info(f"✅ Tool {tool_name} executed successfully")
                return result.get('result')

        except httpx.HTTPError as e:
            self.logger.error(f"Gateway HTTP error: {e}")
            raise Exception(f"Gateway request failed: {e}")

    @classmethod
    def from_env(cls) -> "GatewayClient":
        """
        Create a GatewayClient from environment variables.

        Expected environment variables:
        - GATEWAY_MCP_URL: AgentCore Gateway MCP endpoint
        - GATEWAY_CLIENT_ID: OAuth2 client ID
        - GATEWAY_CLIENT_SECRET: OAuth2 client secret
        - GATEWAY_TOKEN_ENDPOINT: Cognito token endpoint
        - GATEWAY_SCOPE: OAuth2 scope (optional, defaults to 'invoke')

        Returns:
            GatewayClient: Initialized client

        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = [
            'GATEWAY_MCP_URL',
            'GATEWAY_CLIENT_ID',
            'GATEWAY_CLIENT_SECRET',
            'GATEWAY_TOKEN_ENDPOINT'
        ]

        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            gateway_url=os.environ['GATEWAY_MCP_URL'],
            client_id=os.environ['GATEWAY_CLIENT_ID'],
            client_secret=os.environ['GATEWAY_CLIENT_SECRET'],
            token_endpoint=os.environ['GATEWAY_TOKEN_ENDPOINT'],
            scope=os.environ.get('GATEWAY_SCOPE', 'invoke')
        )


# Helper function for task management
def get_gateway_client() -> GatewayClient:
    """
    Get a configured GatewayClient from environment variables.

    Returns:
        GatewayClient: Configured client ready for tool invocation

    Raises:
        ValueError: If Gateway is not configured
    """
    try:
        return GatewayClient.from_env()
    except ValueError as e:
        logging.error(f"Gateway configuration error: {e}")
        raise ValueError(
            "AgentCore Gateway not configured. "
            "Please set GATEWAY_MCP_URL, GATEWAY_CLIENT_ID, "
            "GATEWAY_CLIENT_SECRET, and GATEWAY_TOKEN_ENDPOINT environment variables."
        )
