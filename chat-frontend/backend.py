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
from datetime import datetime

# Import delle utilities custom
from pdf_utils import extract_text_from_pdf, chunk_text
from qdrant_utils import QdrantManager
import hashlib
from requests_toolbelt.multipart.encoder import MultipartEncoder

app = Flask(__name__)
CORS(app)  # Abilita CORS per il frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione AWS
ORCHESTRATOR_ARN = "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/orchestrator-HR2F4m7QCY"
PROJECT_GOAL_WRITER_READER_ARN = os.getenv(
    "PROJECT_GOAL_WRITER_READER_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/project_goal_writer_reader-61UCrz38Qt"
)
PROJECT_UPDATES_EXTRACTOR_ARN = os.getenv(
    "PROJECT_UPDATES_EXTRACTOR_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/project_updates_extractor-58Njxi3hnT"
)
REGION = "us-east-1"

# ARN Lambda (aggiornati dopo il deploy)
GOAL_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalPost"
GOAL_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalGet"
GOAL_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalDelete"
GOAL_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalUpdate"
GOAL_SEARCH_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-GoalSearch"
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
KB_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-KBPost"
KB_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-KBGet"
KB_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-KBDelete"

# N8N Webhooks per Knowledge Base
N8N_WEBHOOK_KB_TEST = "http://host.docker.internal:5678/webhook-test/ae7ec17c-64fc-4848-bcd5-a081e11a6051"
N8N_WEBHOOK_KB_PROD = "http://host.docker.internal:5678/webhook/ae7ec17c-64fc-4848-bcd5-a081e11a6051"
# Token di autorizzazione per N8N (configura nel tuo ambiente)
N8N_API_KEY = os.getenv('N8N_API_KEY', '')  # Imposta tramite variabile ambiente

# Configurazione Qdrant
QDRANT_HOST = os.getenv('QDRANT_HOST', 'host.docker.internal')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6333'))
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'knowledge_base')
QDRANT_VECTOR_SIZE = int(os.getenv('QDRANT_VECTOR_SIZE', '1536'))

# Client AWS
bedrock_client = boto3.client('bedrock-agentcore', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)

# Qdrant Manager
try:
    qdrant_manager = QdrantManager(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=QDRANT_COLLECTION
    )
    logger.info(f"✅ Qdrant manager initialized: {QDRANT_HOST}:{QDRANT_PORT}")
except Exception as e:
    logger.warning(f"⚠️ Qdrant manager initialization failed: {e}")
    qdrant_manager = None


# ========== UTILITY FUNCTIONS ==========

def _simple_hash_embedding(text, size=1536):
    """Genera un embedding deterministico semplice (fallback) basato su hash."""
    if not text:
        return [0.0] * size
    digest = hashlib.sha256(text.encode('utf-8')).digest()
    return [(digest[i % len(digest)] / 255.0) for i in range(size)]


def _parse_json_field(value, default=None):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default

def identify_goal_from_text(text):
    """Invoca l'agente project-goal-writer-reader per identificare il nome dell'obiettivo dal testo"""
    import uuid
    try:
        # Prepara il prompt per l'agent
        prompt = f"""Analizza il seguente testo e identifica il nome dell'obiettivo principale menzionato.
Rispondi SOLO con il nome dell'obiettivo come stringa semplice, senza spiegazioni.
Se non trovi nessun obiettivo, rispondi solo con la parola "vuoto".

Testo:
{text[:2000]}"""  # Limita a 2000 caratteri per non eccedere

        logger.info(f"🧠 Agent prompt (goal identification): {prompt}")
        logger.info(f"🔍 Calling project-goal-writer-reader agent to identify goal from text")
        
        response = _invoke_agent_runtime(PROJECT_GOAL_WRITER_READER_ARN, {"prompt": prompt})
        
        logger.info(f"Agent response contentType: {response.get('contentType')}")
        
        # Processa la risposta
        result = _parse_agent_response(response)
        if isinstance(result, dict):
            goal_name = result.get('result', 'vuoto').strip()
        else:
            goal_name = str(result).strip()
        
        # Pulisci la risposta da newline e whitespace
        goal_name = goal_name.replace('\n', '').strip()
        
        if not goal_name or goal_name.lower() == 'vuoto':
            logger.info(f"ℹ️ Agent returned no goal match")
            logger.info(f"🧠 Agent response: vuoto")
            return "vuoto"
        
        logger.info(f"✅ Agent identified goal: {goal_name}")
        logger.info(f"🧠 Agent response: {goal_name}")
        return goal_name
        
    except Exception as e:
        logger.error(f"❌ Error identifying goal: {e}", exc_info=True)
        return "vuoto"


