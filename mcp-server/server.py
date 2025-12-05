"""
MCP (Model Context Protocol) Server
Server autenticato per esporre tool esterni agli agenti AWS.
Implementa tool Outlook con OAuth2.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import msal
from msgraph.core import GraphClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
MCP_API_KEY = os.environ.get('MCP_API_KEY')
OUTLOOK_CLIENT_ID = os.environ.get('OUTLOOK_CLIENT_ID')
OUTLOOK_CLIENT_SECRET = os.environ.get('OUTLOOK_CLIENT_SECRET')
OUTLOOK_TENANT_ID = os.environ.get('OUTLOOK_TENANT_ID')

# FastAPI app
app = FastAPI(
    title="MCP Server - Personal Assistant",
    description="Model Context Protocol server con tool Outlook e future estensioni",
    version="1.0.0"
)

security = HTTPBearer()


# Pydantic models
class ToolInvocationRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]


class ToolInvocationResponse(BaseModel):
    success: bool
    tool: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OutlookEmailFilter(BaseModel):
    isImportant: Optional[bool] = None
    isRead: Optional[bool] = None
    hasFlag: Optional[bool] = None
    from_email: Optional[str] = None


# Authentication
def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica API key per autenticazione MCP server.
    """
    token = credentials.credentials
    if token != MCP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token


class OutlookClient:
    """
    Client per interagire con Microsoft Graph API (Outlook).
    Gestisce autenticazione OAuth2 e chiamate API.
    """
    
    def __init__(self):
        self.client_id = OUTLOOK_CLIENT_ID
        self.client_secret = OUTLOOK_CLIENT_SECRET
        self.tenant_id = OUTLOOK_TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        # MSAL confidential client
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        self.access_token = None
        self.token_expiry = None
    
    def _get_access_token(self) -> str:
        """
        Ottiene access token tramite OAuth2 Client Credentials flow.
        """
        # Verifica se token è ancora valido
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token
        
        # Acquisisci nuovo token
        result = self.app.acquire_token_for_client(scopes=self.scopes)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            expires_in = result.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            logger.info("Access token acquired successfully")
            return self.access_token
        else:
            error = result.get("error_description", "Unknown error")
            logger.error(f"Failed to acquire token: {error}")
            raise HTTPException(status_code=500, detail=f"Authentication failed: {error}")
    
    def get_emails(
        self,
        folder: str = "inbox",
        max_results: int = 10,
        email_filter: Optional[OutlookEmailFilter] = None,
        select_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera email da Outlook.
        """
        try:
            token = self._get_access_token()
            client = GraphClient(credential=token)
            
            # Build query
            folder_path = f"/me/mailFolders/{folder}/messages"
            
            # Select fields
            select = select_fields or [
                "subject", "from", "receivedDateTime", 
                "importance", "isRead", "hasAttachments", "bodyPreview"
            ]
            select_param = ",".join(select)
            
            # Build filter
            filters = []
            if email_filter:
                if email_filter.isImportant is not None:
                    filters.append(f"importance eq 'high'")
                if email_filter.isRead is not None:
                    filters.append(f"isRead eq {str(email_filter.isRead).lower()}")
                if email_filter.from_email:
                    filters.append(f"from/emailAddress/address eq '{email_filter.from_email}'")
            
            filter_param = " and ".join(filters) if filters else None
            
            # Build URL
            url = f"{folder_path}?$select={select_param}&$top={max_results}"
            if filter_param:
                url += f"&$filter={filter_param}"
            url += "&$orderby=receivedDateTime desc"
            
            # Make request
            response = client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get("value", [])
                
                # Semplifica formato
                simplified_emails = []
                for email in emails:
                    simplified_emails.append({
                        "id": email.get("id"),
                        "subject": email.get("subject"),
                        "from": {
                            "name": email.get("from", {}).get("emailAddress", {}).get("name"),
                            "email": email.get("from", {}).get("emailAddress", {}).get("address")
                        },
                        "received_at": email.get("receivedDateTime"),
                        "is_important": email.get("importance") == "high",
                        "is_read": email.get("isRead"),
                        "has_attachments": email.get("hasAttachments"),
                        "preview": email.get("bodyPreview")
                    })
                
                logger.info(f"Retrieved {len(simplified_emails)} emails from {folder}")
                return simplified_emails
            else:
                logger.error(f"Graph API error: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch emails")
        
        except Exception as e:
            logger.error(f"Error fetching emails: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Cerca email con query di ricerca.
        """
        try:
            token = self._get_access_token()
            client = GraphClient(credential=token)
            
            url = f"/me/messages?$search=\"{query}\"&$top={max_results}"
            
            response = client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            else:
                raise HTTPException(status_code=response.status_code, detail="Search failed")
        
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Global Outlook client instance
outlook_client = OutlookClient()


# MCP Server endpoints

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "MCP Server - Personal Assistant",
        "version": "1.0.0",
        "status": "running",
        "tools": [
            "outlook_get_emails",
            "outlook_search_emails"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/tools/invoke", response_model=ToolInvocationResponse, dependencies=[Depends(verify_api_key)])
def invoke_tool(request: ToolInvocationRequest):
    """
    Invoca un tool MCP.
    """
    try:
        tool_name = request.tool
        params = request.parameters
        
        logger.info(f"Invoking tool: {tool_name}")
        
        if tool_name == "outlook_get_emails":
            # Get emails tool
            folder = params.get("folder", "inbox")
            max_results = params.get("max_results", 10)
            filter_data = params.get("filter", {})
            select_fields = params.get("select")
            
            email_filter = OutlookEmailFilter(**filter_data) if filter_data else None
            
            emails = outlook_client.get_emails(
                folder=folder,
                max_results=max_results,
                email_filter=email_filter,
                select_fields=select_fields
            )
            
            return ToolInvocationResponse(
                success=True,
                tool=tool_name,
                result={"emails": emails, "count": len(emails)}
            )
        
        elif tool_name == "outlook_search_emails":
            # Search emails tool
            query = params.get("query")
            max_results = params.get("max_results", 10)
            
            if not query:
                raise HTTPException(status_code=400, detail="Query parameter required")
            
            emails = outlook_client.search_emails(query, max_results)
            
            return ToolInvocationResponse(
                success=True,
                tool=tool_name,
                result={"emails": emails, "count": len(emails)}
            )
        
        else:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool invocation error: {e}", exc_info=True)
        return ToolInvocationResponse(
            success=False,
            tool=request.tool,
            error=str(e)
        )


@app.get("/tools")
def list_tools(api_key: str = Depends(verify_api_key)):
    """
    Lista tutti i tool disponibili.
    """
    return {
        "tools": [
            {
                "name": "outlook_get_emails",
                "description": "Recupera email da Outlook con filtri opzionali",
                "parameters": {
                    "folder": "string (default: inbox)",
                    "max_results": "integer (default: 10)",
                    "filter": {
                        "isImportant": "boolean",
                        "isRead": "boolean",
                        "hasFlag": "boolean",
                        "from_email": "string"
                    },
                    "select": "array[string]"
                }
            },
            {
                "name": "outlook_search_emails",
                "description": "Cerca email con query di ricerca",
                "parameters": {
                    "query": "string (required)",
                    "max_results": "integer (default: 10)"
                }
            }
        ]
    }


# Run server
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting MCP Server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
