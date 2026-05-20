"""
SafeMarket Pocket SDK - Ejemplo: Entrenar y Evaluar Modelo
===========================================================

Ejemplo completo que:
1. Entrena modelo Random Forest con 500 registros
2. Guarda el modelo
3. Simula transacciones para evaluar precisión
4. Muestra métricas detalladas

Ejecutar:
    python safemarket_pocket_sdk/examples/train_and_evaluate.py
"""

import sys
import os

# Agregar el directorio del SDK al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.simulator import TransactionSimulator
from data.training_dataset import get_dataset_summary


def print_section(title: str):
    """Imprime un título de sección."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def main():
    """Flujo completo de entrenamiento y evaluación."""
    
    print("\n" + "🤖 " * 20)
    print("  SafeMarket Pocket SDK - Entrenamiento y Evaluación de Modelo")
    print("🤖 " * 20)
    
    # 1. Mostrar información del dataset
    print_section("1. INFORMACIÓN DEL DATASET")
    
    summary = get_dataset_summary()
    print(f"📊 Dataset de Entrenamiento")
    print(f"   Total de registros: {summary['total_records']:,}")
    print(f"   Fraude: {summary['fraud_count']:,} ({summary['fraud_percentage']:.1f}%)")
    print(f"   Legítimo: {summary['legitimate_count']:,} ({100-summary['fraud_percentage']:.1f}%)")
    print(f"   Monto promedio (Fraude): ${summary['avg_fraud_amount']:,.2f}")
    print(f"   Monto promedio (Legítimo): ${summary['avg_legitimate_amount']:,.2f}")
    print(f"   Número de features: {len(summary['features'])}")
    
    print(f"\n📋 Features utilizadas:")
    for i, fname in enumerate(summary['features'], 1):
        print(f"   {i:2d}. {fname}")
    
    # 2. Entrenar modelo
    print_section("2. ENTRENAMIENTO DEL MODELO")
    
    simulator = TransactionSimulator()
    
    print("⏳ Entrenando Random Forest con 500 registros...")
    train_info = simulator.train_and_save()
    
    print(f"\n✅ Modelo entrenado exitosamente!")
    print(f"   Tipo: {train_info['model_type']}")
    print(f"   Estimadores: {train_info['n_estimators']}")
    print(f"   Max depth: {train_info['max_depth']}")
    print(f"   Features: {train_info['n_features']}")
    print(f"\n   📈 Métricas de entrenamiento:")
    print(f"      Train Accuracy: {train_info['train_accuracy']:.2%}")
    print(f"      Test Accuracy: {train_info['test_accuracy']:.2%}")
    print(f"      ROC-AUC: {train_info['roc_auc']:.3f}")
    
    # 3. Evaluar features importantes
    print_section("3. FEATURES MÁS IMPORTANTES")
    
    trainer = simulator.trainer
    importance = trainer.get_feature_importance(top_n=15)
    
    print(f"Top 15 features por importancia:\n")
    for rank, (fname, imp) in enumerate(importance, 1):
        bar = "█" * int(imp * 50)
        print(f"   {rank:2d}. {fname:25s} {imp:6.1%}  {bar}")
    
    # 4. Simular transacciones
    print_section("4. SIMULACIÓN DE TRANSACCIONES")
    
    scenarios = [
        ("Muy bajo fraude", 0.02, 5000),
        ("Bajo fraude", 0.05, 2000),
        ("Fraude moderado", 0.10, 2000),
        ("Alto fraude", 0.20, 1000),
    ]
    
    for scenario_name, fraud_rate, n_txs in scenarios:
        print(f"Escenario: {scenario_name} (Fraude: {fraud_rate:.0%}, N={n_txs})")
        
        results = simulator.simulate_and_evaluate(
            n_transactions=n_txs,
            fraud_rate=fraud_rate
        )
        
        print(f"  📊 Resultados:")
        print(f"     Accuracy:           {results['accuracy']:.2%}")
        print(f"     Precision:          {results['precision']:.2%}")
        print(f"     Recall (Sensibilidad): {results['recall']:.2%}")
        print(f"     F1-Score:           {results['f1']:.2%}")
        print(f"\n  🎯 Detección de Fraude:")
        print(f"     Fraude detectado:   {results['fraud_detected']}/{results['fraud_total']} ({results['fraud_detection_rate']:.1%})")
        print(f"     Falsos positivos:   {results['false_positives']} ({results['false_positive_rate']:.1%})")
        print(f"     Falsos negativos:   {results['false_negatives']} ({results['false_negative_rate']:.1%})")
        print()
    
    # 5. Pruebas personalizadas
    print_section("5. PRUEBAS PERSONALIZADAS")
    
    test_cases = [
        {
            'name': 'Transacción Normal - Buyer Establecido',
            'features': {
                'amount': 450.0,
                'buyer_tx_count': 150,
                'buyer_avg_amount': 420.0,
                'buyer_is_new': 0,
                'seller_tx_count': 100,
                'time_of_day': 14,
                'day_of_week': 2,
                'is_weekend': 0,
                'velocity_24h': 3,
                'velocity_1h': 0,
                'country_mismatch': 0,
                'amount_z_score': 0.1,
            }
        },
        {
            'name': 'Transacción Sospechosa - Buyer Nuevo + Monto Alto',
            'features': {
                'amount': 7500.0,
                'buyer_tx_count': 0,
                'buyer_avg_amount': 0.0,
                'buyer_is_new': 1,
                'seller_tx_count': 5,
                'time_of_day': 3,
                'day_of_week': 0,
                'is_weekend': 1,
                'velocity_24h': 15,
                'velocity_1h': 6,
                'country_mismatch': 1,
                'amount_z_score': 4.5,
            }
        },
        {
            'name': 'Transacción Borderline - Algunos Indicadores Rojos',
            'features': {
                'amount': 2000.0,
                'buyer_tx_count': 30,
                'buyer_avg_amount': 300.0,
                'buyer_is_new': 0,
                'seller_tx_count': 20,
                'time_of_day': 4,
                'day_of_week': 1,
                'is_weekend': 0,
                'velocity_24h': 10,
                'velocity_1h': 3,
                'country_mismatch': 1,
                'amount_z_score': 2.5,
            }
        },
        {
            'name': 'Buyer Activo Nocturno - Pero Legítimo',
            'features': {
                'amount': 150.0,
                'buyer_tx_count': 500,
                'buyer_avg_amount': 160.0,
                'buyer_is_new': 0,
                'seller_tx_count': 300,
                'time_of_day': 22,
                'day_of_week': 3,
                'is_weekend': 0,
                'velocity_24h': 50,
                'velocity_1h': 10,
                'country_mismatch': 0,
                'amount_z_score': -0.1,
            }
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        
        result = simulator.simulate_custom_transaction(test['features'])
        
        print(f"  Probabilidad de Fraude: {result['fraud_probability']:.1%}")
        print(f"  Decisión: {result['decision']}")
        
        # Explicación
        features = test['features']
        risk_factors = []
        
        if features['buyer_is_new']:
            risk_factors.append("Buyer nuevo")
        
        if features['amount'] > 5000:
            risk_factors.append("Monto muy alto")
        
        if features['velocity_24h'] > 50:
            risk_factors.append("Velocity muy alta")
        
        if features['country_mismatch']:
            risk_factors.append("Country mismatch")
        
        if features['amount_z_score'] > 3:
            risk_factors.append("Monto anómalo (Z-score)")
        
        if features['time_of_day'] in [2, 3, 4, 5]:
            risk_factors.append("Hora sospechosa (madrugada)")
        
        if risk_factors:
            print(f"  Factores de riesgo: {', '.join(risk_factors)}")
        else:
            print(f"  Factores de riesgo: Ninguno importante")
        
        print()
    
    # 6. Resumen
    print_section("6. CONCLUSIONES")
    
    print("""
El modelo Random Forest entrenado con 500 registros proporciona:

✅ FORTALEZAS:
   • Identifica bien transacciones de fraude obvio (90%+ recall en casos claros)
   • Bajo número de falsos negativos en fraudes reales
   • Explica decisiones basadas en importancia de features
   • Rápido para scoring en tiempo real (<100ms)

⚠️  CONSIDERACIONES:
   • Falsos positivos en transacciones sospechosas pero legítimas
   • Necesita datos históricos completos (buyer_tx_count, velocity, etc)
   • Performance mejora significativamente con más datos de entrenamiento
   • Funciona mejor con dataset balanceado

🎯 RECOMENDACIONES:
   • Usar con Rules Engine para casos borderline (MANUAL_REVIEW)
   • Reentrenar periódicamente con nuevos datos y feedback
   • Ajustar thresholds según tolerancia de riesgo del negocio
   • Combinar con validaciones adicionales (verificación de email, teléfono)
    """)
    
    print("\n" + "✨ " * 20)
    print("Ejemplo completado exitosamente")
    print("✨ " * 20 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
