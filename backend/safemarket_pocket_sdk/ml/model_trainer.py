"""
SafeMarket Pocket SDK - Model Trainer (Random Forest)
======================================================

Entrena un modelo Random Forest con los datos de entrenamiento.

El modelo se persiste localmente para uso posterior en scoring.

Uso:
    from safemarket_pocket_sdk.ml.model_trainer import ModelTrainer
    
    trainer = ModelTrainer()
    model = trainer.train()
    accuracy = trainer.evaluate_on_test_set()
    
    # Predicción
    prediction = trainer.predict(features_dict)
"""

import pickle
import os
from typing import Dict, Any, Tuple, List
import logging

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report, roc_auc_score
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from safemarket_pocket_sdk.data.training_dataset import get_training_data, get_dataset_summary


logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Entrena y gestiona modelo Random Forest para scoring de fraude.
    
    Características:
    - Entrenamiento con 500 registros embebidos
    - Validación en test set
    - Persistencia de modelo
    - Métodos de evaluación
    - Explicabilidad de predicciones
    
    Ejemplo de uso:
        trainer = ModelTrainer()
        
        # Entrenar
        model_info = trainer.train()
        print(f"Accuracy: {model_info['accuracy']:.1%}")
        
        # Evaluar
        metrics = trainer.evaluate_on_test_set()
        print(f"Precision: {metrics['precision']:.1%}")
        
        # Predecir
        features = {
            'amount': 1000.0,
            'buyer_tx_count': 50,
            'velocity_24h': 5,
            ...
        }
        prob_fraud = trainer.predict_probability(features)
    """
    
    def __init__(self, model_path: str = None, random_state: int = 42):
        """
        Inicializa el trainer.
        
        Args:
            model_path (str): Path para guardar modelo (opcional)
            random_state (int): Random state para reproducibilidad
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required. Install with: pip install scikit-learn"
            )
        
        self.random_state = random_state
        self.model_path = model_path or "safemarket_fraud_model.pkl"
        self.model = None
        self.feature_names = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.metrics = None
    
    def prepare_data(self, test_size: float = 0.2) -> Tuple[Any, Any, Any, Any]:
        """
        Prepara datos para entrenamiento.
        
        Carga dataset embebido, separa features de label,
        y divide en train/test.
        
        Args:
            test_size (float): Porcentaje para test set (default 20%)
        
        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        logger.info("Cargando dataset de entrenamiento...")
        data = get_training_data()
        
        # Separar features de label
        X = []
        y = []
        feature_names = None
        
        for record in data:
            record_copy = record.copy()
            label = record_copy.pop('is_fraud')
            
            if feature_names is None:
                feature_names = list(record_copy.keys())
            
            # Convertir a lista ordenada por feature_names
            features = [record_copy[fname] for fname in feature_names]
            X.append(features)
            y.append(label)
        
        self.feature_names = feature_names
        
        logger.info(f"Dataset cargado: {len(X)} registros, {len(feature_names)} features")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y  # Mantener proporción de fraude
        )
        
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        
        logger.info(f"Train set: {len(X_train)} registros")
        logger.info(f"Test set: {len(X_test)} registros")
        
        return X_train, X_test, y_train, y_test
    
    def train(self, n_estimators: int = 100, max_depth: int = 15) -> Dict[str, Any]:
        """
        Entrena el modelo Random Forest.
        
        Args:
            n_estimators (int): Número de árboles
            max_depth (int): Profundidad máxima de árboles
        
        Returns:
            dict: Información del modelo entrenado
        
        Ejemplo:
            info = trainer.train()
            print(f"Training accuracy: {info['train_accuracy']:.1%}")
        """
        logger.info("Preparando datos...")
        self.prepare_data()
        
        logger.info(f"Entrenando Random Forest ({n_estimators} árboles, max_depth={max_depth})...")
        
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=self.random_state,
            n_jobs=-1,  # Usar todos los cores
            class_weight='balanced'  # Compensar desbalance de clases
        )
        
        self.model.fit(self.X_train, self.y_train)
        
        logger.info("Modelo entrenado. Evaluando...")
        
        # Evaluar en train set
        y_train_pred = self.model.predict(self.X_train)
        train_accuracy = accuracy_score(self.y_train, y_train_pred)
        
        # Evaluar en test set
        y_test_pred = self.model.predict(self.X_test)
        test_accuracy = accuracy_score(self.y_test, y_test_pred)
        
        # Probabilidades para ROC-AUC
        y_test_proba = self.model.predict_proba(self.X_test)[:, 1]
        try:
            roc_auc = roc_auc_score(self.y_test, y_test_proba)
        except:
            roc_auc = 0.0
        
        info = {
            'model_type': 'RandomForest',
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'roc_auc': roc_auc,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
        }
        
        logger.info(f"✅ Entrenamiento completado")
        logger.info(f"   Train Accuracy: {train_accuracy:.2%}")
        logger.info(f"   Test Accuracy: {test_accuracy:.2%}")
        logger.info(f"   ROC-AUC: {roc_auc:.3f}")
        
        # Guardar modelo
        self.save_model()
        
        return info
    
    def evaluate_on_test_set(self) -> Dict[str, Any]:
        """
        Evalúa el modelo en el test set.
        
        Retorna múltiples métricas: accuracy, precision, recall, F1, etc.
        
        Returns:
            dict: Métricas de evaluación
        
        Ejemplo:
            metrics = trainer.evaluate_on_test_set()
            print(f"Precision: {metrics['precision']:.2%}")
            print(f"Recall: {metrics['recall']:.2%}")
            print(f"F1: {metrics['f1']:.2%}")
        """
        if self.model is None or self.X_test is None:
            raise ValueError("Modelo no entrenado. Llamar train() primero.")
        
        y_pred = self.model.predict(self.X_test)
        y_proba = self.model.predict_proba(self.X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(self.y_test, y_pred),
            'precision': precision_score(self.y_test, y_pred, zero_division=0),
            'recall': recall_score(self.y_test, y_pred, zero_division=0),
            'f1': f1_score(self.y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(self.y_test, y_proba),
        }
        
        # Matriz de confusión
        cm = confusion_matrix(self.y_test, y_pred)
        metrics['confusion_matrix'] = cm
        metrics['tn'] = cm[0, 0]
        metrics['fp'] = cm[0, 1]
        metrics['fn'] = cm[1, 0]
        metrics['tp'] = cm[1, 1]
        
        # Tasa de falsos positivos y falsos negativos
        metrics['false_positive_rate'] = cm[0, 1] / (cm[0, 0] + cm[0, 1])
        metrics['false_negative_rate'] = cm[1, 0] / (cm[1, 0] + cm[1, 1])
        
        self.metrics = metrics
        
        return metrics
    
    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Retorna features más importantes según el modelo.
        
        Args:
            top_n (int): Cuántos features mostrar
        
        Returns:
            list[tuple]: Lista de (feature_name, importance)
        
        Ejemplo:
            importance = trainer.get_feature_importance(top_n=5)
            for fname, imp in importance:
                print(f"{fname}: {imp:.1%}")
        """
        if self.model is None:
            raise ValueError("Modelo no entrenado.")
        
        importances = self.model.feature_importances_
        feature_importance = list(zip(self.feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        return feature_importance[:top_n]
    
    def predict(self, features: Dict[str, float]) -> int:
        """
        Predice si una transacción es fraude.
        
        Args:
            features (dict): Features de la transacción
        
        Returns:
            int: 0 (legítimo) o 1 (fraude)
        
        Ejemplo:
            features = {
                'amount': 1000.0,
                'buyer_tx_count': 50,
                'velocity_24h': 5,
                ...
            }
            prediction = trainer.predict(features)
            print(f"Fraude: {prediction}")
        """
        if self.model is None:
            self.load_model()
        
        # Convertir dict a array en orden de features
        X = [[features.get(fname, 0) for fname in self.feature_names]]
        
        return self.model.predict(X)[0]
    
    def predict_probability(self, features: Dict[str, float]) -> float:
        """
        Predice probabilidad de fraude (0-1).
        
        Args:
            features (dict): Features de la transacción
        
        Returns:
            float: Probabilidad de fraude (0-1)
        
        Ejemplo:
            prob = trainer.predict_probability(features)
            if prob > 0.7:
                print(f"Alta probabilidad de fraude: {prob:.1%}")
        """
        if self.model is None:
            self.load_model()
        
        X = [[features.get(fname, 0) for fname in self.feature_names]]
        
        return self.model.predict_proba(X)[0][1]
    
    def save_model(self) -> str:
        """
        Guarda el modelo entrenado a disk.
        
        Returns:
            str: Path donde se guardó el modelo
        """
        if self.model is None:
            raise ValueError("No hay modelo para guardar.")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Modelo guardado: {self.model_path}")
        
        return self.model_path
    
    def load_model(self) -> bool:
        """
        Carga modelo entrenado desde disk.
        
        Returns:
            bool: True si se cargó exitosamente
        """
        if not os.path.exists(self.model_path):
            logger.warning(f"Archivo de modelo no encontrado: {self.model_path}")
            return False
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        
        logger.info(f"Modelo cargado: {self.model_path}")
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna información del modelo actual.
        
        Returns:
            dict: Información del modelo
        """
        if self.model is None:
            return {'status': 'No hay modelo entrenado'}
        
        info = {
            'model_type': 'RandomForest',
            'n_estimators': self.model.n_estimators,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
        }
        
        if self.metrics:
            info['metrics'] = self.metrics
        
        return info


if __name__ == "__main__":
    # Script de prueba
    print("\n🤖 SafeMarket Model Trainer - Random Forest\n")
    
    try:
        trainer = ModelTrainer()
        
        # Entrenar
        print("[1] Entrenando modelo...")
        train_info = trainer.train(n_estimators=100, max_depth=15)
        print(f"    ✅ Modelo entrenado")
        print(f"    Train Accuracy: {train_info['train_accuracy']:.2%}")
        print(f"    Test Accuracy: {train_info['test_accuracy']:.2%}\n")
        
        # Evaluar
        print("[2] Evaluando en test set...")
        metrics = trainer.evaluate_on_test_set()
        print(f"    Accuracy: {metrics['accuracy']:.2%}")
        print(f"    Precision: {metrics['precision']:.2%}")
        print(f"    Recall: {metrics['recall']:.2%}")
        print(f"    F1: {metrics['f1']:.2%}")
        print(f"    ROC-AUC: {metrics['roc_auc']:.3f}\n")
        
        # Features importantes
        print("[3] Features más importantes...")
        importance = trainer.get_feature_importance(top_n=10)
        for fname, imp in importance:
            print(f"    {fname}: {imp:.1%}")
        print()
        
        # Predecir ejemplo
        print("[4] Predicción de ejemplo...")
        features = {
            'amount': 1000.0,
            'buyer_tx_count': 50,
            'buyer_avg_amount': 500.0,
            'buyer_is_new': 0,
            'seller_tx_count': 80,
            'time_of_day': 14,
            'day_of_week': 2,
            'is_weekend': 0,
            'velocity_24h': 5,
            'velocity_1h': 1,
            'country_mismatch': 0,
            'amount_z_score': 0.1,
        }
        
        pred = trainer.predict(features)
        prob = trainer.predict_probability(features)
        
        print(f"    Transacción normal")
        print(f"    Predicción: {'FRAUDE' if pred == 1 else 'LEGÍTIMO'}")
        print(f"    Probabilidad fraude: {prob:.1%}\n")
        
        print("✨ Test completado\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
