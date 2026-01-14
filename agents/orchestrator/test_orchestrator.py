"""
Test locale per l'Orchestrator Agent.
Esegui: python test_orchestrator.py
"""

import json
import sys
import os

# Aggiungi directory parent al path per import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import invoke

def test_orchestrator():
    """Testa l'orchestrator con diverse richieste"""
    
    test_cases = [
        {
            "name": "Creazione task",
            "prompt": "Crea un task per comprare il pane domani"
        },
        {
            "name": "Lettura task",
            "prompt": "Mostrami tutti i task con priorità alta"
        },
        {
            "name": "Ricerca + Task",
            "prompt": "Cerca informazioni sulla sicurezza in Python e crea un task per studiarle"
        },
        {
            "name": "Calcolo",
            "prompt": "Quanto fa 125 * 47?"
        },
        {
            "name": "Richiesta complessa",
            "prompt": "Cerca le ultime novità su AWS Bedrock, calcola quanti giorni mancano a Natale, e crea un task per preparare una presentazione"
        }
    ]
    
    print("=" * 80)
    print("TEST ORCHESTRATOR AGENT")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"TEST: {test['name']}")
        print(f"PROMPT: {test['prompt']}")
        print(f"{'='*80}\n")
        
        payload = {"prompt": test['prompt']}
        result = invoke(payload)
        
        print("RISULTATO:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()


if __name__ == "__main__":
    test_orchestrator()