def _invoke_agent_runtime(agent_arn, payload_dict):
    import uuid
    payload_data = json.dumps(payload_dict).encode('utf-8')
    return bedrock_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        runtimeSessionId=str(uuid.uuid4()),
        payload=payload_data
    )


def _parse_agent_response(response):
    content = []
    if response.get("contentType") == "application/json":
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        result_str = ''.join(content)
        logger.debug(f"Raw response: {result_str}")
        try:
            return json.loads(result_str)
        except Exception:
            return result_str

    for chunk in response.get("response", []):
        if isinstance(chunk, bytes):
            content.append(chunk.decode('utf-8'))
        else:
            content.append(str(chunk))
    return ''.join(content).strip()


def _extract_text_from_agent_result(result):
    if isinstance(result, dict):
        content = result.get('content')
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict) and 'text' in first:
                return first['text']
    if isinstance(result, str):
        return result
    return str(result)


def extract_project_updates_from_text(text):
    try:
        payload = {"text": text[:4000]}
        response = _invoke_agent_runtime(PROJECT_UPDATES_EXTRACTOR_ARN, payload)
        result = _parse_agent_response(response)

        if isinstance(result, dict) and all(k in result for k in ["avanzamenti", "cose_da_fare", "punti_attenzione"]):
            return result

        raw_text = _extract_text_from_agent_result(result).strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        return json.loads(raw_text)
    except Exception as e:
        logger.error(f"❌ Error extracting project updates: {e}", exc_info=True)
        return {"avanzamenti": [], "cose_da_fare": [], "punti_attenzione": []}


def update_goal_with_advancements(goal_name, updates):
    try:
        avanzamenti = updates.get("avanzamenti", []) if isinstance(updates, dict) else []
        if not avanzamenti:
            logger.info("ℹ️ No advancements to update for goal")
            return

        note_lines = "\n".join([f"- {a}" for a in avanzamenti])
        prompt = (
            f"Cerca l'obiettivo '{goal_name}' e aggiungi una nota di avanzamento con i seguenti punti:\n"
            f"{note_lines}"
        )

        response = _invoke_agent_runtime(PROJECT_GOAL_WRITER_READER_ARN, {"prompt": prompt})
        _ = _parse_agent_response(response)
        logger.info("✅ Goal updated with advancements")
    except Exception as e:
        logger.error(f"❌ Error updating goal with advancements: {e}", exc_info=True)



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
                logger.debug(f"result_data is dict, checking 'content' field...")
                if 'content' in result_data:
                    content_field = result_data['content']
                    logger.debug(f"content field type: {type(content_field)}")
                    
                    if isinstance(content_field, list):
                        logger.debug(f"content is list with {len(content_field)} elements")
                        # Estrai il testo dal primo elemento content
                        if len(content_field) > 0:
                            first_elem = content_field[0]
                            logger.debug(f"First element type: {type(first_elem)}")
                            if isinstance(first_elem, dict) and 'text' in first_elem:
                                result = first_elem['text']
                                logger.debug(f"✓ Extracted text from content[0].text")
                    elif isinstance(content_field, str):
                        # Content è direttamente una stringa
                        result = content_field
                        logger.debug(f"✓ Extracted from content field (string)")
                    elif isinstance(content_field, dict) and 'text' in content_field:
                        # Content è un dict con field text
                        result = content_field['text']
                        logger.debug(f"✓ Extracted from content.text")
                
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


