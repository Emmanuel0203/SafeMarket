"""
SafeMarket Pocket SDK - Transaction Simulator
==============================================

Simula transacciones para evaluar la precisión del modelo.

Permite generar transacciones con características conocidas
y medir qué tan bien el modelo identifica fraude.

Uso:
    from safemarket_pocket_sdk.ml.simulator import TransactionSimulator
    
    simulator = TransactionSimulator()
    results = simulator.simulate_and_evaluate(n_transactions=1000)
    
    print(f"Accuracy: {results['accuracy']:.1%}")
    print(f"Fraude detectado: {results['fraud_detected']}/{results['fraud_total']}")
"""

import random
from typing import Dict, Any, List
import logging

from safemarket_pocket_sdk.ml.model_trainer import ModelTrainer


logger = logging.getLogger(__name__)


class TransactionSimulator:
    """
    Simula transacciones y evalúa modelo de fraude.
    
    Genera transacciones con características realistas y etiquetas
    conocidas, luego evalúa qué tan bien el modelo predice.
    
    Ejemplo de uso:
        simulator = TransactionSimulator()
        
        # Simular y evaluar
        results = simulator.simulate_and_evaluate(n_transactions=1000)
        
        print(f"Accuracy: {results['accuracy']:.1%}")
        print(f"Fraude detectado: {results['fraud_detected']}/{results['fraud_total']}")
        
        # Detalles
        print(f"Falsos positivos: {results['false_positives']}")
        print(f"Falsos negativos: {results['false_negatives']}")
    """
    
    def __init__(self, model_path: str = None):
        """
        Inicializa el simulador.
        
        Args:
            model_path (str): Path al modelo entrenado (opcional)
        """
        self.trainer = ModelTrainer(model_path=model_path)
        
        # Cargar modelo si existe
        if not self.trainer.load_model():
            logger.warning("Modelo no encontrado. Entrenar primero con train_and_save()")
        
        self.random = random.Random(42)  # Para reproducibilidad
    
    def train_and_save(self, model_path: str = None) -> Dict[str, Any]:
        """
        Entrena el modelo y lo guarda.
        
        Args:
            model_path (str): Path para guardar modelo
        
        Returns:
            dict: Info del modelo entrenado
        
        Ejemplo:
            simulator = TransactionSimulator()
            info = simulator.train_and_save()
            print(f"Model trained with {info['test_accuracy']:.1%} accuracy")
        """
        logger.info("Entrenando modelo...")
        
        if model_path:
            self.trainer.model_path = model_path
        
        train_info = self.trainer.train()
        
        logger.info("Modelo entrenado y guardado")
        
        return train_info
    
    def generate_legitimate_transaction(self) -> Dict[str, float]:
        """
        Genera una transacción legítima (no fraude).
        
        Returns:
            dict: Features de transacción legítima
        """
        return {
            'amount': self.random.uniform(100, 1000),
            'buyer_tx_count': self.random.randint(20, 500),
            'buyer_avg_amount': self.random.uniform(150, 800),
            'buyer_is_new': 0,
            'seller_tx_count': self.random.randint(30, 300),
            'time_of_day': self.random.randint(8, 22),  # Horario normal
            'day_of_week': self.random.randint(0, 6),
            'is_weekend': self.random.randint(0, 1),
            'velocity_24h': self.random.randint(1, 30),
            'velocity_1h': self.random.randint(0, 5),
            'country_mismatch': 0,  # Mismo país
            'amount_z_score': self.random.uniform(-2, 2),
        }
    
    def generate_fraud_transaction(self) -> Dict[str, float]:
        """
        Genera una transacción fraudulenta.
        
        Simula patrones típicos de fraude:
        - Buyer nuevo
        - Monto muy alto
        - Horario sospechoso
        - Country mismatch
        - Velocity alta
        
        Returns:
            dict: Features de transacción fraudulenta
        """
        return {
            'amount': self.random.uniform(2000, 15000),  # Monto muy alto
            'buyer_tx_count': self.random.randint(0, 5),  # Muy pocas transacciones
            'buyer_avg_amount': self.random.uniform(0, 300),
            'buyer_is_new': 1,  # Buyer nuevo
            'seller_tx_count': self.random.randint(0, 20),
            'time_of_day': self.random.choice([2, 3, 4, 5]),  # Madrugada
            'day_of_week': self.random.randint(0, 6),
            'is_weekend': self.random.randint(0, 1),
            'velocity_24h': self.random.randint(10, 100),  # Velocity alta
            'velocity_1h': self.random.randint(3, 20),
            'country_mismatch': 1,  # Country diferente
            'amount_z_score': self.random.uniform(2.5, 5),  # Z-score alto
        }
    
    def simulate_and_evaluate(
        self,
        n_transactions: int = 1000,
        fraud_rate: float = 0.05
    ) -> Dict[str, Any]:
        """
        Simula transacciones y evalúa precisión del modelo.
        
        Args:
            n_transactions (int): Cantidad de transacciones a simular
            fraud_rate (float): Porcentaje de fraude (default 5%)
        
        Returns:
            dict: Resultados de la evaluación
        
        Ejemplo:
            results = simulator.simulate_and_evaluate(n_transactions=5000)
            
            print(f"Accuracy: {results['accuracy']:.1%}")
            print(f"Precision: {results['precision']:.1%}")
            print(f"Recall: {results['recall']:.1%}")
            print(f"F1: {results['f1']:.1%}")
        """
        if self.trainer.model is None:
            raise ValueError("Modelo no cargado. Llamar train_and_save() primero.")
        
        logger.info(f"Simulando {n_transactions} transacciones...")
        
        n_fraud = int(n_transactions * fraud_rate)
        n_legitimate = n_transactions - n_fraud
        
        transactions = []
        true_labels = []
        
        # Generar transacciones legítimas
        for _ in range(n_legitimate):
            tx = self.generate_legitimate_transaction()
            transactions.append(tx)
            true_labels.append(0)
        
        # Generar fraudes
        for _ in range(n_fraud):
            tx = self.generate_fraud_transaction()
            transactions.append(tx)
            true_labels.append(1)
        
        # Mezclar
        combined = list(zip(transactions, true_labels))
        self.random.shuffle(combined)
        transactions, true_labels = zip(*combined)
        transactions = list(transactions)
        true_labels = list(true_labels)
        
        # Predecir
        logger.info("Realizando predicciones...")
        predictions = []
        probabilities = []
        
        for tx in transactions:
            pred = self.trainer.predict(tx)
            prob = self.trainer.predict_probability(tx)
            predictions.append(pred)
            probabilities.append(prob)
        
        # Calcular métricas
        logger.info("Calculando métricas...")
        
        tp = sum(1 for t, p in zip(true_labels, predictions) if t == 1 and p == 1)
        tn = sum(1 for t, p in zip(true_labels, predictions) if t == 0 and p == 0)
        fp = sum(1 for t, p in zip(true_labels, predictions) if t == 0 and p == 1)
        fn = sum(1 for t, p in zip(true_labels, predictions) if t == 1 and p == 0)
        
        accuracy = (tp + tn) / len(true_labels) if len(true_labels) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        results = {
            'total_transactions': n_transactions,
            'fraud_total': n_fraud,
            'legitimate_total': n_legitimate,
            'fraud_rate': fraud_rate,
            
            # Predicciones
            'fraud_detected': tp,
            'legitimate_correctly_identified': tn,
            'false_positives': fp,
            'false_negatives': fn,
            
            # Métricas
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            
            # Tasas
            'fraud_detection_rate': tp / n_fraud if n_fraud > 0 else 0,
            'false_positive_rate': fp / n_legitimate if n_legitimate > 0 else 0,
            'false_negative_rate': fn / n_fraud if n_fraud > 0 else 0,
        }
        
        logger.info(f"✅ Simulación completada")
        logger.info(f"   Accuracy: {accuracy:.1%}")
        logger.info(f"   Precision: {precision:.1%}")
        logger.info(f"   Recall: {recall:.1%}")
        
        return results
    
    def simulate_custom_transaction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Simula predicción en una transacción personalizada.
        
        Args:
            features (dict): Features de la transacción
        
        Returns:
            dict: Predicción y probabilidad
        
        Ejemplo:
            result = simulator.simulate_custom_transaction({
                'amount': 1000,
                'buyer_tx_count': 50,
                'buyer_is_new': 0,
                ...
            })
            
            print(f"Fraud probability: {result['fraud_probability']:.1%}")
        """
        if self.trainer.model is None:
            raise ValueError("Modelo no cargado.")
        
        pred = self.trainer.predict(features)
        prob = self.trainer.predict_probability(features)
        
        return {
            'is_fraud': pred == 1,
            'fraud_probability': prob,
            'decision': 'DECLINE' if prob > 0.7 else 'MANUAL_REVIEW' if prob > 0.3 else 'APPROVE',
        }


if __name__ == "__main__":
    print("\n🎯 SafeMarket Transaction Simulator\n")
    
    try:
        simulator = TransactionSimulator()
        
        # Entrenar
        print("[1] Entrenando modelo...")
        train_info = simulator.train_and_save()
        print(f"    ✅ Modelo entrenado")
        print(f"    Train Accuracy: {train_info['train_accuracy']:.1%}")
        print(f"    Test Accuracy: {train_info['test_accuracy']:.1%}\n")
        
        # Simular diferentes escenarios
        print("[2] Simulación de transacciones\n")
        
        # Escenario 1: Dataset balanceado
        print("    Escenario 1: Dataset con 5% fraude")
        results1 = simulator.simulate_and_evaluate(n_transactions=1000, fraud_rate=0.05)
        print(f"    Accuracy: {results1['accuracy']:.1%}")
        print(f"    Fraude detectado: {results1['fraud_detected']}/{results1['fraud_total']} ({results1['fraud_detection_rate']:.1%})")
        print(f"    Falsos positivos: {results1['false_positives']}\n")
        
        # Escenario 2: Dataset con más fraude
        print("    Escenario 2: Dataset con 10% fraude")
        results2 = simulator.simulate_and_evaluate(n_transactions=1000, fraud_rate=0.10)
        print(f"    Accuracy: {results2['accuracy']:.1%}")
        print(f"    Fraude detectado: {results2['fraud_detected']}/{results2['fraud_total']} ({results2['fraud_detection_rate']:.1%})")
        print(f"    Falsos positivos: {results2['false_positives']}\n")
        
        # Escenario 3: Dataset poco balanceado
        print("    Escenario 3: Dataset con 2% fraude (realista)")
        results3 = simulator.simulate_and_evaluate(n_transactions=5000, fraud_rate=0.02)
        print(f"    Accuracy: {results3['accuracy']:.1%}")
        print(f"    Fraude detectado: {results3['fraud_detected']}/{results3['fraud_total']} ({results3['fraud_detection_rate']:.1%})")
        print(f"    Falsos positivos: {results3['false_positives']}\n")
        
        # Pruebas personalizadas
        print("[3] Pruebas personalizadas\n")
        
        print("    Test 1: Transacción legítima típica")
        result = simulator.simulate_custom_transaction({
            'amount': 500.0,
            'buyer_tx_count': 100,
            'buyer_avg_amount': 480.0,
            'buyer_is_new': 0,
            'seller_tx_count': 80,
            'time_of_day': 14,
            'day_of_week': 2,
            'is_weekend': 0,
            'velocity_24h': 5,
            'velocity_1h': 1,
            'country_mismatch': 0,
            'amount_z_score': 0.1,
        })
        print(f"    Probabilidad fraude: {result['fraud_probability']:.1%}")
        print(f"    Decisión: {result['decision']}\n")
        
        print("    Test 2: Transacción sospechosa")
        result = simulator.simulate_custom_transaction({
            'amount': 8000.0,
            'buyer_tx_count': 2,
            'buyer_avg_amount': 150.0,
            'buyer_is_new': 1,
            'seller_tx_count': 5,
            'time_of_day': 3,
            'day_of_week': 0,
            'is_weekend': 1,
            'velocity_24h': 20,
            'velocity_1h': 8,
            'country_mismatch': 1,
            'amount_z_score': 4.2,
        })
        print(f"    Probabilidad fraude: {result['fraud_probability']:.1%}")
        print(f"    Decisión: {result['decision']}\n")
        
        print("✨ Simulación completada\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
