.PHONY: up down logs test lint migrate migration format

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	docker compose run --rm --no-deps --entrypoint pytest backend
	cd frontend && npm test

lint:
	docker compose run --rm --no-deps --entrypoint ruff backend check app tests
	cd frontend && npm run lint

migrate:
	docker compose run --rm --no-deps --entrypoint alembic backend upgrade head

migration:
	docker compose run --rm --no-deps --entrypoint alembic backend revision --autogenerate -m "$(m)"

format:
	docker compose run --rm --no-deps --entrypoint ruff backend format app tests
