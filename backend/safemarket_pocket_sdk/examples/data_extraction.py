"""
SafeMarket Pocket SDK - Ejemplo: Extracción de Datos
======================================================

Ejemplo de cómo extraer datos de una BD PostgreSQL para
construir datasets de entrenamiento.

Este ejemplo es útil para integradores que quieren:
- Entrenar modelos personalizados
- Auditar decisiones
- Construir datasets etiquetados
"""

import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any

from safemarket_pocket_sdk.data import PostgreSQLConnector
from safemarket_pocket_sdk.features import FeatureExtractor
from safemarket_pocket_sdk.core import Transaction


def extract_dataset_from_postgresql():
    """
    Ejemplo: Extraer datos de PostgreSQL para entrenamiento.
    """
    
    print("\\n📊 SafeMarket Pocket SDK - Extracción de Datos\\n")
    
    # 1. Conectar a BD PostgreSQL
    print("[1] Conectando a PostgreSQL...")
    
    connector = PostgreSQLConnector(
        connection_string="postgresql://usuario:contraseña@localhost:5432/safemarket_db",
        transaction_table="transactions",
        buyer_table="users",
        seller_table="merchants"
    )
    
    try:
        connector.connect()
        print("    ✅ Conexión exitosa\\n")
        
        # 2. Validar esquema
        print("[2] Validando esquema...")
        is_valid, errors = connector.validate()
        
        if not is_valid:
            print(f"    ❌ Errores: {errors}")
            return
        print("    ✅ Esquema válido\\n")
        
        # 3. Extraer transacciones de los últimos 30 días
        print("[3] Extrayendo transacciones...\\n")
        
        query = """
            SELECT 
                id, amount, buyer_id, seller_id, created_at,
                buyer_email, seller_email, category,
                payment_method, is_fraud
            FROM transactions
            WHERE created_at > NOW() - INTERVAL '30 days'
            AND is_fraud IS NOT NULL
            ORDER BY created_at DESC
        """
        
        transactions = connector.fetch_transactions(query, limit=50000)
        print(f"    ✅ Extrajimos {len(transactions)} transacciones\\n")
        
        # 4. Construir features para cada transacción
        print("[4] Construyendo features...\\n")
        
        feature_extractor = FeatureExtractor()
        dataset = []
        
        for i, tx_data in enumerate(transactions):
            if i % 5000 == 0:
                print(f"    Procesando: {i}/{len(transactions)}...")
            
            # Obtener históricos
            buyer_hist = connector.fetch_buyer_history(tx_data['buyer_id'])
            seller_hist = connector.fetch_seller_history(tx_data['seller_id'])
            
            # Configurar en extractor
            feature_extractor.set_buyer_history(
                buyer_id=tx_data['buyer_id'],
                tx_count=buyer_hist.get('transaction_count', 0),
                avg_amount=float(buyer_hist.get('avg_amount', 0) or 0)
            )
            
            feature_extractor.set_seller_history(
                seller_id=tx_data['seller_id'],
                tx_count=seller_hist.get('transaction_count', 0),
                avg_amount=float(seller_hist.get('avg_amount', 0) or 0)
            )
            
            # Crear Transaction object
            tx = Transaction(
                id=tx_data['id'],
                amount=float(tx_data['amount']),
                buyer_id=tx_data['buyer_id'],
                seller_id=tx_data['seller_id'],
                timestamp=tx_data['created_at'],
                category=tx_data.get('category'),
                payment_method=tx_data.get('payment_method'),
                buyer_email=tx_data.get('buyer_email'),
                seller_email=tx_data.get('seller_email'),
            )
            
            # Extraer features
            features = feature_extractor.extract(tx)
            
            # Añadir al dataset con etiqueta
            dataset_row = {
                'transaction_id': tx['id'],
                'amount': features.amount,
                'amount_z_score': features.amount_z_score,
                'buyer_tx_count': features.buyer_transaction_count,
                'buyer_avg_amount': features.buyer_avg_amount,
                'buyer_is_new': int(features.buyer_is_new),
                'seller_tx_count': features.seller_transaction_count,
                'seller_avg_amount': features.seller_avg_amount,
                'time_of_day': features.time_of_day,
                'day_of_week': features.day_of_week,
                'is_weekend': int(features.is_weekend),
                'velocity_1h': features.velocity_1h,
                'velocity_24h': features.velocity_24h,
                'is_repeated_seller': int(features.is_repeated_seller),
                'country_mismatch': int(features.country_mismatch),
                # Label para entrenamientos
                'label': int(tx_data.get('is_fraud', 0)),
            }
            
            dataset.append(dataset_row)
        
        print(f"    ✅ Features construidos\\n")
        
        # 5. Exportar dataset a CSV
        print("[5] Exportando dataset...\\n")
        
        output_file = "safemarket_training_dataset.csv"
        
        if dataset:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=dataset[0].keys())
                writer.writeheader()
                writer.writerows(dataset)
            
            print(f"    ✅ Dataset exportado a: {output_file}")
            print(f"    📈 {len(dataset)} registros")
            print(f"    💾 Tamaño: {len(str(dataset)) / 1024:.2f} KB\\n")
        
        # 6. Mostrar estadísticas
        print("[6] Estadísticas del dataset...\\n")
        
        fraud_count = sum(1 for row in dataset if row['label'] == 1)
        legitimate_count = len(dataset) - fraud_count
        
        avg_amount = sum(row['amount'] for row in dataset) / len(dataset)
        max_amount = max(row['amount'] for row in dataset)
        min_amount = min(row['amount'] for row in dataset)
        
        print(f"    Total transacciones: {len(dataset)}")
        print(f"    Fraude: {fraud_count} ({fraud_count/len(dataset)*100:.1f}%)")
        print(f"    Legítimas: {legitimate_count} ({legitimate_count/len(dataset)*100:.1f}%)")
        print(f"    ---")
        print(f"    Monto promedio: ${avg_amount:,.2f}")
        print(f"    Monto mínimo: ${min_amount:,.2f}")
        print(f"    Monto máximo: ${max_amount:,.2f}")
        print(f"    ---")
        
        # Buyers nuevos vs existentes
        new_buyers = sum(1 for row in dataset if row['buyer_is_new'] == 1)
        print(f"    Buyers nuevos: {new_buyers} ({new_buyers/len(dataset)*100:.1f}%)")
        
        print(f"\\n✨ Extracción completada\\n")
    
    except Exception as e:
        print(f"    ❌ Error: {e}\\n")
    
    finally:
        connector.close()
        print("    ✅ Conexión cerrada\\n")


