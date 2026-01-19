#!/usr/bin/env python
"""
Script di setup rapido per la Short-Term Memory del Candidate Matcher Agent

Questo script:
1. Crea una memory resource con STM
2. Salva il Memory ID in un file .env
3. Fornisce i comandi per il deployment

Uso:
    python setup_memory.py
"""

import sys
import os

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("❌ Errore: bedrock-agentcore non è installato")
    print("Esegui: pip install bedrock-agentcore")
    sys.exit(1)

def setup_memory():
    """Setup della memory resource"""
    
    print("=" * 70)
    print("🧠 Bedrock AgentCore Memory Setup - Candidate Matcher")
    print("=" * 70)
    print()
    
    # Richiedi la regione
    region = input("📍 In quale regione AWS vuoi creare la memory? [us-east-1]: ").strip() or "us-east-1"
    
    # Richiedi l'account ID (opzionale)
    account_id = input("🔑 Inserisci il tuo AWS Account ID (opzionale): ").strip()
    
    # Costruisci l'ARN della role
    role_arn = None
    if account_id:
        # Usa la stessa role usata per il gateway
        role_arn = f"arn:aws:iam::{account_id}:role/MatchGuruAgentCoreExecutionRole"
        print(f"   Role ARN: {role_arn}")
    else:
        print("   ℹ️ Procedo senza role (userò le credenziali AWS CLI)")
    
    print()
    print("⏳ Creazione della memory resource...")
    print()
    
    try:
        client = MemoryClient(region_name=region)
        
        # Crea la memory (STM - Short-Term Memory)
        memory = client.create_memory_and_wait(
            name="candidate_matcher_stm",  # Usa underscore invece di trattini
            strategies=[],  # STM non ha bisogno di strategie di estrazione
            description="Short-Term Memory per l'intervista con candidati",
            event_expiry_days=7,  # Mantiene i dati per 7 giorni
            memory_execution_role_arn=role_arn,
            max_wait=300,
            poll_interval=5
        )
        
        memory_id = memory.get("id") or memory.get("memoryId")
        
        print("✅ Memory creata con successo!")
        print()
        print(f"   Memory ID: {memory_id}")
        print(f"   Region: {region}")
        print(f"   Status: {memory.get('status', 'ACTIVE')}")
        print()
        
        # Salva in .env
        env_file = ".env"
        env_content = f"MEMORY_ID={memory_id}\nAWS_REGION={region}\nACTOR_ID=candidate-matcher\n"
        
        with open(env_file, "w") as f:
            f.write(env_content)
        
        print(f"💾 Configurazione salvata in {env_file}")
        print()
        
        # Mostra i comandi next
        print("=" * 70)
        print("📋 PROSSIMI STEP")
        print("=" * 70)
        print()
        print("1️⃣  Carica le variabili di ambiente:")
        print()
        print("    # Windows PowerShell:")
        print(f'    $env:MEMORY_ID = "{memory_id}"')
        print(f'    $env:AWS_REGION = "{region}"')
        print(f'    $env:ACTOR_ID = "candidate-matcher"')
        print()
        print("    # Linux/macOS:")
        print(f'    export MEMORY_ID="{memory_id}"')
        print(f'    export AWS_REGION="{region}"')
        print(f'    export ACTOR_ID="candidate-matcher"')
        print()
        print("2️⃣  Deploy l'agente:")
        print("    cd agents/candidate-matcher")
        print("    agentcore launch")
        print()
        print("3️⃣  Testa la memory multi-turno:")
        print("    # Windows PowerShell:")
        print('    $SESSION_ID = "test-" + (Get-Date -UFormat %s)')
        print('    agentcore invoke "{\\"prompt\\":\\"Sono Marco\\",\\"session_id\\":\\"$SESSION_ID\\"}"')
        print('    agentcore invoke "{\\"prompt\\":\\"Come mi chiamo?\\",\\"session_id\\":\\"$SESSION_ID\\"}"')
        print()
        print("=" * 70)
        
        # Mostra i dettagli della memory
        print()
        print("📊 DETTAGLI DELLA MEMORY")
        print("=" * 70)
        print(f"Type: Short-Term Memory (STM)")
        print(f"Retention: 7 giorni")
        print(f"Strategies: Nessuna (solo storage)")
        print(f"Max Size: Illimitato")
        print()
        print("ℹ️  La STM mantiene la storia esatta della conversazione.")
        print("   Se vuoi memoria persistente cross-session, usa LTM.")
        print()
        
        return memory_id
        
    except Exception as e:
        print(f"❌ Errore durante la creazione della memory:")
        print(f"   {e}")
        print()
        print("Suggerimenti:")
        print("  - Verifica che aws cli sia configurata: aws configure")
        print("  - Verifica i permessi su bedrock-agentcore")
        print("  - Prova di nuovo con una regione diversa")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        memory_id = setup_memory()
        print("🎉 Setup completato!")
        print()
    except KeyboardInterrupt:
        print()
        print("❌ Setup annullato dall'utente")
        sys.exit(1)

if __name__ == "__main__":
    main()
