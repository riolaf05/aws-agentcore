"""
Test script per project-updates-extractor agent.
Invia un testo narrativo di aggiornamento progetto e verifica l'estrazione strutturata.
"""

import boto3
import json
import uuid
from datetime import datetime

# Configurazione
REGION = 'us-east-1'
AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/project_updates_extractor-4K01E4Fumo"

# Testo di test
TEST_TEXT = """
Nel corso dell'ultima settimana il team ha completato l'integrazione tra il modulo di 
gestione candidati e il sistema di shortlist, risolvendo i principali bug segnalati in 
fase di test. È stata inoltre rilasciata in ambiente di staging la nuova logica di 
gestione degli stati del candidato, che consente un tracciamento più accurato del ciclo 
di vita del processo di selezione.

Restano ancora da completare alcune attività, in particolare l'allineamento dei permessi 
tra recruiter e referenti aziendali e l'implementazione del logout automatico in caso di 
token scaduto. Queste attività sono pianificate per la prossima settimana.

Durante i test è emerso un potenziale problema legato alla visibilità di alcuni candidati 
nel database: in alcuni casi i recruiter non riescono a trovare profili esistenti durante 
l'invio delle shortlist. Il team sta analizzando la causa e l'impatto del problema per 
evitare ripercussioni sugli utenti finali prima del rilascio in produzione.
"""

def test_extract_updates():
    """Test dell'agent project-updates-extractor."""
    
    print("🧪 Testing project-updates-extractor agent")
    print("=" * 70)
    
    # Client Bedrock AgentCore
    client = boto3.client('bedrock-agentcore', region_name=REGION)
    
    # Payload
    payload = {
        "text": TEST_TEXT
    }
    
    print(f"\n📤 Invocazione agent")
    print(f"📝 Testo da analizzare ({len(TEST_TEXT)} caratteri):")
    print(f"{TEST_TEXT[:200]}...\n")
    
    try:
        # Invoca agent con invoke_agent_runtime
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_ARN,
            runtimeSessionId=str(uuid.uuid4()),
            payload=json.dumps(payload).encode(),
            qualifier="DEFAULT"
        )
        
        print("✅ Agent invocato con successo!")
        
        # Leggi risposta
        content = []
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        result_text = ''.join(content)
        
        # Parse risultato
        result = json.loads(result_text)
        
        print("\n📊 RISULTATO:")
        print("=" * 70)
        
        # Avanzamenti
        print("\n✅ AVANZAMENTI:")
        if result.get('avanzamenti'):
            for i, item in enumerate(result['avanzamenti'], 1):
                print(f"  {i}. {item}")
        else:
            print("  (nessuno)")
        
        # Cose da fare
        print("\n📝 COSE DA FARE:")
        if result.get('cose_da_fare'):
            for i, item in enumerate(result['cose_da_fare'], 1):
                print(f"  {i}. {item}")
        else:
            print("  (nessuno)")
        
        # Punti di attenzione
        print("\n⚠️ PUNTI DI ATTENZIONE:")
        if result.get('punti_attenzione'):
            for i, item in enumerate(result['punti_attenzione'], 1):
                print(f"  {i}. {item}")
        else:
            print("  (nessuno)")
        
        print("\n" + "=" * 70)
        print("✅ Test completato con successo!")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERRORE durante l'invocazione: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_extract_updates()
    
    if result:
        print("\n💾 Risultato JSON completo:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
