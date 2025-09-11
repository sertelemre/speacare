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
	# This will be configured to run pytest for the api
	# and playwright for the web app.

# ==============================================================================
# DATABASE
# ==============================================================================

migrate:
	@echo "Running database migrations..."
	# This will be configured to run Django migrations.
