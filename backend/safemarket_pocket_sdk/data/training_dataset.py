"""
SafeMarket Pocket SDK - Training Dataset
==========================================

Dataset de 500 transacciones de entrenamiento embebidas.

Usado para entrenar el modelo Random Forest sin depender de BD externa.

Uso:
    from safemarket_pocket_sdk.data.training_dataset import get_training_data
    
    dataset = get_training_data()
    print(f"Registros: {len(dataset)}")
    print(f"Columnas: {dataset[0].keys()}")
"""

from typing import List, Dict, Any


def get_training_data() -> List[Dict[str, Any]]:
    """
    Retorna dataset de 500 transacciones para entrenamiento.
    
    Cada registro contiene:
    - Features: amount, buyer_tx_count, velocity_24h, etc
    - Label: is_fraud (0=legítimo, 1=fraude)
    
    Returns:
        list[dict]: 500 registros de entrenamiento
    
    Ejemplo:
        data = get_training_data()
        for record in data[:10]:
            print(f"Amount: {record['amount']}, Fraud: {record['is_fraud']}")
    """
    
    # 500 registros generados y etiquetados
    # Proporción: ~95% legítimo, ~5% fraude (realista)
    
    dataset = [
        # Batch 1: Transacciones normales (buyer establecido)
        {'amount': 450.0, 'buyer_tx_count': 120, 'buyer_avg_amount': 420.0, 'buyer_is_new': 0, 'seller_tx_count': 85, 'time_of_day': 14, 'day_of_week': 2, 'is_weekend': 0, 'velocity_24h': 3, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': -0.1, 'is_fraud': 0},
        {'amount': 380.0, 'buyer_tx_count': 95, 'buyer_avg_amount': 390.0, 'buyer_is_new': 0, 'seller_tx_count': 102, 'time_of_day': 15, 'day_of_week': 3, 'is_weekend': 0, 'velocity_24h': 2, 'velocity_1h': 1, 'country_mismatch': 0, 'amount_z_score': -0.3, 'is_fraud': 0},
        {'amount': 520.0, 'buyer_tx_count': 180, 'buyer_avg_amount': 480.0, 'buyer_is_new': 0, 'seller_tx_count': 156, 'time_of_day': 11, 'day_of_week': 1, 'is_weekend': 0, 'velocity_24h': 4, 'velocity_1h': 1, 'country_mismatch': 0, 'amount_z_score': 0.2, 'is_fraud': 0},
        {'amount': 650.0, 'buyer_tx_count': 200, 'buyer_avg_amount': 620.0, 'buyer_is_new': 0, 'seller_tx_count': 220, 'time_of_day': 10, 'day_of_week': 4, 'is_weekend': 0, 'velocity_24h': 5, 'velocity_1h': 2, 'country_mismatch': 0, 'amount_z_score': 0.3, 'is_fraud': 0},
        {'amount': 310.0, 'buyer_tx_count': 75, 'buyer_avg_amount': 320.0, 'buyer_is_new': 0, 'seller_tx_count': 45, 'time_of_day': 16, 'day_of_week': 5, 'is_weekend': 0, 'velocity_24h': 2, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': -0.2, 'is_fraud': 0},
        
        # Batch 2: Transacciones con anomalías (fraude potencial)
        {'amount': 9500.0, 'buyer_tx_count': 5, 'buyer_avg_amount': 200.0, 'buyer_is_new': 1, 'seller_tx_count': 12, 'time_of_day': 3, 'day_of_week': 6, 'is_weekend': 1, 'velocity_24h': 8, 'velocity_1h': 3, 'country_mismatch': 1, 'amount_z_score': 4.5, 'is_fraud': 1},
        {'amount': 5200.0, 'buyer_tx_count': 2, 'buyer_avg_amount': 150.0, 'buyer_is_new': 1, 'seller_tx_count': 8, 'time_of_day': 2, 'day_of_week': 0, 'is_weekend': 1, 'velocity_24h': 12, 'velocity_1h': 5, 'country_mismatch': 1, 'amount_z_score': 3.8, 'is_fraud': 1},
        {'amount': 7800.0, 'buyer_tx_count': 1, 'buyer_avg_amount': 0.0, 'buyer_is_new': 1, 'seller_tx_count': 5, 'time_of_day': 4, 'day_of_week': 1, 'is_weekend': 0, 'velocity_24h': 15, 'velocity_1h': 8, 'country_mismatch': 1, 'amount_z_score': 5.2, 'is_fraud': 1},
        
        # Batch 3: Más transacciones normales
        {'amount': 280.0, 'buyer_tx_count': 110, 'buyer_avg_amount': 300.0, 'buyer_is_new': 0, 'seller_tx_count': 95, 'time_of_day': 13, 'day_of_week': 2, 'is_weekend': 0, 'velocity_24h': 3, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': -0.1, 'is_fraud': 0},
        {'amount': 420.0, 'buyer_tx_count': 160, 'buyer_avg_amount': 440.0, 'buyer_is_new': 0, 'seller_tx_count': 120, 'time_of_day': 14, 'day_of_week': 3, 'is_weekend': 0, 'velocity_24h': 4, 'velocity_1h': 1, 'country_mismatch': 0, 'amount_z_score': -0.05, 'is_fraud': 0},
        {'amount': 580.0, 'buyer_tx_count': 140, 'buyer_avg_amount': 600.0, 'buyer_is_new': 0, 'seller_tx_count': 180, 'time_of_day': 12, 'day_of_week': 4, 'is_weekend': 0, 'velocity_24h': 3, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': -0.15, 'is_fraud': 0},
        {'amount': 390.0, 'buyer_tx_count': 85, 'buyer_avg_amount': 400.0, 'buyer_is_new': 0, 'seller_tx_count': 110, 'time_of_day': 15, 'day_of_week': 5, 'is_weekend': 0, 'velocity_24h': 2, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': -0.25, 'is_fraud': 0},
        {'amount': 510.0, 'buyer_tx_count': 130, 'buyer_avg_amount': 520.0, 'buyer_is_new': 0, 'seller_tx_count': 145, 'time_of_day': 11, 'day_of_week': 1, 'is_weekend': 0, 'velocity_24h': 3, 'velocity_1h': 1, 'country_mismatch': 0, 'amount_z_score': -0.05, 'is_fraud': 0},
        
        # Batch 4: Buyer nuevo con comportamiento normal
        {'amount': 250.0, 'buyer_tx_count': 1, 'buyer_avg_amount': 250.0, 'buyer_is_new': 1, 'seller_tx_count': 50, 'time_of_day': 10, 'day_of_week': 2, 'is_weekend': 0, 'velocity_24h': 1, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': 0.0, 'is_fraud': 0},
        {'amount': 350.0, 'buyer_tx_count': 2, 'buyer_avg_amount': 325.0, 'buyer_is_new': 1, 'seller_tx_count': 65, 'time_of_day': 14, 'day_of_week': 3, 'is_weekend': 0, 'velocity_24h': 2, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': 0.05, 'is_fraud': 0},
        {'amount': 400.0, 'buyer_tx_count': 3, 'buyer_avg_amount': 350.0, 'buyer_is_new': 1, 'seller_tx_count': 70, 'time_of_day': 16, 'day_of_week': 4, 'is_weekend': 0, 'velocity_24h': 3, 'velocity_1h': 0, 'country_mismatch': 0, 'amount_z_score': 0.15, 'is_fraud': 0},
        
        # Batch 5: Velocity alta pero legítimo (comprador activo)
        {'amount': 200.0, 'buyer_tx_count': 500, 'buyer_avg_amount': 180.0, 'buyer_is_new': 0, 'seller_tx_count': 300, 'time_of_day': 13, 'day_of_week': 2, 'is_weekend': 0, 'velocity_24h': 45, 'velocity_1h': 8, 'country_mismatch': 0, 'amount_z_score': 0.1, 'is_fraud': 0},
        {'amount': 190.0, 'buyer_tx_count': 480, 'buyer_avg_amount': 175.0, 'buyer_is_new': 0, 'seller_tx_count': 280, 'time_of_day': 14, 'day_of_week': 3, 'is_weekend': 0, 'velocity_24h': 50, 'velocity_1h': 10, 'country_mismatch': 0, 'amount_z_score': 0.05, 'is_fraud': 0},
        
        # Batch 6: Fraude con patrones variados
        {'amount': 3000.0, 'buyer_tx_count': 0, 'buyer_avg_amount': 0.0, 'buyer_is_new': 1, 'seller_tx_count': 3, 'time_of_day': 4, 'day_of_week': 0, 'is_weekend': 1, 'velocity_24h': 5, 'velocity_1h': 2, 'country_mismatch': 1, 'amount_z_score': 2.5, 'is_fraud': 1},
        {'amount': 4500.0, 'buyer_tx_count': 1, 'buyer_avg_amount': 100.0, 'buyer_is_new': 1, 'seller_tx_count': 2, 'time_of_day': 5, 'day_of_week': 6, 'is_weekend': 1, 'velocity_24h': 3, 'velocity_1h': 1, 'country_mismatch': 1, 'amount_z_score': 3.2, 'is_fraud': 1},
        {'amount': 2800.0, 'buyer_tx_count': 2, 'buyer_avg_amount': 200.0, 'buyer_is_new': 1, 'seller_tx_count': 4, 'time_of_day': 3, 'day_of_week': 1, 'is_weekend': 0, 'velocity_24h': 10, 'velocity_1h': 4, 'country_mismatch': 1, 'amount_z_score': 2.2, 'is_fraud': 1},
    ]
    
    # Completar hasta 500 registros con patrones variados
    # Agregar 467 más (tenemos 33)
    
    # Transacciones normales adicionales (90% del resto)
    normal_patterns = [
        # Patrón 1: Buyer muy activo, cantidad pequeña
        {'amount': 100.0, 'buyer_tx_count': 1000, 'buyer_avg_amount': 95.0, 'buyer_is_new': 0, 'seller_tx_count': 500, 'time_of_day': i % 24, 'day_of_week': i % 7, 'is_weekend': (i % 7) >= 5, 'velocity_24h': 20, 'velocity_1h': 5, 'country_mismatch': 0, 'amount_z_score': 0.05, 'is_fraud': 0}
        for i in range(100)
    ]
    
    # Patrón 2: Buyer moderado
    for i in range(100):
        normal_patterns.append({
            'amount': 300.0 + (i % 50),
            'buyer_tx_count': 50 + (i % 100),
            'buyer_avg_amount': 300.0,
            'buyer_is_new': 0,
            'seller_tx_count': 80 + (i % 100),
            'time_of_day': (10 + i) % 24,
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 2 + (i % 5),
            'velocity_1h': i % 2,
            'country_mismatch': 0,
            'amount_z_score': -0.2 + (i % 5) * 0.1,
            'is_fraud': 0
        })
    
    # Patrón 3: Buyer nuevo con compra única pequeña
    for i in range(100):
        normal_patterns.append({
            'amount': 200.0 + (i % 100),
            'buyer_tx_count': 1,
            'buyer_avg_amount': 200.0 + (i % 100),
            'buyer_is_new': 1,
            'seller_tx_count': 30 + (i % 50),
            'time_of_day': (9 + i) % 24,
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 1,
            'velocity_1h': 0,
            'country_mismatch': 0,
            'amount_z_score': 0.0,
            'is_fraud': 0
        })
    
    # Patrón 4: Buyer activo de noche (pero legítimo)
    for i in range(100):
        normal_patterns.append({
            'amount': 150.0 + (i % 100),
            'buyer_tx_count': 200 + (i % 200),
            'buyer_avg_amount': 160.0,
            'buyer_is_new': 0,
            'seller_tx_count': 150 + (i % 150),
            'time_of_day': 20 + (i % 4),  # 20-23 (noche)
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 15 + (i % 20),
            'velocity_1h': 3 + (i % 5),
            'country_mismatch': 0,
            'amount_z_score': -0.1,
            'is_fraud': 0
        })
    
    # Patrón 5: Buyer con country mismatch pero legítimo
    for i in range(67):
        normal_patterns.append({
            'amount': 400.0 + (i % 100),
            'buyer_tx_count': 100 + (i % 150),
            'buyer_avg_amount': 420.0,
            'buyer_is_new': 0,
            'seller_tx_count': 80 + (i % 120),
            'time_of_day': (8 + i) % 24,
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 3 + (i % 5),
            'velocity_1h': 0 + (i % 2),
            'country_mismatch': 1,  # Country mismatch pero histórico sólido
            'amount_z_score': 0.0,
            'is_fraud': 0
        })
    
    dataset.extend(normal_patterns)
    
    # Fraudes adicionales (10% del resto)
    fraud_patterns = [
        # Patrón 1: Buyer nuevo + monto muy alto
        {
            'amount': 5000.0 + (i % 5000),
            'buyer_tx_count': 0,
            'buyer_avg_amount': 0.0,
            'buyer_is_new': 1,
            'seller_tx_count': 5 + (i % 10),
            'time_of_day': 2 + (i % 4),  # Madrugada
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 5 + (i % 15),
            'velocity_1h': 2 + (i % 5),
            'country_mismatch': 1,
            'amount_z_score': 3.0 + (i % 3),
            'is_fraud': 1
        }
        for i in range(30)
    ]
    
    # Patrón 2: Velocity extrema + monto alto
    for i in range(20):
        fraud_patterns.append({
            'amount': 3000.0 + (i % 4000),
            'buyer_tx_count': 1 + (i % 5),
            'buyer_avg_amount': 100.0 + (i % 200),
            'buyer_is_new': 1,
            'seller_tx_count': 2 + (i % 8),
            'time_of_day': 3 + (i % 5),
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 50 + (i % 100),  # Extrema
            'velocity_1h': 20 + (i % 50),
            'country_mismatch': 1,
            'amount_z_score': 2.5 + (i % 2),
            'is_fraud': 1
        })
    
    # Patrón 3: Buyer promedio pero monto súper anómalo
    for i in range(20):
        fraud_patterns.append({
            'amount': 8000.0 + (i % 5000),
            'buyer_tx_count': 50 + (i % 100),
            'buyer_avg_amount': 300.0,
            'buyer_is_new': 0,
            'seller_tx_count': 40 + (i % 60),
            'time_of_day': 4 + (i % 3),
            'day_of_week': i % 7,
            'is_weekend': (i % 7) >= 5,
            'velocity_24h': 10 + (i % 30),
            'velocity_1h': 3 + (i % 8),
            'country_mismatch': 1,
            'amount_z_score': 5.0 + (i % 2),  # Z-score muy alto
            'is_fraud': 1
        })
    
    dataset.extend(fraud_patterns)
    
    return dataset[:500]  # Exactamente 500 registros


def get_dataset_summary() -> dict:
    """
    Retorna resumen del dataset de entrenamiento.
    
    Returns:
        dict: Estadísticas del dataset
    """
    data = get_training_data()
    
    fraud_count = sum(1 for r in data if r['is_fraud'] == 1)
    legitimate_count = len(data) - fraud_count
    
    avg_fraud_amount = sum(r['amount'] for r in data if r['is_fraud'] == 1) / max(fraud_count, 1)
    avg_legit_amount = sum(r['amount'] for r in data if r['is_fraud'] == 0) / max(legitimate_count, 1)
    
    return {
        'total_records': len(data),
        'fraud_count': fraud_count,
        'legitimate_count': legitimate_count,
        'fraud_percentage': (fraud_count / len(data)) * 100,
        'avg_fraud_amount': avg_fraud_amount,
        'avg_legitimate_amount': avg_legit_amount,
        'features': list(data[0].keys()) if data else []
    }


if __name__ == "__main__":
    # Script de prueba
    data = get_training_data()
    summary = get_dataset_summary()
    
    print(f"Dataset de Entrenamiento: {summary['total_records']} registros")
    print(f"Fraude: {summary['fraud_count']} ({summary['fraud_percentage']:.1f}%)")
    print(f"Legítimo: {summary['legitimate_count']} ({100-summary['fraud_percentage']:.1f}%)")
    print(f"Monto promedio (Fraude): ${summary['avg_fraud_amount']:.2f}")
    print(f"Monto promedio (Legítimo): ${summary['avg_legitimate_amount']:.2f}")
    print(f"Features: {len(summary['features'])}")
