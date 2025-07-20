docker-up:
	docker-compose -f ./tests/integration/docker-compose.yaml up -d
	@echo "Waiting for services to become healthy..."
	@docker-compose -f ./tests/integration/docker-compose.yaml exec -T redpanda \
		sh -c 'until curl -sf http://localhost:9644/v1/status/ready; do sleep 1; done'
	@docker-compose -f ./tests/integration/docker-compose.yaml exec -T rabbitmq \
		sh -c 'until rabbitmqctl status > /dev/null 2>&1; do sleep 1; done'

docker-down:
	docker-compose -f ./tests/integration/docker-compose.yaml down --volumes

unit-test:
	python -m pytest --ignore=tests/integration

integration-test:
	$(MAKE) docker-up
	python -m pytest ./tests/integration
	$(MAKE) docker-down

test: unit-test integration-test

test-coverage:
	$(MAKE) docker-up
	python -m pytest --cov=dispytch
	$(MAKE) docker-down
	powershell -Command "if (Test-Path '.coverage') { Remove-Item '.coverage'}"