@app.route('/api/goals/search', methods=['GET'])
def search_goal():
    """Cerca un goal per titolo/nome"""
    try:
        titolo = request.args.get('titolo')
        ambito = request.args.get('ambito')
        status = request.args.get('status')
        limit = request.args.get('limit', '50')
        
        if not titolo:
            logger.warning("GET /api/goals/search called without titolo parameter")
            return jsonify({"error": "titolo è obbligatorio per la ricerca"}), 400
        
        logger.info(f"🔍 Searching goals by titolo: {titolo}")
        
        # Prepara query parameters
        query_params = {
            'titolo': titolo,
            'limit': limit
        }
        if ambito:
            query_params['ambito'] = ambito
        if status:
            query_params['status'] = status
        
        # Invoca Lambda con query parameters
        response = lambda_client.invoke(
            FunctionName=GOAL_SEARCH_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(query_params)
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
        logger.error(f"Error searching goals: {str(e)}")
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/goals/<goal_id>/notes', methods=['POST'])
def add_goal_note(goal_id):
    """Aggiunge una nota a un goal esistente"""
    try:
        data = request.get_json()
        note = data.get('note')
        note_source = data.get('note_source', 'frontend')
        
        if not note:
            logger.warning("POST goal note called without note")
            return jsonify({"error": "note è obbligatorio"}), 400
        
        logger.info(f"📝 Adding note to goal: {goal_id}")
        
        # Prepara il payload per l'update
        update_payload = {
            'goal_id': goal_id,
            'note': note,
            'note_source': note_source
        }
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=GOAL_UPDATE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(update_payload)
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
        logger.error(f"Error adding note to goal: {str(e)}")
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
        tipo = request.args.get('tipo', '')
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
        if tipo:
            payload['tipo'] = tipo
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


# ========================================
# KNOWLEDGE BASE API ENDPOINTS
# ========================================

@app.route('/api/kb', methods=['GET'])
def get_kb_documents():
    """Recupera tutti i documenti della Knowledge Base"""
    try:
        tipo = request.args.get('tipo')
        logger.info(f"📚 Getting KB documents, filter tipo: {tipo}")
        
        # Prepara l'evento per Lambda
        event_payload = {
            'queryStringParameters': {}
        }
        
        if tipo:
            event_payload['queryStringParameters']['tipo'] = tipo
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=KB_GET_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(event_payload)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"Retrieved {body.get('count', 0)} KB documents")
            
            # Debug: mostra struttura dei documenti
            if body.get('documents'):
                logger.debug(f"📄 First document structure: {json.dumps(body['documents'][0], indent=2, default=str)}")
                # Mostra i campi disponibili nel primo documento
                logger.info(f"📋 Available fields in documents: {list(body['documents'][0].keys()) if body['documents'] else 'No documents'}")
            
            return jsonify(body), result.get('statusCode', 200)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting KB documents: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/kb', methods=['POST'])
