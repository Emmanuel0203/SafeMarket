"""
SafeMarket Pocket SDK - Pruebas de Integración
=============================================

Suite completa de pruebas de integración para validar
que todos los módulos funcionan correctamente juntos.

Ejecución:
    python -m pytest safemarket_pocket_sdk/tests/test_integration.py -v
    
O sin pytest:
    python safemarket_pocket_sdk/tests/test_integration.py
"""

import sys
import os
from typing import Dict, Any, List, Tuple
import traceback

# Agregar el directorio del SDK al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Transaction, FeatureSet
from features.extractor import FeatureExtractor
from scoring.score_engine import ScoreEngine
from data.training_dataset import get_training_data, get_dataset_summary
from ml.model_trainer import ModelTrainer
from ml.simulator import TransactionSimulator
from integration.adapter import SafeMarketAdapter


class IntegrationTestSuite:
    """Suite de pruebas de integración."""
    
    def __init__(self):
        """Inicializa el suite de pruebas."""
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results: List[Tuple[str, bool, str]] = []
    
    def run_test(self, test_name: str, test_func):
        """Ejecuta un test y registra el resultado."""
        try:
            print(f"\n{'='*70}")
            print(f"  TEST: {test_name}")
            print(f"{'='*70}\n")
            
            test_func()
            
            self.tests_passed += 1
            self.test_results.append((test_name, True, "✅ PASSED"))
            print(f"✅ PASSED\n")
            
        except AssertionError as e:
            self.tests_failed += 1
            self.test_results.append((test_name, False, f"❌ FAILED: {e}"))
            print(f"❌ FAILED: {e}\n")
            traceback.print_exc()
            
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((test_name, False, f"❌ ERROR: {e}"))
            print(f"❌ ERROR: {e}\n")
            traceback.print_exc()
    
    def test_1_feature_extractor(self):
        """Prueba: FeatureExtractor extrae características correctamente."""
        print("Probando extracción de características...")
        
        # Crear transacción
        tx = Transaction(
            id="test_tx_1",
            amount=1000.0,
            buyer_id="buyer_123",
            seller_id="seller_456"
        )
        
        # Crear extractor
        extractor = FeatureExtractor()
        
        # Establecer datos históricos
        extractor.set_buyer_history({
            'tx_count': 50,
            'avg_amount': 800.0,
            'is_new': False
        })
        
        extractor.set_seller_history({
            'tx_count': 100,
            'avg_amount': 950.0
        })
        
        # Extraer features
        features = extractor.extract(tx)
        
        # Validaciones
        assert isinstance(features, FeatureSet), "Features debe ser FeatureSet"
        assert features.amount == 1000.0, "Monto incorrecto"
        assert features.buyer_tx_count == 50, "TX count incorrecto"
        assert features.buyer_is_new == 0, "buyer_is_new incorrecto"
        assert features.seller_tx_count == 100, "Seller TX count incorrecto"
        
        print(f"  ✓ Features extraídas correctamente")
        print(f"    - Amount: {features.amount}")
        print(f"    - Buyer TX Count: {features.buyer_tx_count}")
        print(f"    - Seller TX Count: {features.seller_tx_count}")
        print(f"    - Amount Z-score: {features.amount_z_score:.2f}")
    
    def test_2_score_engine_rules(self):
        """Prueba: ScoreEngine aplica reglas correctamente."""
        print("Probando Score Engine...")
        
        # Crear features
        features = FeatureSet(
            amount=8000.0,
            buyer_tx_count=0,
            buyer_avg_amount=0.0,
            buyer_is_new=1,
            seller_tx_count=5,
            time_of_day=3,
            day_of_week=0,
            is_weekend=1,
            velocity_24h=20,
            velocity_1h=8,
            country_mismatch=1,
            amount_z_score=4.5
        )
        
        # Crear engine
        engine = ScoreEngine()
        
        # Evaluar
        result = engine.calculate_score(features)
        
        # Validaciones
        assert isinstance(result, dict), "Resultado debe ser dict"
        assert 'score' in result, "Score no presente en resultado"
        assert 'risk_level' in result, "Risk level no presente"
        assert result['score'] > 50, "Score debe ser alto para transacción sospechosa"
        
        print(f"  ✓ Score calculado: {result['score']:.0f}/100")
        print(f"  ✓ Risk Level: {result['risk_level']}")
        print(f"  ✓ Decision: {result['decision']}")
        print(f"  ✓ Triggered rules: {len(result.get('triggered_rules', []))}")
    
    def test_3_features_scoring_integration(self):
        """Prueba: Features + Scoring funcionan juntos."""
        print("Probando integración Features + Scoring...")
        
        # Crear transacción
        tx = Transaction(
            id="test_tx_2",
            amount=500.0,
            buyer_id="buyer_123",
            seller_id="seller_456"
        )
        
        # Extraer features
        extractor = FeatureExtractor()
        extractor.set_buyer_history({'tx_count': 100, 'avg_amount': 480.0, 'is_new': False})
        extractor.set_seller_history({'tx_count': 150, 'avg_amount': 520.0})
        features = extractor.extract(tx)
        
        # Scoring
        engine = ScoreEngine()
        result = engine.calculate_score(features)
        
        # Validaciones
        assert result['score'] < 40, "Transacción legítima debe tener score bajo"
        assert result['risk_level'] == 'LOW', "Risk level debe ser LOW"
        assert result['decision'] == 'APPROVE', "Decision debe ser APPROVE"
        
        print(f"  ✓ Features extraídas")
        print(f"  ✓ Scoring aplicado")
        print(f"  ✓ Score: {result['score']:.0f} (Legítimo)")
        print(f"  ✓ Decisión: {result['decision']}")
    
    def test_4_training_dataset(self):
        """Prueba: Dataset de entrenamiento cargado correctamente."""
        print("Probando dataset de entrenamiento...")
        
        # Cargar dataset
        data = get_training_data()
        summary = get_dataset_summary()
        
        # Validaciones
        assert len(data) == 500, "Dataset debe tener 500 registros"
        assert summary['total_records'] == 500, "Summary mismatch"
        
        fraud_count = sum(1 for r in data if r['is_fraud'] == 1)
        assert fraud_count > 0, "Dataset debe tener registros de fraude"
        
        legitimate_count = sum(1 for r in data if r['is_fraud'] == 0)
        assert legitimate_count > 0, "Dataset debe tener registros legítimos"
        
        # Validar estructura
        first_record = data[0]
        required_fields = [
            'amount', 'buyer_tx_count', 'buyer_avg_amount', 'buyer_is_new',
            'seller_tx_count', 'time_of_day', 'day_of_week', 'is_weekend',
            'velocity_24h', 'velocity_1h', 'country_mismatch', 'amount_z_score',
            'is_fraud'
        ]
        
        for field in required_fields:
            assert field in first_record, f"Campo {field} faltante en dataset"
        
        print(f"  ✓ Dataset cargado: {len(data)} registros")
        print(f"  ✓ Fraude: {fraud_count} ({fraud_count/len(data)*100:.1f}%)")
        print(f"  ✓ Legítimo: {legitimate_count} ({legitimate_count/len(data)*100:.1f}%)")
        print(f"  ✓ Features: {len(summary['features'])}")
    
    def test_5_model_trainer(self):
        """Prueba: Model Trainer entrena correctamente."""
        print("Probando Model Trainer...")
        
        # Crear trainer
        trainer = ModelTrainer()
        
        # Entrenar
        info = trainer.train(n_estimators=50, max_depth=10)
        
        # Validaciones
        assert trainer.model is not None, "Modelo no entrenado"
        assert 'train_accuracy' in info, "Train accuracy no presente"
        assert 'test_accuracy' in info, "Test accuracy no presente"
        assert info['train_accuracy'] > 0.85, "Train accuracy muy baja"
        assert info['test_accuracy'] > 0.80, "Test accuracy muy baja"
        
        print(f"  ✓ Modelo entrenado")
        print(f"  ✓ Train Accuracy: {info['train_accuracy']:.2%}")
        print(f"  ✓ Test Accuracy: {info['test_accuracy']:.2%}")
        print(f"  ✓ ROC-AUC: {info['roc_auc']:.3f}")
        print(f"  ✓ Features: {info['n_features']}")
    
    def test_6_model_prediction(self):
        """Prueba: Modelo predice correctamente."""
        print("Probando predicciones del modelo...")
        
        # Entrenar modelo
        trainer = ModelTrainer()
        trainer.train(n_estimators=50, max_depth=10)
        
        # Test 1: Transacción legítima
        features_legitimate = {
            'amount': 500.0,
            'buyer_tx_count': 100,
            'buyer_avg_amount': 480.0,
            'buyer_is_new': 0,
            'seller_tx_count': 150,
            'time_of_day': 14,
            'day_of_week': 2,
            'is_weekend': 0,
            'velocity_24h': 5,
            'velocity_1h': 1,
            'country_mismatch': 0,
            'amount_z_score': 0.1,
        }
        
        pred_legit = trainer.predict(features_legitimate)
        prob_legit = trainer.predict_probability(features_legitimate)
        
        assert pred_legit in [0, 1], "Predicción debe ser 0 o 1"
        assert 0 <= prob_legit <= 1, "Probabilidad debe estar entre 0 y 1"
        assert prob_legit < 0.5, "TX legítima debe tener prob baja"
        
        print(f"  ✓ Predicción legítima: {pred_legit} (prob: {prob_legit:.2%})")
        
        # Test 2: Transacción fraudulenta
        features_fraud = {
            'amount': 8000.0,
            'buyer_tx_count': 0,
            'buyer_avg_amount': 0.0,
            'buyer_is_new': 1,
            'seller_tx_count': 5,
            'time_of_day': 3,
            'day_of_week': 0,
            'is_weekend': 1,
            'velocity_24h': 20,
            'velocity_1h': 8,
            'country_mismatch': 1,
            'amount_z_score': 4.5,
        }
        
        pred_fraud = trainer.predict(features_fraud)
        prob_fraud = trainer.predict_probability(features_fraud)
        
        assert prob_fraud > 0.3, "TX fraudulenta debe tener prob alta"
        
        print(f"  ✓ Predicción fraudulenta: {pred_fraud} (prob: {prob_fraud:.2%})")
    
    def test_7_simulator(self):
        """Prueba: Simulator funciona correctamente."""
        print("Probando Transaction Simulator...")
        
        # Crear y entrenar
        simulator = TransactionSimulator()
        simulator.train_and_save()
        
        # Simular (pequeño dataset para speed)
        results = simulator.simulate_and_evaluate(
            n_transactions=500,
            fraud_rate=0.05
        )
        
        # Validaciones
        assert 'accuracy' in results, "Accuracy no presente"
        assert 'precision' in results, "Precision no presente"
        assert 'recall' in results, "Recall no presente"
        assert 'f1' in results, "F1 no presente"
        assert results['accuracy'] > 0.8, "Accuracy muy baja"
        
        print(f"  ✓ Simulación completada: {results['total_transactions']} TX")
        print(f"  ✓ Accuracy: {results['accuracy']:.2%}")
        print(f"  ✓ Precision: {results['precision']:.2%}")
        print(f"  ✓ Recall: {results['recall']:.2%}")
        print(f"  ✓ F1: {results['f1']:.2%}")
    
    def test_8_custom_rules(self):
        """Prueba: Reglas personalizadas funcionan."""
        print("Probando reglas personalizadas...")
        
        # Crear engine
        engine = ScoreEngine()
        
        # Agregar regla personalizada
        engine.add_rule(
            name="high_amount_new_buyer",
            condition=lambda f: f.buyer_is_new and f.amount > 5000,
            score_delta=50,
            severity="HIGH"
        )
        
        # Test features que disparan la regla
        features = FeatureSet(
            amount=7000.0,
            buyer_tx_count=0,
            buyer_avg_amount=0.0,
            buyer_is_new=1,
            seller_tx_count=5,
            time_of_day=14,
            day_of_week=2,
            is_weekend=0,
            velocity_24h=5,
            velocity_1h=1,
            country_mismatch=0,
            amount_z_score=2.0
        )
        
        result = engine.calculate_score(features)
        
        # Validaciones
        assert result['score'] >= 50, "Score debe incluir delta de regla personalizada"
        
        print(f"  ✓ Regla personalizada agregada")
        print(f"  ✓ Score con regla: {result['score']:.0f}")
        print(f"  ✓ Triggered rules: {len(result.get('triggered_rules', []))}")
    
    def test_9_adapter_basic(self):
        """Prueba: SafeMarketAdapter funciona básico."""
        print("Probando SafeMarketAdapter (básico)...")
        
        # Crear adaptador
        adapter = SafeMarketAdapter()
        
        # Crear transacción
        tx = Transaction(
            id="adapter_test_1",
            amount=500.0,
            buyer_id="buyer_123",
            seller_id="seller_456"
        )
        
        # Validar
        result = adapter.validate_transaction(tx)
        
        # Validaciones
        assert isinstance(result, dict), "Resultado debe ser dict"
        assert 'transaction_id' in result, "transaction_id no presente"
        assert 'score' in result, "score no presente"
        assert 'risk_level' in result, "risk_level no presente"
        assert 'decision' in result, "decision no presente"
        assert 0 <= result['score'] <= 100, "Score fuera de rango"
        
        print(f"  ✓ Transacción validada")
        print(f"  ✓ Score: {result['score']:.0f}")
        print(f"  ✓ Risk Level: {result['risk_level']}")
        print(f"  ✓ Decision: {result['decision']}")
    
    def test_10_adapter_with_history(self):
        """Prueba: Adapter con históricos."""
        print("Probando SafeMarketAdapter (con históricos)...")
        
        # Crear adaptador
        adapter = SafeMarketAdapter()
        
        # Configurar datos
        adapter.set_buyer_data(
            buyer_id="buyer_123",
            tx_count=50,
            avg_amount=480.0,
            is_new=False
        )
        
        adapter.set_seller_data(
            seller_id="seller_456",
            tx_count=100,
            avg_amount=500.0
        )
        
        # Crear transacción
        tx = Transaction(
            id="adapter_test_2",
            amount=500.0,
            buyer_id="buyer_123",
            seller_id="seller_456"
        )
        
        # Validar
        result = adapter.validate_transaction(tx)
        
        # Validaciones
        assert result['score'] < 40, "Score debe ser bajo para TX legítima"
        assert result['decision'] == 'APPROVE', "Decision debe ser APPROVE"
        
        print(f"  ✓ Datos configurados")
        print(f"  ✓ Score: {result['score']:.0f}")
        print(f"  ✓ Decision: {result['decision']}")
    
    def test_11_adapter_feedback(self):
        """Prueba: Adapter registra feedback."""
        print("Probando feedback del Adapter...")
        
        # Crear adaptador
        adapter = SafeMarketAdapter()
        
        # Registrar feedback
        adapter.submit_feedback(
            transaction_id="tx_feedback_1",
            label="FRAUD",
            reviewer_id="reviewer_john",
            notes="Card reported stolen"
        )
        
        # Registrar otro feedback
        adapter.submit_feedback(
            transaction_id="tx_feedback_2",
            label="LEGITIMATE",
            reviewer_id="reviewer_jane",
            notes="Verified customer"
        )
        
        # Obtener log
        feedback_log = adapter.get_feedback_log()
        
        # Validaciones
        assert len(feedback_log) == 2, "Debe haber 2 feedbacks registrados"
        assert feedback_log[0]['label'] == 'FRAUD', "Primer feedback debe ser FRAUD"
        assert feedback_log[1]['label'] == 'LEGITIMATE', "Segundo debe ser LEGITIMATE"
        
        print(f"  ✓ Feedback registrado: {len(feedback_log)} registros")
        print(f"  ✓ Feedback 1: {feedback_log[0]['label']}")
        print(f"  ✓ Feedback 2: {feedback_log[1]['label']}")
    
    def test_12_adapter_custom_rules(self):
        """Prueba: Adapter con reglas personalizadas."""
        print("Probando Adapter con reglas personalizadas...")
        
        # Crear adaptador
        adapter = SafeMarketAdapter()
        
        # Agregar regla
        adapter.add_custom_rule(
            name="test_high_amount",
            condition=lambda f: f.amount > 5000,
            score_delta=30,
            severity="HIGH",
            reason="High amount transaction"
        )
        
        # Transacción normal (no dispara regla)
        tx1 = Transaction(
            id="rule_test_1",
            amount=1000.0,
            buyer_id="buyer_1",
            seller_id="seller_1"
        )
        result1 = adapter.validate_transaction(tx1)
        
        # Transacción alta (dispara regla)
        tx2 = Transaction(
            id="rule_test_2",
            amount=6000.0,
            buyer_id="buyer_2",
            seller_id="seller_2"
        )
        result2 = adapter.validate_transaction(tx2)
        
        # Validaciones
        assert result2['score'] > result1['score'], "TX alta debe tener score mayor"
        
        print(f"  ✓ Regla personalizada agregada")
        print(f"  ✓ TX normal ($1000): Score {result1['score']:.0f}")
        print(f"  ✓ TX alta ($6000): Score {result2['score']:.0f}")
    
    def test_13_adapter_health(self):
        """Prueba: Adapter health check."""
        print("Probando health check del Adapter...")
        
        # Crear adaptador
        adapter = SafeMarketAdapter()
        
        # Agregar algunas operaciones
        adapter.submit_feedback("tx_1", "FRAUD", "reviewer_1")
        adapter.submit_feedback("tx_2", "LEGITIMATE", "reviewer_1")
        adapter.add_custom_rule("rule_1", lambda f: f.amount > 5000, 20, "MEDIUM")
        
        # Health check
        health = adapter.get_model_health()
        
        # Validaciones
        assert 'model_version' in health, "model_version no presente"
        assert 'rules_count' in health, "rules_count no presente"
        assert 'feedback_count' in health, "feedback_count no presente"
        assert health['feedback_count'] == 2, "Debe haber 2 feedbacks"
        assert health['rules_count'] >= 1, "Debe haber reglas"
        
        print(f"  ✓ Model Version: {health['model_version']}")
        print(f"  ✓ Rules Count: {health['rules_count']}")
        print(f"  ✓ Feedback Count: {health['feedback_count']}")
    
    def print_summary(self):
        """Imprime resumen de pruebas."""
        total = self.tests_passed + self.tests_failed
        
        print("\n" + "="*70)
        print("  RESUMEN DE PRUEBAS DE INTEGRACIÓN")
        print("="*70 + "\n")
        
        for test_name, passed, message in self.test_results:
            status = "✅" if passed else "❌"
            print(f"{status} {test_name:50s} {message}")
        
        print("\n" + "-"*70)
        print(f"Total:  {total}")
        print(f"Pasadas: {self.tests_passed} ✅")
        print(f"Fallidas: {self.tests_failed} ❌")
        print(f"Tasa de éxito: {self.tests_passed/total*100:.1f}%")
        print("-"*70 + "\n")
        
        if self.tests_failed == 0:
            print("🎉 TODAS LAS PRUEBAS PASARON! 🎉\n")
        else:
            print(f"⚠️  {self.tests_failed} PRUEBAS FALLARON\n")


