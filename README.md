# Agent Core Starter Template


1. Initialize the project
```
  uv sync
```

1. Synth Infrastructure
```
  AWS_PROFILE=<your_profile> cdk synth > template.yaml
```

2. Deploy Infrastructure
```
  AWS_PROFILE=<your_profile> cdk deploy --template-file template.yaml
```


3. Configure the bedrock agent core (This will generate a bedrock agent core configuration file)
```
  AWS_PROFILE=<your_profile> agentcore configure
```

Request URL 
```
export TOKEN=$(aws cognito-idp initiate-auth \
    --client-id "$CLIENT_ID" \
    --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters USERNAME='testuser',PASSWORD='PASSWORD' \
    --region us-east-1 | jq -r '.AuthenticationResult.AccessToken')
```

Invoke 
```
  export PAYLOAD='{"prompt": "hello what is 1+1?"}'
  export BEDROCK_AGENT_CORE_ENDPOINT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com"
  export AGENT_ARN="<agent_aren>"
  curl -v -X POST "${BEDROCK_AGENT_CORE_ENDPOINT_URL}/runtimes/${AGENT_ARN}/invocations?qualifier=DEFAULT" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Amzn-Trace-Id: your-trace-id" \
  -H "Content-Type: application/json" \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: <fake_session_id_101191191292929292j2jdjjd292929292929292>" \
  -d "${PAYLOAD}"
```
