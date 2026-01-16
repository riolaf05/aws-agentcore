"""
Test suite per il Needs Reader Agent

Run con: python test_needs_reader.py
"""

import json
import sys
from pathlib import Path

# Aggiungi il path dell'agente al sys.path
AGENT_PATH = Path(__file__).parent.parent / 'needs-reader'
sys.path.insert(0, str(AGENT_PATH))

def test_basic_prompts():
    """Testa i prompt comuni"""
    test_prompts = [
        "Mostrami tutti i need disponibili",
        "Quali ruoli di sviluppatore sono disponibili?",
        "Cerca una posizione come Project Manager",
        "Quante opportunità ci sono a Milano?",
        "Mi serve uno sviluppatore React senior",
        "Quali aziende cercano data scientist?",
    ]
    
    print("=" * 60)
    print("🧪 Test Basic Prompts")
    print("=" * 60)
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        print("-" * 60)
        
        # Nel test reale, questo chiamerebbe l'agente
        print(f"✅ Ready to test with agent")
    
    print("\n" + "=" * 60)

def test_api_endpoints():
    """Testa gli endpoint della Lambda"""
    print("\n" + "=" * 60)
    print("🌐 Test API Endpoints")
    print("=" * 60)
    
    endpoints = [
        ("GET", "/needs", "List all needs", {}),
        ("GET", "/needs/12345", "Get need by ID", {"id": "12345"}),
        ("GET", "/search/Python", "Search by keyword", {"query": "Python"}),
    ]
    
    for method, endpoint, description, params in endpoints:
        print(f"\n{method} {endpoint}")
        print(f"Description: {description}")
        print(f"Params: {json.dumps(params, indent=2)}")
        print("-" * 60)
        print("Expected Response:")
        print("""
{
    "statusCode": 200,
    "body": {
        "status": "success",
        "count": <number>,
        "data": [...]
    }
}
        """)

def test_error_scenarios():
    """Testa gli scenari di errore"""
    print("\n" + "=" * 60)
    print("⚠️  Test Error Scenarios")
    print("=" * 60)
    
    error_cases = [
        ("Invalid endpoint", "/invalid", "Endpoint non trovato (404)"),
        ("Non-existent ID", "/needs/invalid-id-12345", "Need non trovato (404)"),
        ("MongoDB connection error", "MONGODB_HOST not set", "Errore connessione (500)"),
        ("Empty search query", "/search/", "No results (200)"),
    ]
    
    for case, input_val, expected in error_cases:
        print(f"\n❌ {case}")
        print(f"Input: {input_val}")
        print(f"Expected: {expected}")

def test_configuration():
    """Verifica la configurazione dell'agente"""
    print("\n" + "=" * 60)
    print("⚙️  Configuration Verification")
    print("=" * 60)
    
    import os
    
    config_vars = [
        "GATEWAY_CLIENT_ID",
        "GATEWAY_CLIENT_SECRET",
        "GATEWAY_TOKEN_ENDPOINT",
        "GATEWAY_MCP_URL",
    ]
    
    print("\nRequired environment variables:")
    for var in config_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    mongodb_vars = [
        "MONGODB_HOST",
        "MONGODB_PORT",
        "MONGODB_DB",
        "MONGODB_USER",
    ]
    
    print("\nMongoDB configuration:")
    for var in mongodb_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: NOT SET (using default)")

def test_example_responses():
    """Mostra esempi di response attese"""
    print("\n" + "=" * 60)
    print("📊 Example Responses")
    print("=" * 60)
    
    # Example: List all needs
    list_response = {
        "statusCode": 200,
        "body": json.dumps({
            "status": "success",
            "count": 10,
            "data": [
                {
                    "id": "1",
                    "title": "Senior Python Developer",
                    "description": "Cerchiamo uno sviluppatore Python senior con esperienza in microservizi",
                    "role": {"name": "Backend Developer"},
                    "company": "TechCorp",
                    "city": {"name": "Milano"},
                    "salary_min": 50000,
                    "salary_max": 70000,
                },
                {
                    "id": "2",
                    "title": "Project Manager",
                    "description": "Manager per progetti digitali innovativi",
                    "role": {"name": "Project Manager"},
                    "company": "Digital Agency",
                    "city": {"name": "Roma"},
                    "salary_min": 40000,
                    "salary_max": 55000,
                }
            ]
        }, ensure_ascii=False)
    }
    
    print("\n✅ GET /needs (Success)")
    print(json.dumps(json.loads(list_response['body']), indent=2, ensure_ascii=False))
    
    # Example: Get by ID
    by_id_response = {
        "statusCode": 200,
        "body": json.dumps({
            "status": "success",
            "data": {
                "id": "1",
                "title": "Senior Python Developer",
                "description": "Cerchiamo uno sviluppatore Python senior con esperienza in microservizi",
                "role": {"name": "Backend Developer"},
                "company": "TechCorp",
                "city": {"name": "Milano"},
                "salary_min": 50000,
                "salary_max": 70000,
                "required_skills": ["Python", "Docker", "Kubernetes", "PostgreSQL"],
                "experience_years": 5,
            }
        }, ensure_ascii=False)
    }
    
    print("\n✅ GET /needs/{id} (Success)")
    print(json.dumps(json.loads(by_id_response['body']), indent=2, ensure_ascii=False))
    
    # Example: Search
    search_response = {
        "statusCode": 200,
        "body": json.dumps({
            "status": "success",
            "query": "Python",
            "count": 5,
            "data": [
                {
                    "id": "1",
                    "title": "Senior Python Developer",
                    "company": "TechCorp",
                },
                {
                    "id": "3",
                    "title": "Python Data Scientist",
                    "company": "DataCorp",
                }
            ]
        }, ensure_ascii=False)
    }
    
    print("\n✅ GET /search/{query} (Success)")
    print(json.dumps(json.loads(search_response['body']), indent=2, ensure_ascii=False))
    
    # Example: Error
    error_response = {
        "statusCode": 404,
        "body": json.dumps({
            "status": "error",
            "message": "Need con ID 'invalid-id' non trovato"
        }, ensure_ascii=False)
    }
    
    print("\n❌ GET /needs/{invalid_id} (Error)")
    print(json.dumps(json.loads(error_response['body']), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "🧪 NEEDS READER AGENT TEST SUITE" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")
    
    test_configuration()
    test_basic_prompts()
    test_api_endpoints()
    test_error_scenarios()
    test_example_responses()
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Summary")
    print("=" * 60)
    print("""
Run these commands to test:

1. Test locally:
   cd agents/needs-reader
   python -m pytest test_needs_reader.py -v

2. Test with deployed agent:
   agentcore agent invoke \\
       --name needs-reader \\
       --payload '{"prompt": "Mostrami tutti i need"}'

3. Test Lambda directly:
   aws lambda invoke \\
       --function-name needs-api \\
       --payload '{"rawPath": "/needs", "requestContext": {"http": {"method": "GET"}}}' \\
       response.json
   cat response.json
    """)
    print("=" * 60)
