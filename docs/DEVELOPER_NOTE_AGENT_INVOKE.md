# Developer Note: Agent Invoke Lambda

Questa nota descrive l’implementazione della Lambda che invoca un AgentCore Runtime e i permessi necessari.

## 📌 Scopo

La Lambda riceve una stringa (`text`/`prompt`) via API Gateway e invoca l’agent runtime configurato in `AGENT_RUNTIME_ARN` come se fosse un `agentcore invoke`.

## ✅ Implementazione (Python)

Riferimento: [lambdas/agent-invoke/agent_invoke.py](../lambdas/agent-invoke/agent_invoke.py)

```python
import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN", "").strip()

bedrock_client = boto3.client("bedrock-agentcore")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        payload = _extract_payload(event)
        text = payload.get("text") or payload.get("prompt") or payload.get("input")
        session_id = payload.get("session_id") or str(uuid.uuid4())

        if not text or not str(text).strip():
            return _response(400, {"error": "Missing text", "message": "Provide 'text' (or 'prompt') in the request"})

        if not AGENT_RUNTIME_ARN:
            return _response(500, {"error": "Missing agent ARN", "message": "Set AGENT_RUNTIME_ARN env var"})

        agent_payload = {
            "prompt": str(text),
            "agent_arn": AGENT_RUNTIME_ARN,
        }

        response = bedrock_client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=json.dumps(agent_payload).encode("utf-8"),
        )

        result = _parse_agent_response(response)
        return _response(200, {"result": result, "session_id": session_id})

    except Exception as exc:
        logger.error("Unexpected error", exc_info=True)
        return _response(500, {"error": "Internal server error", "message": str(exc)})
```

## 🔐 Permessi IAM necessari

La role della Lambda deve poter invocare l’AgentCore Runtime:

```json
{
  "Effect": "Allow",
  "Action": ["bedrock-agentcore:InvokeAgentRuntime"],
  "Resource": [
    "arn:aws:bedrock-agentcore:REGION:ACCOUNT:runtime/<AGENT_ID>",
    "arn:aws:bedrock-agentcore:REGION:ACCOUNT:runtime/<AGENT_ID>/runtime-endpoint/*"
  ]
}
```

Nel CDK la policy viene aggiunta alla role della Lambda in modo automatico.

## ⚙️ Variabili d’ambiente

- `AGENT_RUNTIME_ARN`: ARN dell’agent runtime target (obbligatorio).
- `AGENT_INVOKE_API_KEY`: chiave API usata dal gateway (solo per il client).
- `ENABLE_AGENT_INVOKE_API`: abilita/disabilita la POST (risponde 503 se `false`).

## 🧪 Esempio di input

```json
{
  "text": "Cerca una posizione lavorativa per un professionista senior..."
}
```

## 🧭 Note operative

- In caso di errori CORS, verificare che il preflight `OPTIONS` risponda con i header corretti.
- Se `AGENT_RUNTIME_ARN` è vuoto, la Lambda risponde 500 con errore esplicito.
