"""
Test locale per il Researcher Agent.
Esegui: python test_researcher.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import invoke

def test_researcher():
    """Testa il researcher con diverse query di ricerca"""
    
    test_cases = [
        {
            "name": "Ricerca Python",
            "prompt": "Cerca informazioni sulle novità di Python 3.13"
        },
        {
            "name": "Ricerca AWS",
            "prompt": "Quali sono le ultime funzionalità di AWS Bedrock?"
        },
        {
            "name": "Ricerca locale Italia",
            "prompt": "Qual è il meteo previsto per Roma questa settimana?"
        },
        {
            "name": "Ricerca tecnologia",
            "prompt": "Cerca articoli recenti sull'intelligenza artificiale generativa"
        }
    ]
    
    print("=" * 80)
    print("TEST RESEARCHER AGENT")
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
    test_researcher()
