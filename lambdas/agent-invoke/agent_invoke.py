"""
Lambda per invocare un AgentCore Runtime passando una stringa di input.
La scelta dell'agente avviene tramite variabile d'ambiente AGENT_RUNTIME_ARN.
"""

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


def _extract_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, dict):
        return {}

    body = event.get("body")
    if isinstance(body, str):
        body = body.strip()
        if not body:
            return event
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"text": body}

    if isinstance(body, dict):
        return body

    return event


def _parse_agent_response(response: Dict[str, Any]) -> Any:
    content_chunks = []
    if response.get("contentType") == "application/json":
        for chunk in response.get("response", []):
            content_chunks.append(chunk.decode("utf-8"))
        result_str = "".join(content_chunks)
        try:
            return json.loads(result_str)
        except Exception:
            return result_str

    for chunk in response.get("response", []):
        if isinstance(chunk, bytes):
            content_chunks.append(chunk.decode("utf-8"))
        else:
            content_chunks.append(str(chunk))

    return "".join(content_chunks).strip()


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
