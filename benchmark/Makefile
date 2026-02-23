BENCHMARK_SERVICES = benchmark-app k6-flood kafka kafka-init

cleanup:
	@echo "Cleaning up benchmark containers, keeping observability alive..."
	docker-compose stop $(BENCHMARK_SERVICES)
	docker-compose rm -f -v $(BENCHMARK_SERVICES)

raw:
	@$(MAKE) cleanup
	@echo "Starting Benchmark..."
	docker-compose --env-file ./envs/raw.env up -d --build


with-io:
	@$(MAKE) cleanup
	@echo "Starting Benchmark..."
	docker-compose --env-file ./envs/with-io.env up -d --build


with-resource-pool:
	@$(MAKE) cleanup
	@echo "Starting Benchmark..."
	docker-compose --env-file ./envs/with-resource-pool.env up -d --build