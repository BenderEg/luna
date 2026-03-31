up-local:
	cp --update=none .env.example .env || true
	cp --update=none credentials.examlpe.yaml credentials.yaml || true
	docker compose -f docker-compose.yml up -d --build

down-local:
	docker compose -f docker-compose.yml down