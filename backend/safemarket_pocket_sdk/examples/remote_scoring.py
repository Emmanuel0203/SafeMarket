"""Ejemplo de uso remoto del SafeMarket Pocket SDK.

Este ejemplo muestra cómo un aplicativo cliente puede usar el SDK de bolsillo
para enviar transacciones al backend robusto de SafeMarket para validación.
"""

from safemarket_pocket_sdk import create_adapter
from safemarket_pocket_sdk.core import Config, Transaction


def main():
    config = Config(
        API_URL="https://api.safemarket.local",
        API_KEY="sk_demo_12345",
        USE_REMOTE_API=True,
    )

    adapter = create_adapter(
        use_remote_api=True,
        config=config,
    )

    tx = Transaction(
        id="tx_remote_001",
        amount=1299.90,
        buyer_id="buyer_demo_001",
        seller_id="seller_demo_001",
        currency="USD",
        category="ecommerce",
        payment_method="credit_card",
        metadata={"platform": "mobile_app", "user_segment": "silver"}
    )

    result = adapter.validate_transaction(tx)
    print("Remote validation result:")
    print(result)


if __name__ == "__main__":
    main()
