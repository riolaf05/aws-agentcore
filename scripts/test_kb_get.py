import json
import boto3

lambda_client = boto3.client('lambda', region_name='us-east-1')

KB_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-KBGet"

event_payload = {
    'queryStringParameters': {}
}

print("Invocando Lambda KB GET...")
response = lambda_client.invoke(
    FunctionName=KB_GET_LAMBDA_ARN,
    InvocationType='RequestResponse',
    Payload=json.dumps(event_payload)
)

payload_bytes = response['Payload'].read()
result = json.loads(payload_bytes)

print("\n=== Lambda Response ===")
print(json.dumps(result, indent=2, default=str))

if 'body' in result:
    body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
    print("\n=== Parsed Body ===")
    print(json.dumps(body, indent=2, default=str))
    
    if body.get('documents'):
        print(f"\n=== First Document ===")
        print(json.dumps(body['documents'][0], indent=2, default=str))
        print(f"\n=== Available Fields ===")
        print(list(body['documents'][0].keys()))