def simulate_data_extraction():
    """
    Simulación sin BD real (para testing).
    """
    
    print("\\n📊 SafeMarket Pocket SDK - Extracción Simulada\\n")
    print("(Este ejemplo simula datos sin conectar a BD real)\\n")
    
    # Crear transacciones simuladas
    print("[1] Generando transacciones simuladas...")
    
    simulated_transactions = [
        {
            'id': f'tx_sim_{i:06d}',
            'amount': 500 + (i % 5000),
            'buyer_id': f'buyer_{i % 100}',
            'seller_id': f'seller_{i % 50}',
            'is_fraud': i % 50 == 0,  # ~2% fraud rate
            'category': 'electronics',
            'payment_method': 'credit_card',
        }
        for i in range(1000)
    ]
    
    print(f"    ✅ {len(simulated_transactions)} transacciones generadas\\n")
    
    # Construir features
    print("[2] Construyendo features...")
    
    extractor = FeatureExtractor()
    dataset = []
    
    for tx_data in simulated_transactions:
        # Features simulados
        features_row = {
            'transaction_id': tx_data['id'],
            'amount': tx_data['amount'],
            'amount_z_score': (tx_data['amount'] - 2500) / 1500,
            'buyer_tx_count': 50,
            'buyer_avg_amount': 500,
            'seller_tx_count': 100,
            'seller_avg_amount': 600,
            'time_of_day': 14,
            'day_of_week': 3,
            'is_weekend': 0,
            'label': int(tx_data['is_fraud']),
        }
        dataset.append(features_row)
    
    print(f"    ✅ Features construidos\\n")
    
    # Estadísticas
    print("[3] Estadísticas...\\n")
    
    fraud_count = sum(1 for row in dataset if row['label'] == 1)
    print(f"    Total: {len(dataset)} transacciones")
    print(f"    Fraude: {fraud_count} ({fraud_count/len(dataset)*100:.1f}%)")
    print(f"    Legítimas: {len(dataset)-fraud_count} ({(len(dataset)-fraud_count)/len(dataset)*100:.1f}%)")
    
    print(f"\\n✨ Simulación completada\\n")


if __name__ == "__main__":
    # Ejecutar simulación (comentar para usar BD real)
    simulate_data_extraction()
    
    # Para usar BD real, descomentar:
    # extract_dataset_from_postgresql()
