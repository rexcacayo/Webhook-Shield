SHELL := /bin/bash

.PHONY: build build-local local-api deploy-local api-id api-url test-localstack test-sam-local queues dlq replay

# 1) Build robusto para pyenv: compila dentro del contenedor del runtime
build:
	rm -rf .aws-sam
	sam build --use-container

# (opcional) si quieres build sin contenedor (no recomendado con pyenv)
build-local:
	rm -rf .aws-sam
	sam build

# SAM local (NO LocalStack). Útil para pruebas rápidas.
local-api: build
	sam local start-api --port 3000

# Deploy a LocalStack
deploy-local: build
	@source scripts/localstack_env.sh && \
	sam deploy \
	  --stack-name webhook-shield \
	  --capabilities CAPABILITY_IAM \
	  --no-confirm-changeset \
	  --resolve-s3

# Obtener ApiId desde LocalStack (HTTP API)
api-id:
	@source scripts/localstack_env.sh && \
	aws --endpoint-url=$$AWS_ENDPOINT_URL apigatewayv2 get-apis

# Construir API_URL de LocalStack (requiere que exportes API_ID)
api-url:
	@echo 'Exporta API_ID y usa:'
	@echo 'export API_URL="http://localhost:4566/restapis/$$API_ID/$$default/_user_request_"'
	@echo 'echo $$API_URL'

# Test contra SAM local start-api
test-sam-local:
	./scripts/test_webhook.sh http://127.0.0.1:3000 stripe dev_stripe_secret

# Test contra LocalStack API Gateway (requiere API_URL ya exportada)
test-localstack:
	@if [ -z "$$API_URL" ]; then echo "Falta API_URL. Ejemplo:"; \
	  echo 'export API_URL="http://localhost:4566/restapis/<apiId>/$$default/_user_request_"'; \
	  exit 1; fi
	./scripts/test_webhook.sh "$$API_URL" stripe dev_stripe_secret

# Ver colas en LocalStack
queues:
	@source scripts/localstack_env.sh && \
	aws --endpoint-url=$$AWS_ENDPOINT_URL sqs list-queues

# Leer DLQ (requiere que pegues la URL que te salga en list-queues)
dlq:
	@echo "Usa: aws --endpoint-url=$$AWS_ENDPOINT_URL sqs receive-message --queue-url <DLQ_URL> --max-number-of-messages 10"

# Replay (requiere API_URL)
replay:
	@if [ -z "$$API_URL" ]; then echo "Falta API_URL (ver target test-localstack)"; exit 1; fi
	curl -s -X POST "$$API_URL/replay/any" | jq .
