unit-test:
	python -m pytest --ignore=tests/integration

integration-test:
	docker-compose -f ./tests/integration/docker-compose.yaml up -d
	@echo "Waiting for services to become healthy..."
	@docker-compose -f ./tests/integration/docker-compose.yaml exec -T redpanda \
		sh -c 'until curl -sf http://localhost:9644/v1/status/ready; do sleep 1; done'
	@docker-compose -f ./tests/integration/docker-compose.yaml exec -T rabbitmq \
		sh -c 'until rabbitmqctl status > /dev/null 2>&1; do sleep 1; done'
	python -m pytest ./tests/integration
	docker-compose -f ./tests/integration/docker-compose.yaml down --volumes

test: unit-test integration-test