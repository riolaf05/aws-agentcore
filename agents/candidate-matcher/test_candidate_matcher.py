"""
Test script per l'agente Candidate Matcher

Testa il matching tra candidati e needs usando il tool find_matching_needs
"""

import json
from agent import invoke

# Test Case 1: Input minimo (solo ruolo obbligatorio)
print("=" * 80)
print("TEST 1: Input Minimo (solo current_role)")
print("=" * 80)

payload_1 = {
    "prompt": "Trova i migliori needs per un Senior Python Developer"
}

response_1 = invoke(payload_1)
print(f"Risposta:\n{response_1}\n")

# Test Case 2: Input completo con tutte le informazioni
print("=" * 80)
print("TEST 2: Input Completo")
print("=" * 80)

payload_2 = {
    "prompt": """
    Trova i migliori needs per un candidato con queste caratteristiche:
    - Ruolo: Senior Full Stack Developer
    - Esperienza: 7 anni
    - Provincia: Milano (MI)
    - Tecnologie: Python, React, AWS, Docker, PostgreSQL
    - Hard Skills: API REST Design, Microservices, CI/CD
    - Soft Skills: Team Leadership, Problem Solving
    - Lingue: Italiano madrelingua, Inglese C1, Spagnolo B2
    """
}

response_2 = invoke(payload_2)
print(f"Risposta:\n{response_2}\n")

# Test Case 3: Data Scientist con focus su ML
print("=" * 80)
print("TEST 3: Data Scientist")
print("=" * 80)

payload_3 = {
    "prompt": """
    Trova needs per un Data Scientist con:
    - 3 anni di esperienza
    - Competenze: Python, TensorFlow, Pandas, SQL
    - Hard Skills: Machine Learning, Deep Learning, Data Visualization
    - Lingue: Inglese C1
    - Provincia: Roma
    """
}

response_3 = invoke(payload_3)
print(f"Risposta:\n{response_3}\n")

# Test Case 4: Conversazione interattiva (l'agente chiede informazioni)
print("=" * 80)
print("TEST 4: Conversazione Guidata")
print("=" * 80)

payload_4 = {
    "prompt": "Ciao, vorrei trovare needs per un candidato"
}

response_4 = invoke(payload_4)
print(f"Risposta:\n{response_4}\n")

print("=" * 80)
print("Test completati!")
print("=" * 80)
