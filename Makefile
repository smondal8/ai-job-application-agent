.PHONY: setup test run-backend run-frontend stop migrate clean

setup:
	./scripts/setup.sh

test:
	./scripts/test.sh

run-backend:
	./scripts/run_backend.sh

run-frontend:
	./scripts/run_frontend.sh

stop:
	./scripts/stop.sh

migrate:
	./scripts/migrate.sh

smoke-test-phase5:
	./scripts/smoke-test-phase5.sh

smoke-test-phase6:
	./scripts/smoke-test-phase6.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf frontend/dist
