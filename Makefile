.PHONY: validate generate

validate:
	uv run python -m scripts.validate

generate:
	uv run python -m scripts.generate $(APP)
