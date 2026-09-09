.PHONY: lab test compose-config fmt
DATA ?= $(CURDIR)/data

lab:
	MINTRANET_DATA_DIR=$(DATA) MINTRANET_ALLOW_DEV_AUTH=true \
		PYTHONPATH=api python3 -m uvicorn app.main:app --app-dir api --host 127.0.0.1 --port 8081

test:
	MINTRANET_ALLOW_DEV_AUTH=true PYTHONPATH=api python3 tests/test_api.py

compose-config:
	docker compose config >/dev/null
