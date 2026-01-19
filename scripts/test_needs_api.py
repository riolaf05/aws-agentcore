"""
Script per testare il deployment della Needs API
"""

import json
import subprocess
import sys
import os
from urllib.parse import quote

def run_command(cmd, description=""):
    """Esegui un comando AWS CLI"""
    print(f"\n📝 {description}")
    print(f"   $ {cmd}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success")
            if result.stdout:
                print(result.stdout[:500])  # Limita l'output
            return True
        else:
            print(f"❌ Error")
            if result.stderr:
                print(result.stderr[:500])
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_lambda_function():
    """Testa la Lambda direttamente"""
    print("\n" + "=" * 80)
    print("⚡ Testing Lambda Function")
    print("=" * 80)
    
    LAMBDA_NAME = "mg-matchguru-needs-search-dev"
    
    # Test 1: List all needs
    payload = {
        "rawPath": "/needs",
        "requestContext": {"http": {"method": "GET"}}
    }
    
    cmd = f"""aws lambda invoke \\
        --function-name {LAMBDA_NAME} \\
        --payload '{json.dumps(payload)}' \\
        response.json 2>&1 && cat response.json"""
    
    run_command(cmd, "Test 1: GET /needs (List all)")
    
    # Test 2: Search by ID
    payload = {
        "rawPath": "/needs/test-id",
        "requestContext": {"http": {"method": "GET"}}
    }
    
    cmd = f"""aws lambda invoke \\
        --function-name {LAMBDA_NAME} \\
        --payload '{json.dumps(payload)}' \\
        response.json 2>&1 && cat response.json"""
    
    run_command(cmd, "Test 2: GET /needs/{{id}}")
    
    # Test 3: Search by keyword
    payload = {
        "rawPath": "/search/Python",
        "requestContext": {"http": {"method": "GET"}}
    }
    
    cmd = f"""aws lambda invoke \\
        --function-name {LAMBDA_NAME} \\
        --payload '{json.dumps(payload)}' \\
        response.json 2>&1 && cat response.json"""
    
    run_command(cmd, "Test 3: GET /search/{{query}}")

