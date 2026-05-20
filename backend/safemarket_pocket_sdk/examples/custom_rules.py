\"\"\"
SafeMarket Pocket SDK - Ejemplo: Reglas Personalizadas
========================================================

Ejemplo de cómo crear reglas de negocio personalizadas para casos
específicos de cada integrador.

Las reglas se aplican después del modelo ML para ajustar el score
según políticas y restricciones locales.
\"\"\"

from safemarket_pocket_sdk.integration import SafeMarketAdapter
from safemarket_pocket_sdk.core import Transaction


def main():
    \"\"\"
    Ejemplo completo de reglas personalizadas.
    \"\"\"
    
    print(\"\\n⚙️  SafeMarket Pocket SDK - Reglas Personalizadas\\n\")
    
    # 1. Crear adaptador
    print(\"[1] Inicializando adaptador...\\n\")
    adapter = SafeMarketAdapter()
    
    # 2. Configurar datos históricos
    print(\"[2] Configurando datos...\\n\")
    
    adapter.set_buyer_data(
        buyer_id=\"buyer_trusted\",
        tx_count=500,
        avg_amount=1000,
        is_new=False
    )
    
    adapter.set_buyer_data(
        buyer_id=\"buyer_vip\",
        tx_count=1000,
        avg_amount=5000,
        is_new=False
    )
    
    adapter.set_buyer_data(
        buyer_id=\"buyer_new\",
        tx_count=0,
        avg_amount=0,
        is_new=True
    )
    
    # 3. Añadir reglas personalizadas
    print(\"[3] Configurando reglas personalizadas...\\n\")
    
    # Regla 1: Buyer de confianza (muchas transacciones)
    adapter.add_custom_rule(
        name=\"trusted_buyer_low_score\",
        condition=lambda f: f.buyer_transaction_count > 200,
        score_delta=-20,
        severity=\"LOW\",
        reason=\"Established buyer with good history\"
    )
    print(\"    ✅ Regla: trusted_buyer_low_score\")
    
    # Regla 2: Buyer nuevo + monto alto = riesgo
    adapter.add_custom_rule(
        name=\"new_buyer_high_amount\",
        condition=lambda f: f.buyer_is_new and f.amount > 2000,
        score_delta=+35,
        severity=\"HIGH\",
        reason=\"New buyer attempting high-value transaction\"
    )
    print(\"    ✅ Regla: new_buyer_high_amount\")
    
    # Regla 3: Velocidad muy alta
    adapter.add_custom_rule(
        name=\"extreme_velocity\",
        condition=lambda f: f.velocity_24h > 100,
        score_delta=+30,
        severity=\"HIGH\",
        reason=\"Extreme velocity: >100 transactions in 24h\"
    )
    print(\"    ✅ Regla: extreme_velocity\")
    
    # Regla 4: Monto repetido sospechosamente
    adapter.add_custom_rule(
        name=\"round_amount_pattern\",
        condition=lambda f: f.amount in [100, 500, 1000, 5000],
        score_delta=+10,
        severity=\"LOW\",
        reason=\"Suspiciously round transaction amount\"
    )
    print(\"    ✅ Regla: round_amount_pattern\")
    
    # Regla 5: Horario sospechoso (madrugada)
    adapter.add_custom_rule(
        name=\"suspicious_time_of_day\",
        condition=lambda f: f.time_of_day in [2, 3, 4, 5],
        score_delta=+15,
        severity=\"MEDIUM\",
        reason=\"Transaction during late night hours\"
    )
    print(\"    ✅ Regla: suspicious_time_of_day\")
    
    # Regla 6: Régimen especial (bloqueo crítico)
    adapter.add_custom_rule(
        name=\"blocked_payment_method\",
        condition=lambda f: f.extra_features.get('payment_method') == 'prepaid_card',
        score_delta=+50,
        severity=\"CRITICAL\",
        reason=\"Blocked payment method: prepaid cards not allowed\"
    )
    print(\"    ✅ Regla: blocked_payment_method\\n\")
    
    # 4. Pruebas de scoring con las reglas
    print(\"[4] Aplicando reglas a transacciones...\\n\")
    print(\"-\" * 90)
    
    test_cases = [
        {
            'name': 'Buyer confiable - Monto bajo',
            'transaction': Transaction(
                id=\"tx_001\",
                amount=500,
                buyer_id=\"buyer_trusted\",
                seller_id=\"seller_1\",
                metadata={'payment_method': 'credit_card'}
            ),
            'expected_rules': ['trusted_buyer_low_score']
        },
        {
            'name': 'Buyer nuevo - Monto alto',
            'transaction': Transaction(
                id=\"tx_002\",
                amount=3000,
                buyer_id=\"buyer_new\",
                seller_id=\"seller_1\",
                metadata={'payment_method': 'credit_card'}
            ),
            'expected_rules': ['new_buyer_high_amount']
        },
        {
            'name': 'Buyer VIP - Monto premium',
            'transaction': Transaction(
                id=\"tx_003\",
                amount=10000,
                buyer_id=\"buyer_vip\",
                seller_id=\"seller_1\",
                metadata={'payment_method': 'credit_card'}
            ),
            'expected_rules': ['trusted_buyer_low_score']
        },
        {
            'name': 'Buyer de confianza - Horario sospechoso',
            'transaction': Transaction(
                id=\"tx_004\",
                amount=1500,
                buyer_id=\"buyer_trusted\",
                seller_id=\"seller_1\",
                timestamp=Transaction(id='x', amount=1, buyer_id='x', seller_id='x').timestamp.replace(hour=3),
                metadata={'payment_method': 'credit_card'}
            ),
            'expected_rules': ['trusted_buyer_low_score', 'suspicious_time_of_day']
        },
        {
            'name': 'Pago bloqueado - Método no permitido',
            'transaction': Transaction(
                id=\"tx_005\",
                amount=500,
                buyer_id=\"buyer_trusted\",
                seller_id=\"seller_1\",
                metadata={'payment_method': 'prepaid_card'}
            ),
            'expected_rules': ['blocked_payment_method']
        },
    ]
    
    for test_case in test_cases:
        print(f\"\\n📋 {test_case['name']}\")
        print(f\"   Transacción: {test_case['transaction'].id}\")
        print(f\"   Monto: ${test_case['transaction'].amount}\")
        print(f\"   Buyer: {test_case['transaction'].buyer_id}\")
        
        result = adapter.validate_transaction(test_case['transaction'])
        
        print(f\"   ---\")
        print(f\"   Score: {result['score']:.0f}/100\")
        print(f\"   Risk Level: {result['risk_level']}\")
        print(f\"   Decision: {result['decision']}\")
        print(f\"   Confidence: {result['confidence']:.0%}\")
        print(f\"   Triggered Rules: {', '.join(result['risk_factors']) if result['risk_factors'] else 'None'}\")
    
    print(f\"\\n{'-' * 90}\\n\")
    
    # 5. Información del modelo
    print(\"[5] Información del modelo...\\n\")
    
    health = adapter.get_model_health()
    print(f\"    Versión: {health['model_version']}\")
    print(f\"    Reglas total: {health['rules_count']}\")
    print(f\"    Timestamp: {health['timestamp']}\\n\")
    
    print(\"✨ Ejemplo de reglas completado\\n\")


def advanced_rule_example():
    \"\"\"
    Ejemplo avanzado: reglas basadas en contexto.
    \"\"\"
    
    print(\"\\n🎯 SafeMarket Pocket SDK - Reglas Avanzadas\\n\")
    
    adapter = SafeMarketAdapter()
    
    # Regla con lógica compleja
    def is_suspicious_pattern(features):
        \"\"\"
        Detecta patrón sospechoso: buyer nuevo + país mismatch + monto alto.
        \"\"\"
        return (
            features.buyer_is_new and
            features.country_mismatch and
            features.amount > 1000
        )
    
    adapter.add_custom_rule(
        name=\"suspicious_trio\",
        condition=is_suspicious_pattern,
        score_delta=+50,
        severity=\"CRITICAL\",
        reason=\"Multiple red flags: new buyer + country mismatch + high amount\"
    )
    
    print(\"✅ Regla avanzada configurada\\n\")
    
    print(\"✨ Ejemplo completado\\n\")


if __name__ == \"__main__\":
    main()
    # advanced_rule_example()
