.PHONY: dev down test migrate

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

dev:
	@echo "Starting development environment..."
	docker-compose up -d

down:
	@echo "Stopping development environment..."
	docker-compose down

# ==============================================================================
# TESTING
# ==============================================================================

test:
	@echo "Running tests..."
	cd apps/api && python3 -m pytest
	cd apps/web && npm run test

# ==============================================================================
# DATABASE
# ==============================================================================

migrate:
	@echo "Running database migrations..."
	cd apps/api && python3 manage.py makemigrations
	cd apps/api && python3 manage.py migrate

seed:
	@echo "Seeding database with initial data..."
	cd apps/api && python3 manage.py seed_data