def test_api_gateway():
    """Testa API Gateway se presente"""
    print("\n" + "=" * 80)
    print("🌐 Testing API Gateway")
    print("=" * 80)
    
    # Trova API Gateway per needs-api
    cmd = "aws apigatewayv2 get-apis --query 'Items[?Name==`needs-api`].[ApiId,ApiEndpoint]' --output text"
    
    print(f"\n📝 Fetching API Gateway info")
    print(f"   $ {cmd}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            api_id, api_endpoint = result.stdout.strip().split()
            print(f"✅ API Found: {api_id}")
            print(f"   Endpoint: {api_endpoint}")
            
            # Test endpoint
            test_url = f"{api_endpoint}/prod/needs"
            cmd = f"curl -s '{test_url}' -H 'Content-Type: application/json' | jq . 2>/dev/null || echo 'Could not reach endpoint'"
            
            print(f"\n📝 Testing API Endpoint")
            print(f"   URL: {test_url}")
            print("-" * 80)
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(result.stdout)
        else:
            print("⚠️  API Gateway non trovato")
    except Exception as e:
        print(f"❌ Exception: {e}")

def check_lambda_configuration():
    """Verifica la configurazione della Lambda"""
    print("\n" + "=" * 80)
    print("⚙️  Checking Lambda Configuration")
    print("=" * 80)
    
    cmd = "aws lambda get-function-configuration --function-name mg-matchguru-needs-search-dev"
    
    print(f"\n📝 Lambda Configuration")
    print(f"   $ {cmd}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            config = json.loads(result.stdout)
            print(f"✅ Lambda Configuration:")
            print(f"   Runtime: {config.get('Runtime')}")
            print(f"   Memory: {config.get('MemorySize')} MB")
            print(f"   Timeout: {config.get('Timeout')} seconds")
            print(f"   Handler: {config.get('Handler')}")
            print(f"\n   Environment Variables:")
            for key, value in config.get('Environment', {}).get('Variables', {}).items():
                if key.startswith('MONGODB'):
                    masked = value[:10] + "..." if len(value) > 10 else value
                    print(f"      {key}: {masked}")
                else:
                    print(f"      {key}: {value}")
        else:
            print(f"❌ Error: Lambda not found")
    except Exception as e:
        print(f"❌ Exception: {e}")

def check_iam_permissions():
    """Verifica i permessi IAM"""
    print("\n" + "=" * 80)
    print("🔐 Checking IAM Permissions")
    print("=" * 80)
    
    # Check Lambda role
    cmd = "aws lambda get-function --function-name mg-matchguru-needs-search-dev --query 'Configuration.Role' --output text 2>/dev/null | head -c 100 || echo 'Could not retrieve role'"
    
    print(f"\n📝 Lambda Execution Role")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout[:500])
    except Exception as e:
        print(f"⚠️  Could not verify: {e}")

def check_cloudwatch_logs():
    """Verifica i log CloudWatch"""
    print("\n" + "=" * 80)
    print("📋 Checking CloudWatch Logs")
    print("=" * 80)
    
    cmd = """aws logs describe-log-groups \\
        --log-group-name-prefix /aws/lambda/mg-matchguru \\
        --query 'logGroups[?contains(logGroupName, `mg-matchguru-needs-search-dev`)].logGroupName' \\
        --output text | head -c 100"""
    
    print(f"\n📝 Recent Logs")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        log_group = result.stdout.strip()
        
        if log_group and log_group != "None":
            cmd = f"""aws logs tail {log_group} --follow --max-items 20"""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if result.stdout:
                print(result.stdout[:1000])
            else:
                print("✅ Log group exists (no recent logs)")
        else:
            print("⚠️  No log group found yet (Lambda may not have been invoked)")
    except subprocess.TimeoutExpired:
        print("✅ Log group exists")
    except Exception as e:
        print(f"⚠️  {e}")

def check_gateway():
    """Verifica il Gateway MCP"""
    print("\n" + "=" * 80)
    print("🌐 Checking Gateway MCP")
    print("=" * 80)
    
    cmd = "agentcore gateway list-mcp-gateways --region us-east-1 --query 'Gateways[?contains(Name, `matchguru`)][GatewayArn,Status]' --output text 2>/dev/null || echo 'Gateway not found or AgentCore CLI not available'"
    
    print(f"\n📝 Gateway Status")
    print(f"   $ {cmd}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout if result.stdout.strip() else "⚠️  Gateway not yet created")
    except Exception as e:
        print(f"⚠️  {e}")

def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "🔍 NEEDS API DEPLOYMENT TEST" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Check if AWS CLI is available
    try:
        subprocess.run("aws --version", shell=True, capture_output=True, check=True)
    except:
        print("\n❌ AWS CLI not found. Please install AWS CLI.")
        sys.exit(1)
    
    # Run tests
    check_lambda_configuration()
    test_lambda_function()
    check_iam_permissions()
    check_cloudwatch_logs()
    check_api_gateway()
    check_gateway()
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ Test Complete")
    print("=" * 80)
    print("""
Next steps:

1. If Lambda tests failed:
   - Check MongoDB connectivity
   - Verify environment variables
   - Check CloudWatch logs: aws logs tail /aws/lambda/needs-api --follow

2. If API Gateway tests failed:
   - Create API Gateway via docs/NEEDS_GATEWAY_DEPLOYMENT.md
   - Add permission for API Gateway to invoke Lambda

3. If Gateway MCP is not found:
   - Run: agentcore gateway create-mcp-gateway --name needs-api-gateway --region us-east-1
   - Save the Cognito credentials for the agent

4. Test the agent:
   - cd agents/needs-reader
   - Update credentials in agent.py
   - python agent.py
    """)
    print("=" * 80)

if __name__ == "__main__":
    main()