def create_kb_document():
    """Carica un nuovo documento nella Knowledge Base - processa PDF, identifica goal, salva su Qdrant"""
    try:
        # Determina se è FormData o JSON
        is_form_data = request.content_type and 'multipart/form-data' in request.content_type
        
        # Ottieni la collection Qdrant selezionata
        if is_form_data:
            collection = request.form.get('collection', 'meetings_notes')
        else:
            collection = (request.get_json() or {}).get('collection', 'meetings_notes')
        
        logger.info(f"📚 Creating KB document with collection: {collection}, is_form_data: {is_form_data}")
        
        # Variabili per gestire il testo
        text_content = None
        tipo = None
        file_content = None
        filename = None
        
        # Check if file or form data
        if is_form_data:
            # Handle FormData (file o testo)
            file = request.files.get('data')
            tipo = request.form.get('type', 'meeting-notes')
            
            # Debug logging
            logger.info(f"📋 FormData keys - files: {list(request.files.keys())}, form: {list(request.form.keys())}")
            
            if file and file.filename:
                # File upload
                logger.info(f"📚 Uploading KB file: {file.filename}")
                filename = file.filename
                
                # Read file content
                file_content = file.read()
                
                # 1️⃣ ESTRAI TESTO DAL PDF
                if filename.lower().endswith('.pdf'):
                    try:
                        text_content = extract_text_from_pdf(file_content)
                        logger.info(f"✅ PDF text extracted successfully")
                    except Exception as pdf_error:
                        logger.error(f"❌ Failed to extract PDF text: {pdf_error}")
                        return jsonify({"error": f"Failed to extract PDF text: {str(pdf_error)}"}), 500
                else:
                    # Se non è PDF, prova a leggerlo come testo
                    try:
                        text_content = file_content.decode('utf-8')
                    except:
                        return jsonify({"error": "File must be PDF or text"}), 400
            else:
                # Testo inviato tramite FormData (senza file)
                text_content = request.form.get('data', '')
                logger.info(f"📚 Creating KB text document from FormData, text length: {len(text_content)}")
        else:
            # Handle JSON data
            data = request.get_json()
            tipo = data.get('type', 'meeting-notes')
            text_content = data.get('data', '')
            
            logger.info(f"📚 Creating KB text document from JSON")
        
        if not text_content:
            return jsonify({"error": "No text content provided"}), 400
        
        # 2️⃣ IDENTIFICA L'OBIETTIVO DAL TESTO
        goal_name = identify_goal_from_text(text_content)
        logger.info(f"🎯 Identified goal: {goal_name}")

        # 2.1️⃣ Estrai aggiornamenti dal testo e aggiorna il goal se presente
        project_updates = extract_project_updates_from_text(text_content)
        logger.info(f"🧩 Project updates extracted: {project_updates}")

        if goal_name and goal_name.lower() != "vuoto":
            update_goal_with_advancements(goal_name, project_updates)
        
        # Data odierna
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Tags di sistema
        storage_mode = 'parent-child'
        tags = {
            'is_parent': False,
            'storage_mode': storage_mode,
            'nome_obiettivo': goal_name,
            'data_odierna': today
        }
        logger.info(f"📌 System tags: {tags}")
        
        # 3️⃣ PREPARA PAYLOAD PER LAMBDA (DynamoDB + S3) - include tags
        import base64

        if file_content and filename:
            # Multipart con file
            encoder = MultipartEncoder(
                fields={
                    'data': (filename, file_content, 'application/pdf'),
                    'type': tipo,
                    'tags': json.dumps(tags)
                }
            )
        else:
            # Multipart con testo
            encoder = MultipartEncoder(
                fields={
                    'data': text_content,
                    'type': tipo,
                    'tags': json.dumps(tags)
                }
            )

        body_bytes = encoder.to_string()
        payload = {
            'body': base64.b64encode(body_bytes).decode('utf-8'),
            'isBase64Encoded': True,
            'headers': {
                'content-type': encoder.content_type
            }
        }
        
        # 4️⃣ Invoca Lambda (DynamoDB + S3)
        logger.info(f"📤 Lambda payload content-type: {payload['headers'].get('content-type')}")
        logger.info(f"📤 Lambda payload body preview (base64): {str(payload['body'])[:200]}")
        response = lambda_client.invoke(
            FunctionName=KB_POST_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        logger.info(f"📦 Lambda response statusCode: {result.get('statusCode')}, body preview: {str(result.get('body', ''))[:200]}")
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        lambda_success = False
        document_id = None
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            document_id = body.get('document_id')
            lambda_success = True
            logger.info(f"✅ KB document created in Lambda with ID: {document_id}")
        else:
            body = result
            document_id = body.get('document_id')
            lambda_success = True
        
        # 5️⃣ Chunking + salvataggio su Qdrant (parent-child)
        if not qdrant_manager:
            return jsonify({"error": "Qdrant not available"}), 503

        # Data odierna
        today = datetime.now().strftime("%Y-%m-%d")

        # Payload aggiuntivo fornito dal client
        if is_form_data:
            extra_payload = _parse_json_field(request.form.get('payload')) or _parse_json_field(request.form.get('metadata')) or {}
            chunk_size = int(request.form.get('chunk_size', 1000))
            chunk_overlap = int(request.form.get('chunk_overlap', 200))
            provided_chunks = _parse_json_field(request.form.get('chunks'))
            provided_embeddings = _parse_json_field(request.form.get('embeddings'))
        else:
            data_json = request.get_json() or {}
            extra_payload = data_json.get('payload') or data_json.get('metadata') or {}
            chunk_size = int(data_json.get('chunk_size', 1000))
            chunk_overlap = int(data_json.get('chunk_overlap', 200))
            provided_chunks = data_json.get('chunks')
            provided_embeddings = data_json.get('embeddings')

        if not isinstance(extra_payload, dict):
            extra_payload = {}

        # Prepara chunks
        chunks = []
        if isinstance(provided_chunks, list) and provided_chunks:
            # Usa chunks già forniti
            for idx, ch in enumerate(provided_chunks):
                if isinstance(ch, dict):
                    chunks.append({
                        'id': ch.get('id', idx),
                        'text': ch.get('text', ''),
                        'embedding': ch.get('embedding') or _simple_hash_embedding(ch.get('text', ''), QDRANT_VECTOR_SIZE),
                        'metadata': ch.get('metadata', {})
                    })
        else:
            # Chunking automatico dal testo
            text_chunks = chunk_text(text_content, chunk_size=chunk_size, overlap=chunk_overlap)
            for idx, ch_text in enumerate(text_chunks):
                if isinstance(provided_embeddings, list) and idx < len(provided_embeddings):
                    embedding = provided_embeddings[idx]
                else:
                    embedding = _simple_hash_embedding(ch_text, QDRANT_VECTOR_SIZE)
                chunks.append({
                    'id': idx,
                    'text': ch_text,
                    'embedding': embedding
                })

        # Metadata finale con tags di sistema (già generati sopra)
        metadata = {
            **tags,  # Includi i tags già generati: is_parent, storage_mode, nome_obiettivo, data_odierna
            **extra_payload
        }

        # Imposta temporaneamente la collection scelta dall'utente
        original_collection = qdrant_manager.collection_name
        qdrant_manager.collection_name = collection
        
        try:
            # Salva su Qdrant (parent-child mode)
            qdrant_manager.save_chunks(
                chunks,
                metadata,
                storage_mode=storage_mode,
                parent_text=text_content,
                vector_size=QDRANT_VECTOR_SIZE
            )
            logger.info(f"✅ Saved {len(chunks)} chunks to Qdrant collection '{collection}' (mode: {storage_mode}) with tags: {tags}")
        finally:
            # Ripristina la collection originale
            qdrant_manager.collection_name = original_collection
        
        # Ritorna successo con metadata aggiuntivi
        response_body = body.copy() if isinstance(body, dict) else {"result": body}
        response_body['goal_identified'] = goal_name
        response_body['date'] = today
        response_body['tags'] = tags
        response_body['document_id'] = document_id
        
        logger.info(f"🔵 Returning response with tags: {response_body.get('tags')}")
        logger.debug(f"Full response structure: {json.dumps({k: str(v)[:100] if not isinstance(v, (dict, list)) else '...' for k, v in response_body.items()}, indent=2)}")
        
        return jsonify(response_body), result.get('statusCode', 201)
        
    except Exception as e:
        logger.error(f"❌ Error creating KB document: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/kb/<document_id>', methods=['DELETE'])
def delete_kb_document(document_id):
    """Elimina un documento della Knowledge Base"""
    try:
        logger.info(f"📚 Deleting KB document: {document_id}")
        
        # Prepara l'evento per Lambda
        event_payload = {
            'pathParameters': {
                'document_id': document_id
            }
        }
        
        # Invoca Lambda
        response = lambda_client.invoke(
            FunctionName=KB_DELETE_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(event_payload)
        )
        
        # Leggi payload
        payload_bytes = response['Payload'].read()
        result = json.loads(payload_bytes)
        
        if response['StatusCode'] != 200:
            return jsonify({"error": "Lambda invocation failed"}), 500
        
        # Estrai body se presente (formato API Gateway)
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            logger.info(f"KB document deleted successfully")
            return jsonify(body), result.get('statusCode', 200)
        
        logger.info(f"KB document deleted successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.info(f"❌ Error deleting KB document: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


@app.route('/api/kb/search', methods=['POST'])
def search_kb_qdrant():
    """Cerca nella Knowledge Base usando Qdrant con filtri sul payload"""
    try:
        data = request.get_json()
        
        # Estrai parametri
        query_vector = data.get('query_vector')  # Vettore embedding della query
        filter_payload = data.get('filter', {})  # Filtri (es. {"nome_obiettivo": "Obiettivo1"})
        limit = data.get('limit', 10)
        
        if not query_vector:
            return jsonify({"error": "query_vector is required"}), 400
        
        logger.info(f"🔍 Searching Qdrant with filters: {filter_payload}")
        
        if not qdrant_manager:
            return jsonify({"error": "Qdrant not available"}), 503
        
        # Cerca su Qdrant usando il manager
        results = qdrant_manager.search(query_vector, filters=filter_payload, limit=limit)
        
        # Formatta risultati
        formatted_results = []
        for hit in results:
            formatted_results.append({
                'id': hit.id,
                'score': hit.score,
                'payload': hit.payload
            })
        
        logger.info(f"✅ Found {len(formatted_results)} results")
        return jsonify({
            'results': formatted_results,
            'count': len(formatted_results)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error searching KB: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore: {str(e)}"}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Personal Copilot Backend Server")
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

