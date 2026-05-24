"""CLQ App integration examples for SafeMarket Pocket SDK.

Muestra dos formas de integrar el SDK:
 - Embebido localmente (modo "pocket" local)
 - Remoto vía API (llama al backend SafeMarket local)

Ejecutar:
    # Ejecutar backend en modo testing (usa SQLite in-memory):
    set ENVIRONMENT=testing
    python -m uvicorn main:app --reload

    # Luego en otra terminal ejecutar este ejemplo
    python -m safemarket_pocket_sdk.examples.clq_integration_example

Este archivo sólo simula transacciones y muestra respuestas.
"""

from safemarket_pocket_sdk import create_adapter
from safemarket_pocket_sdk.core import Transaction, Config


def run_local_example():
    print("--- Local SDK (embedded) example ---")
    adapter = create_adapter(use_remote_api=False)

    tx = Transaction(
        id="clq_tx_1",
        amount=1200.0,
        buyer_id="buyer_100",
        seller_id="seller_50",
        currency="USD",
        category="ecommerce",
    )

    result = adapter.validate_transaction(tx)
    print(result)


def run_remote_example():
    print("--- Remote SDK (calls local backend) example ---")
    cfg = Config(API_URL="http://127.0.0.1:8000", API_KEY="sm_demo_123", USE_REMOTE_API=True)
    adapter = create_adapter(use_remote_api=True, config=cfg)

    tx = Transaction(
        id="clq_tx_2",
        amount=75000.0,
        buyer_id="buyer_999",
        seller_id="seller_88",
        currency="USD",
        category="digital_services",
    )

    result = adapter.validate_transaction(tx)
    print(result)


if __name__ == "__main__":
    run_local_example()
    print("\n(ensure backend is running for remote example)")
    try:
        run_remote_example()
    except Exception as e:
        print(f"Remote example failed (is backend running?): {e}")