def main():
    """Función principal."""
    print("\n" + "🧪 " * 20)
    print("  SafeMarket Pocket SDK - Pruebas de Integración")
    print("🧪 " * 20 + "\n")
    
    suite = IntegrationTestSuite()
    
    # Ejecutar tests
    suite.run_test("1. Feature Extractor", suite.test_1_feature_extractor)
    suite.run_test("2. Score Engine - Rules", suite.test_2_score_engine_rules)
    suite.run_test("3. Features + Scoring (Integration)", suite.test_3_features_scoring_integration)
    suite.run_test("4. Training Dataset", suite.test_4_training_dataset)
    suite.run_test("5. Model Trainer", suite.test_5_model_trainer)
    suite.run_test("6. Model Predictions", suite.test_6_model_prediction)
    suite.run_test("7. Transaction Simulator", suite.test_7_simulator)
    suite.run_test("8. Custom Rules", suite.test_8_custom_rules)
    suite.run_test("9. Adapter - Basic", suite.test_9_adapter_basic)
    suite.run_test("10. Adapter - With History", suite.test_10_adapter_with_history)
    suite.run_test("11. Adapter - Feedback", suite.test_11_adapter_feedback)
    suite.run_test("12. Adapter - Custom Rules", suite.test_12_adapter_custom_rules)
    suite.run_test("13. Adapter - Health Check", suite.test_13_adapter_health)
    
    # Imprimir resumen
    suite.print_summary()
    
    return 0 if suite.tests_failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
