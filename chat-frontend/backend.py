"""
Backend proxy per connettere il frontend all'orchestrator e alle API Lambda.
Fornisce endpoint per:
- Chat con orchestrator AWS
- CRUD per Goals
- CRUD per Projects
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import logging
import os

app = Flask(__name__)
CORS(app)  # Abilita CORS per il frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione AWS
ORCHESTRATOR_ARN = "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/orchestrator-HR2F4m7QCY"
REGION = "us-east-1"

# ARN Lambda (aggiornati dopo il deploy)
GOAL_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalPost"
GOAL_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalGet"
GOAL_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalDelete"
GOAL_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalUpdate"
PROJECT_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectPost"
PROJECT_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectGet"
PROJECT_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectDelete"
PROJECT_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ProjectUpdate"
CONTACT_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactPost"
CONTACT_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactGet"
CONTACT_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactDelete"
CONTACT_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-ContactUpdate"
EVENT_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventPost"
EVENT_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventGet"
EVENT_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventDelete"
EVENT_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-EventUpdate"
PLACE_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlacePost"
PLACE_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceGet"
PLACE_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceDelete"
PLACE_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-PlaceUpdate"

# Client AWS
bedrock_client = boto3.client('bedrock-agentcore', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "orchestrator-proxy"}), 200


@app.route('/invoke', methods=['POST'])
def invoke_orchestrator():
    """Proxy per invocare l'orchestrator su AWS"""
    try:
        # Ottieni payload dal frontend
        data = request.get_json()
        prompt = data.get('prompt', '')
        actor_id = data.get('actor_id', 'chat-user')
        session_id = data.get('session_id', 'default-session')
        
        if not prompt:
            return jsonify({"error": "Prompt richiesto"}), 400
        
        logger.info(f"Invoking orchestrator: prompt='{prompt[:50]}...', session={session_id}")
        
        # Prepara payload per l'orchestrator
        payload = {
            "prompt": prompt,
            "actor_id": actor_id,
            "session_id": session_id
        }
        
        # Invoca l'orchestrator su AWS
        response = bedrock_client.invoke_agent_runtime(
            agentRuntimeArn=ORCHESTRATOR_ARN,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8')
        )
        
        logger.info(f"Response contentType: {response.get('contentType')}")
        
        # Processa la risposta
        if response.get("contentType") == "application/json":
            content = []
            for chunk in response.get("response", []):
                content.append(chunk.decode('utf-8'))
            
            result_data = json.loads(''.join(content))
            logger.debug(f"Raw result_data type: {type(result_data)}, keys: {result_data.keys() if isinstance(result_data, dict) else 'N/A'}")
            
            # Estrai il testo dalla risposta dell'agent
            result = None
            
            # Prima prova il formato agent: {"role": "assistant", "content": [{"text": "..."}]}
            if isinstance(result_data, dict):
                if 'content' in result_data and isinstance(result_data['content'], list):
                    # Estrai il testo dal primo elemento content
                    if len(result_data['content']) > 0 and isinstance(result_data['content'][0], dict):
                        if 'text' in result_data['content'][0]:
                            result = result_data['content'][0]['text']
                            logger.debug(f"✓ Extracted text from content[0].text")
                
                # Poi prova i campi standard, ma estrai testo se sono dict
                if result is None and 'result' in result_data:
                    res = result_data['result']
                    if isinstance(res, dict) and 'content' in res and isinstance(res['content'], list):
                        if len(res['content']) > 0 and 'text' in res['content'][0]:
                            result = res['content'][0]['text']
                            logger.debug(f"✓ Extracted text from result.content[0].text")
                    elif isinstance(res, str):
                        result = res
                        logger.debug(f"✓ Extracted from 'result' key (string)")
                
                if result is None and 'message' in result_data:
                    msg = result_data['message']
                    if isinstance(msg, dict) and 'content' in msg and isinstance(msg['content'], list):
                        if len(msg['content']) > 0 and 'text' in msg['content'][0]:
                            result = msg['content'][0]['text']
                            logger.debug(f"✓ Extracted text from message.content[0].text")
                    elif isinstance(msg, str):
                        result = msg
                        logger.debug(f"✓ Extracted from 'message' key (string)")
            
            # Fallback: converti tutto a stringa
            if result is None:
                logger.warning("Could not extract result, converting entire result_data to string")
                result = str(result_data) if not isinstance(result_data, str) else result_data
            
            # Assicurati che sia una stringa
            if not isinstance(result, str):
                logger.error(f"Result is still not a string! Type: {type(result)}")
                result = json.dumps(result, ensure_ascii=False, indent=2)
            
            logger.info(f"Final result: {result[:100]}...")
            return jsonify({"result": result}), 200
            
        elif "text/event-stream" in response.get("contentType", ""):
            # Gestisci streaming
            content = []
            for line in response["response"].iter_lines(chunk_size=1024):
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    content.append(line_str)
            
            result = "\n".join(content)
            result_str = str(result)
            logger.info(f"Success (streaming): {result_str[:100]}...")
            return jsonify({"result": result}), 200
        
        else:
            logger.warning(f"Unknown contentType: {response.get('contentType')}")
            return jsonify({"result": str(response)}), 200
        
    except Exception as e:
        logger.error(f"Error invoking orchestrator: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# GOALS API
# ========================================

@app.route('/api/goals', methods=['GET'])
def get_goals():
    """Recupera goals da Lambda"""
    try:
        # Estrai query params
        params = {
            'ambito': request.args.get('ambito'),
            'status': request.args.get('status'),
            'priorita': request.args.get('priorita'),
            'goal_id': request.args.get('goal_id'),
            'limit': request.args.get('limit', '100')
        }
        
        # Rimuovi parametri None
        params = {k: v for k, v in params.items() if v}
        
        logger.info(f"Getting goals with params: {params}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=GOAL_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(params)
        )
        
        result = json.loads(response['Payload'].read())
        logger.debug(f"Lambda response: {result}")
        
        # Gestisci errori Lambda
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting goals: {str(e)}")
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/goals', methods=['POST'])
def create_goal():
    """Crea un nuovo goal"""
    try:
        data = request.get_json()
        logger.info(f"Creating goal: {data.get('titolo')}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=GOAL_POST_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        result = json.loads(response['Payload'].read())
        logger.debug(f"Lambda response: {result}")
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error creating goal: {str(e)}")
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/goals', methods=['DELETE'])
def delete_goal():
    """Cancella un goal esistente"""
    try:
        goal_id = request.args.get('goal_id')
        
        if not goal_id:
            logger.warning("DELETE goal called without goal_id")
            return jsonify({"error": "goal_id è obbligatorio"}), 400
        
        logger.info(f"🗑️ Deleting goal: {goal_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=GOAL_DELETE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'goal_id': goal_id})
        )
        
        logger.info(f"Lambda StatusCode: {response['StatusCode']}")
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        logger.info(f"Raw payload: {payload_bytes}")
        
        result = json.loads(payload_bytes)
        logger.info(f"Parsed Lambda response: {result}")
        
        # Controlla errori Lambda
        if response['StatusCode'] != 200:
            logger.error(f"Lambda invocation failed with status {response['StatusCode']}")
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente
        if 'body' in result:
            logger.info(f"Extracting body from result, type: {type(result['body'])}")
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            status_code = result.get('statusCode', 200)
            logger.info(f"Returning body with status {status_code}: {body}")
            return jsonify(body), status_code
        
        logger.info(f"Returning direct result: {result}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting goal: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/goals', methods=['PUT'])
def update_goal():
    """Aggiorna un goal esistente"""
    try:
        data = request.get_json()
        goal_id = data.get('goal_id')
        
        if not goal_id:
            logger.warning("PUT goal called without goal_id")
            return jsonify({"error": "goal_id è obbligatorio"}), 400
        
        logger.info(f"✏️ Updating goal: {goal_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=GOAL_UPDATE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        logger.info(f"Lambda StatusCode: {response['StatusCode']}")
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        logger.debug(f"Raw payload: {payload_bytes}")
        
        result = json.loads(payload_bytes)
        logger.info(f"Parsed Lambda response: {result}")
        
        # Controlla errori Lambda
        if response['StatusCode'] != 200:
            logger.error(f"Lambda invocation failed with status {response['StatusCode']}")
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            status_code = result.get('statusCode', 200)
            logger.info(f"Returning body with status {status_code}")
            return jsonify(body), status_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating goal: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


# ========================================
# PROJECTS API
# ========================================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Recupera projects da Lambda"""
    try:
        params = {
            'ambito': request.args.get('ambito'),
            'tag': request.args.get('tag'),
            'project_id': request.args.get('project_id'),
            'limit': request.args.get('limit', '100')
        }
        
        # Rimuovi parametri None
        params = {k: v for k, v in params.items() if v}
        
        logger.info(f"Getting projects with params: {params}")
        
        response = lambda_client.invoke(
            FunctionName=PROJECT_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(params)
        )
        
        result = json.loads(response['Payload'].read())
        logger.debug(f"Lambda response: {result}")
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Crea un nuovo project"""
    try:
        data = request.get_json()
        logger.info(f"Creating project: {data.get('titolo')}")
        
        response = lambda_client.invoke(
            FunctionName=PROJECT_POST_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        result = json.loads(response['Payload'].read())
        logger.debug(f"Lambda response: {result}")
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/projects', methods=['DELETE'])
def delete_project():
    """Cancella un project esistente"""
    try:
        project_id = request.args.get('project_id')
        
        if not project_id:
            logger.warning("DELETE project called without project_id")
            return jsonify({"error": "project_id è obbligatorio"}), 400
        
        logger.info(f"🗑️ Deleting project: {project_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=PROJECT_DELETE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'project_id': project_id})
        )
        
        logger.info(f"Lambda StatusCode: {response['StatusCode']}")
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        logger.info(f"Raw payload: {payload_bytes}")
        
        result = json.loads(payload_bytes)
        logger.info(f"Parsed Lambda response: {result}")
        
        # Controlla errori Lambda
        if response['StatusCode'] != 200:
            logger.error(f"Lambda invocation failed with status {response['StatusCode']}")
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente
        if 'body' in result:
            logger.info(f"Extracting body from result, type: {type(result['body'])}")
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            status_code = result.get('statusCode', 200)
            logger.info(f"Returning body with status {status_code}: {body}")
            return jsonify(body), status_code
        
        logger.info(f"Returning direct result: {result}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting project: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/projects', methods=['PUT'])
def update_project():
    """Aggiorna un project esistente"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            logger.warning("PUT project called without project_id")
            return jsonify({"error": "project_id è obbligatorio"}), 400
        
        logger.info(f"✏️ Updating project: {project_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=PROJECT_UPDATE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        logger.info(f"Lambda StatusCode: {response['StatusCode']}")
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        logger.debug(f"Raw payload: {payload_bytes}")
        
        result = json.loads(payload_bytes)
        logger.info(f"Parsed Lambda response: {result}")
        
        # Controlla errori Lambda
        if response['StatusCode'] != 200:
            logger.error(f"Lambda invocation failed with status {response['StatusCode']}")
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            status_code = result.get('statusCode', 200)
            logger.info(f"Returning body with status {status_code}")
            return jsonify(body), status_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating project: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


# ========================================
# CONTACTS API (Proxy to Lambda)
# ========================================

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Recupera contatti con filtri opzionali"""
    try:
        # Ottieni parametri query
        nome = request.args.get('nome', '')
        cognome = request.args.get('cognome', '')
        email = request.args.get('email', '')
        dove_conosciuto = request.args.get('dove_conosciuto', '')
        contact_id = request.args.get('contact_id', '')
        limit = request.args.get('limit', '100')
        
        # Costruisci payload
        payload = {}
        if nome:
            payload['nome'] = nome
        if cognome:
            payload['cognome'] = cognome
        if email:
            payload['email'] = email
        if dove_conosciuto:
            payload['dove_conosciuto'] = dove_conosciuto
        if contact_id:
            payload['contact_id'] = contact_id
        if limit:
            payload['limit'] = int(limit)
        
        logger.info(f"📖 Getting contacts with filters: {payload}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=CONTACT_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Lambda returned {len(body.get('contacts', []))} contacts")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Lambda returned {len(result.get('contacts', []))} contacts")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting contacts: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/contacts', methods=['POST'])
def create_contact():
    """Crea un nuovo contatto"""
    try:
        data = request.get_json()
        logger.info(f"➕ Creating contact: {data.get('nome', '')} {data.get('cognome', '')}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=CONTACT_POST_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Contact created: {body.get('contact_id', 'unknown')}")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Contact created: {result.get('contact_id', 'unknown')}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error creating contact: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/contacts', methods=['DELETE'])
def delete_contact():
    """Elimina un contatto"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        
        if not contact_id:
            return jsonify({"error": "contact_id è obbligatorio"}), 400
        
        logger.info(f"🗑️ Deleting contact: {contact_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=CONTACT_DELETE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Contact deleted successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Contact deleted successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting contact: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/contacts', methods=['PUT'])
def update_contact():
    """Aggiorna un contatto esistente"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        
        if not contact_id:
            return jsonify({"error": "contact_id è obbligatorio"}), 400
        
        logger.info(f"✏️ Updating contact: {contact_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=CONTACT_UPDATE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Contact updated successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Contact updated successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating contact: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


# ========================================
# EVENT ENDPOINTS
# ========================================

@app.route('/api/events', methods=['GET'])
def get_events():
    """Recupera eventi con filtri opzionali"""
    try:
        params = request.args.to_dict()
        logger.info(f"📅 Getting events with filters: {params}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=EVENT_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(params)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Found {body.get('count', 0)} events")
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting events: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """Recupera un evento specifico"""
    try:
        logger.info(f"📅 Getting event: {event_id}")
        
        response = lambda_client.invoke(
            FunctionName=EVENT_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'event_id': event_id})
        )
        
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting event: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/events', methods=['POST'])
def create_event():
    """Crea un nuovo evento"""
    try:
        data = request.get_json()
        logger.info(f"📅 Creating event: {data.get('nome')}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=EVENT_POST_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Event created successfully")
            return jsonify(body), result.get('statusCode', 201)
        
        logger.info(f"Event created successfully")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating event: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Elimina un evento"""
    try:
        logger.info(f"📅 Deleting event: {event_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=EVENT_DELETE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'event_id': event_id})
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Event deleted successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Event deleted successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting event: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Aggiorna un evento esistente"""
    try:
        data = request.get_json()
        data['event_id'] = event_id
        
        logger.info(f"✏️ Updating event: {event_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=EVENT_UPDATE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Event updated successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Event updated successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating event: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


# ========================================
# PLACE ENDPOINTS
# ========================================

@app.route('/api/places', methods=['GET'])
def get_places():
    """Recupera luoghi con filtri opzionali"""
    try:
        params = request.args.to_dict()
        logger.info(f"📍 Getting places with filters: {params}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=PLACE_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(params)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Found {body.get('count', 0)} places")
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting places: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/places/<place_id>', methods=['GET'])
def get_place(place_id):
    """Recupera un luogo specifico"""
    try:
        logger.info(f"📍 Getting place: {place_id}")
        
        response = lambda_client.invoke(
            FunctionName=PLACE_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'place_id': place_id})
        )
        
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting place: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/places', methods=['POST'])
def create_place():
    """Crea un nuovo luogo"""
    try:
        data = request.get_json()
        logger.info(f"📍 Creating place: {data.get('nome')}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=PLACE_POST_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Place created successfully")
            return jsonify(body), result.get('statusCode', 201)
        
        logger.info(f"Place created successfully")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating place: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/places/<place_id>', methods=['DELETE'])
def delete_place(place_id):
    """Elimina un luogo"""
    try:
        logger.info(f"📍 Deleting place: {place_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=PLACE_DELETE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'place_id': place_id})
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Place deleted successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Place deleted successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting place: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/places/<place_id>', methods=['PUT'])
def update_place(place_id):
    """Aggiorna un luogo esistente"""
    try:
        data = request.get_json()
        data['place_id'] = place_id
        
        logger.info(f"✏️ Updating place: {place_id}")
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=PLACE_UPDATE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Place updated successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"Place updated successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating place: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Personal Assistant Backend Server")
    print("=" * 60)
    print(f"Orchestrator ARN: {ORCHESTRATOR_ARN}")
    print(f"Region: {REGION}")
    print(f"Server: http://localhost:5000")
    print("=" * 60)
    print("\nEndpoints disponibili:")
    print("  POST /invoke          - Chat con orchestrator")
    print("  GET  /api/goals       - Recupera obiettivi")
    print("  POST /api/goals       - Crea obiettivo")
    print("  PUT  /api/goals       - Aggiorna obiettivo")
    print("  DELETE /api/goals     - Cancella obiettivo")
    print("  GET  /api/projects    - Recupera progetti")
    print("  POST /api/projects    - Crea progetto")
    print("  PUT  /api/projects    - Aggiorna progetto")
    print("  DELETE /api/projects  - Cancella progetto")
    print("  GET  /api/contacts    - Recupera contatti")
    print("  POST /api/contacts    - Crea contatto")
    print("  PUT  /api/contacts    - Aggiorna contatto")
    print("  DELETE /api/contacts  - Cancella contatto")
    print("  GET  /api/events      - Recupera eventi")
    print("  POST /api/events      - Crea evento")
    print("  PUT  /api/events      - Aggiorna evento")
    print("  DELETE /api/events    - Cancella evento")
    print("  GET  /api/places      - Recupera luoghi")
    print("  POST /api/places      - Crea luogo")
    print("  PUT  /api/places      - Aggiorna luogo")
    print("  DELETE /api/places    - Cancella luogo")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

