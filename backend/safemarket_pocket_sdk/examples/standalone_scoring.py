"""
SafeMarket Pocket SDK - Ejemplo: Scoring Standalone
======================================================

Ejemplo básico de scoring de transacciones sin dependencias externas.

Este es el caso más simple: usar SafeMarket directamente en el código
de un aplicativo tercero sin llamar a API remota.
"""

from safemarket_pocket_sdk.integration import SafeMarketAdapter
from safemarket_pocket_sdk.core import Transaction


def main():
    """
    Ejemplo completo de scoring standalone.
    """
    
    print("\\n🔐 SafeMarket Pocket SDK - Ejemplo Standalone\\n")
    
    # 1. Crear adaptador
    print("[1] Inicializando SafeMarket Adapter...")
    adapter = SafeMarketAdapter()
    print("    ✅ Adaptador listo\\n")
    
    # 2. Configurar datos históricos (idealmente de BD)
    print("[2] Configurando datos históricos...")
    adapter.set_buyer_data(
        buyer_id="buyer_123",
        tx_count=50,
        avg_amount=500.0,
        is_new=False
    )
    
    adapter.set_buyer_data(
        buyer_id="buyer_new",
        tx_count=0,
        avg_amount=0,
        is_new=True
    )
    
    adapter.set_seller_data(
        seller_id="seller_456",
        tx_count=100,
        avg_amount=750.0
    )
    print("    ✅ Datos configurados\\n")
    
    # 3. Crear transacciones de ejemplo
    print("[3] Creando transacciones de prueba...\\n")
    
    transactions = [
        Transaction(
            id="tx_001",
            amount=500.0,
            currency="USD",
            buyer_id="buyer_123",
            seller_id="seller_456",
            category="electronics",
            payment_method="credit_card",
            description="iPhone 15 Pro"
        ),
        Transaction(
            id="tx_002",
            amount=5000.0,  # Monto alto
            currency="USD",
            buyer_id="buyer_new",  # Buyer nuevo
            seller_id="seller_456",
            category="electronics",
            payment_method="credit_card",
            description="Gaming PC",
            buyer_country="US",
            seller_country="CN",  # Country mismatch
        ),
        Transaction(
            id="tx_003",
            amount=1500.0,
            currency="COP",
            buyer_id="buyer_123",
            seller_id="seller_456",
            category="digital_services",
            payment_method="bank_transfer",
            description="Software license"
        ),
    ]
    
    # 4. Realizar scoring
    print("[4] Realizando scoring...\\n")
    print("-" * 80)
    
    for tx in transactions:
        result = adapter.validate_transaction(tx)
        
        print(f"\\nTransacción: {tx.id}")
        print(f"  Monto: {tx.amount} {tx.currency}")
        print(f"  Buyer: {tx.buyer_id} | Seller: {tx.seller_id}")
        print(f"  ---")
        print(f"  📊 Score: {result['score']:.0f}/100")
        print(f"  ⚠️  Risk Level: {result['risk_level']}")
        print(f"  ✔️  Decision: {result['decision']}")
        print(f"  🎯 Confianza: {result['confidence']:.0%}")
        print(f"  💡 Razón: {result['reason']}")
        print(f"  🚩 Factores de Riesgo: {', '.join(result['risk_factors']) if result['risk_factors'] else 'Ninguno'}")
    
    print(f"\\n{'-' * 80}\\n")
    
    # 5. Simular feedback humano
    print("[5] Registrando feedback...\\n")
    
    adapter.submit_feedback(
        transaction_id="tx_001",
        label="LEGITIMATE",
        reviewer_id="reviewer_john",
        notes="Cliente confirmó compra"
    )
    
    adapter.submit_feedback(
        transaction_id="tx_002",
        label="FRAUD",
        reviewer_id="reviewer_maria",
        notes="Buyer denies transaction, card was stolen"
    )
    
    print("    ✅ Feedback registrado\\n")
    
    # 6. Ver salud del modelo
    print("[6] Salud del modelo...\\n")
    health = adapter.get_model_health()
    print(f"    Versión: {health['model_version']}")
    print(f"    Reglas configuradas: {health['rules_count']}")
    print(f"    Feedbacks registrados: {health['feedback_count']}\\n")
    
    # 7. Ver log de feedback
    print("[7] Log de feedback...\\n")
    feedback_log = adapter.get_feedback_log()
    for feedback in feedback_log:
        print(f"    • TX {feedback['transaction_id']}: {feedback['label']} por {feedback['reviewer_id']}")
    
    print(f"\\n✨ Ejemplo completado\\n")


if __name__ == "__main__":
    main()
