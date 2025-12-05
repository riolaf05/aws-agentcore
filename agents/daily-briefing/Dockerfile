# Daily Briefing Agent - ARM64 per AWS Lambda/AgentCore Runtime
FROM public.ecr.aws/lambda/python:3.11-arm64

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy agent code
COPY agent.py ${LAMBDA_TASK_ROOT}/

# Set entrypoint
CMD ["agent.invoke"]
