Guía rápida para probar SafeMarket Pocket SDK y backend localmente

Resumen:
- Ejecutar backend en modo `testing` (usa SQLite in-memory) para evitar DB real.
- Probar SDK embebido (local) y remoto (llamadas a `/sdk/score`) desde ejemplos y tests.

1) Dependencias

    pip install -r requirements.txt

2) Ejecutar backend en modo testing (in-memory DB)

    set ENVIRONMENT=testing
    python -m uvicorn main:app --reload

   - El flag `ENVIRONMENT=testing` hace que el backend use SQLite in-memory y no intente conectarse a Postgres.

3) Probar SDK embebido (local)

    python -m safemarket_pocket_sdk.examples.clq_integration_example

4) Probar SDK en modo remoto (usa backend en 127.0.0.1:8000)

    # Asegúrate de que backend esté corriendo (ver paso 2)
    python -m safemarket_pocket_sdk.examples.clq_integration_example

5) Ejecutar tests (TestClient + pruebas locales)

    cd backend
    set ENVIRONMENT=testing
    pytest -q

6) Simulaciones sin BD

- Usa `safemarket_pocket_sdk` en modo local para generar decisiones automáticamente.
- Para probar el flujo remoto sin DB, ejecuta backend en `ENVIRONMENT=testing` y usa los tests que hacen POST a `/sdk/score`.

7) Notas útiles

- Variables importantes en cliente/CLQ app:
  - `USE_REMOTE_API` (True/False)
  - `API_URL` (ej: http://127.0.0.1:8000)
  - `API_KEY` (X-API-KEY header)
