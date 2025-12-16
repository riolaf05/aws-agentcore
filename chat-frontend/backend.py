"""
Backend proxy per connettere il frontend chat all'orchestrator deployato su AWS.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import logging

app = Flask(__name__)
CORS(app)  # Abilita CORS per il frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione AWS
ORCHESTRATOR_ARN = "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/orchestrator-HR2F4m7QCY"
REGION = "us-east-1"    

# Client AWS
bedrock_client = boto3.client('bedrock-agentcore', region_name=REGION)


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


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Orchestrator Proxy Server")
    print("=" * 60)
    print(f"Orchestrator ARN: {ORCHESTRATOR_ARN}")
    print(f"Region: {REGION}")
    print(f"Server: http://localhost:5000")
    print("=" * 60)
    print("\nAGGIORNA 'ORCHESTRATOR_ARN' con il tuo ARN prima di avviare!")
    print("Trova l'ARN con: agentcore list (se disponibile)")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
