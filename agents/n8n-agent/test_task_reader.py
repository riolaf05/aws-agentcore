"""
Test locale per il Task Reader Agent.
Esegui: python test_task_reader.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import invoke

def test_task_reader():
    """Testa il task reader con diverse query"""
    
    test_cases = [
        {
            "name": "Tutti i task",
            "prompt": "Mostrami tutti i task"
        },
        {
            "name": "Task con priorità alta",
            "prompt": "Dammi i task con priorità alta"
        },
        {
            "name": "Task completati",
            "prompt": "Quali task sono stati completati?"
        },
        {
            "name": "Task in scadenza",
            "prompt": "Mostrami i task che scadono questa settimana"
        }
    ]
    
    print("=" * 80)
    print("TEST TASK READER AGENT")
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
    test_task_reader()
