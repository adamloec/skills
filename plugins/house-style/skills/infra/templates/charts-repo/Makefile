COMPOSE := docker compose -f local/docker-compose.yml
# Keep in step with the loop in .github/workflows/chart-publish.yml.
CHARTS := {{app}}

.PHONY: up up-dev down logs ps setup helm-deps helm-lint helm-template

up:
	$(COMPOSE) up -d --build

up-dev:
	$(COMPOSE) --profile dev up -d --build

down:
	$(COMPOSE) --profile '*' down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

setup:
	./scripts/setup-local.sh

helm-deps:
	@for c in $(CHARTS); do helm dependency update charts/$$c/; done

helm-lint:
	@for c in $(CHARTS); do helm lint charts/$$c/; done

helm-template:
	helm template {{app}} charts/{{app}}/
