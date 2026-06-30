# Repository instructions

Do not introduce environment-variable feature toggles for request routing. This service uses `config/routes.yaml` as the source of truth for routing behavior.

Existing implementation to inspect: `src/existing_service.py`.
