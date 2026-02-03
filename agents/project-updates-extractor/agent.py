"""
Agent per l'estrazione strutturata di aggiornamenti da testi narrativi di progetto.

Questo agent analizza testi di aggiornamento progetto ed estrae:
- ✅ Avanzamenti: progressi completati, milestone raggiunte
- 📝 Cose da fare: attività pianificate, task pendenti
- ⚠️ Punti di attenzione: rischi, problemi, blocchi

Input: testo narrativo di aggiornamento progetto
Output: JSON con tre liste (avanzamenti, cose_da_fare, punti_attenzione)
"""

from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp
from pydantic import BaseModel, Field
from typing import List
import json
import re

app = BedrockAgentCoreApp()

# Modello per la risposta strutturata
class ProjectUpdates(BaseModel):
    """Struttura degli aggiornamenti di progetto estratti."""
    avanzamenti: List[str] = Field(
        description="Lista degli avanzamenti completati: progressi, milestone raggiunte, task completati"
    )
    cose_da_fare: List[str] = Field(
        description="Lista delle cose da fare: attività pianificate, task pendenti, prossimi passi"
    )
    punti_attenzione: List[str] = Field(
        description="Lista dei punti di attenzione: rischi, problemi, blocchi, criticità da monitorare"
    )

system_prompt = """Sei un assistente specializzato nell'analisi di aggiornamenti di progetto.

Il tuo compito è leggere un testo narrativo di aggiornamento progetto ed estrarre in modo strutturato:

1. **✅ Avanzamenti**: progressi completati, milestone raggiunte, funzionalità rilasciate, problemi risolti
2. **📝 Cose da fare**: attività pianificate, task pendenti, prossimi passi, implementazioni future
3. **⚠️ Punti di attenzione**: rischi identificati, problemi aperti, blocchi, criticità da monitorare

REGOLE:
- Estrai SOLO informazioni presenti nel testo, non inventare nulla
- Sii conciso ma completo: ogni punto deve essere chiaro e auto-esplicativo
- Se non ci sono elementi per una categoria, restituisci una lista vuota per quella categoria
- Mantieni il contesto: chi fa cosa, quando, perché
- Usa linguaggio professionale ma comprensibile

OUTPUT FORMAT:
Restituisci un JSON con tre chiavi: avanzamenti, cose_da_fare, punti_attenzione
Ogni chiave contiene una lista di stringhe."""

@app.entrypoint
def invoke(payload):
    """Estrae aggiornamenti strutturati da testi narrativi di progetto"""
    
    text = payload.get("text", "")
    
    if not text:
        return {
            "error": "Nessun testo fornito",
            "payload_received": str(payload),
            "avanzamenti": [],
            "cose_da_fare": [],
            "punti_attenzione": []
        }
    
    # Usa il modello Bedrock tramite Agent per ottenere JSON strutturato
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        temperature=0.2,
        streaming=False
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt
    )

    result = agent(
        f"""{text}

Rispondi SOLO con JSON valido che rispetti lo schema con chiavi: avanzamenti, cose_da_fare, punti_attenzione."""
    )

    raw = result.message if hasattr(result, "message") else result
    raw_text = raw

    if isinstance(raw, dict):
        content = raw.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict) and "text" in first:
                raw_text = first["text"]
    elif not isinstance(raw, str):
        raw_text = str(raw)

    if isinstance(raw_text, str):
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```[a-zA-Z]*\n", "", raw_text)
            raw_text = re.sub(r"\n```$", "", raw_text)

    try:
        updates = ProjectUpdates.model_validate_json(raw_text)
    except Exception:
        try:
            updates = ProjectUpdates.model_validate(json.loads(raw_text))
        except Exception as e:
            return {
                "error": f"Risposta non valida: {str(e)}",
                "raw": raw,
                "avanzamenti": [],
                "cose_da_fare": [],
                "punti_attenzione": []
            }

    return updates.model_dump()

if __name__ == "__main__":
    app.run()

