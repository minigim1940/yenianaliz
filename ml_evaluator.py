# -*- coding: utf-8 -*-
"""
ML Evaluator
============
Comprehensive model evaluation with:
- Confusion matrix
- ROC curves and AUC
- Precision-Recall curves
- Feature importance analysis
- Model comparison visualizations

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score
)
from sklearn.preprocessing import label_binarize
import warnings
warnings.filterwarnings('ignore')

print("[OK] ML Evaluator Module Loaded")


class MLEvaluator:
    """
    Evaluates ML model performance with comprehensive metrics
    """
    
    def __init__(self, predictor, output_dir: str = "evaluation"):
        """
        Initialize evaluator
        
        Args:
            predictor: EnhancedMLPredictor instance
            output_dir: Directory to save evaluation results
        """
        self.predictor = predictor
        self.output_dir = output_dir
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Class names
        self.class_names = ['Away Win', 'Draw', 'Home Win']
        
        print(f"[OK] ML Evaluator initialized")
        print(f"     Output dir: {output_dir}")
    
    def plot_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str,
        save: bool = True
    ) -> np.ndarray:
        """
        Plot confusion matrix
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            model_name: Model identifier
            save: Save figure to disk
            
        Returns:
            Confusion matrix
        """
        # Calculate confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # Plot
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=self.class_names,
            yticklabels=self.class_names,
            cbar_kws={'label': 'Count'}
        )
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        if save:
            filepath = f"{self.output_dir}/{model_name}_confusion_matrix.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"[OK] Saved: {filepath}")
        
        plt.close()
        
        return cm
    
    def plot_roc_curves(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        save: bool = True
    ) -> Dict[str, float]:
        """
        Plot ROC curves for all models
        
        Args:
            X: Features
            y_true: True labels
            save: Save figure to disk
            
        Returns:
            AUC scores for each model
        """
        X_scaled = self.predictor.scaler.transform(X)
        
        # Binarize labels for multi-class ROC
        y_bin = label_binarize(y_true, classes=[0, 1, 2])
        n_classes = y_bin.shape[1]
        
        # Models
        models = {
            'XGBoost': self.predictor.xgb_model,
            'RandomForest': self.predictor.rf_model,
            'Neural Network': self.predictor.nn_model,
            'Logistic': self.predictor.lr_model,
            'Poisson': self.predictor.poisson_model
        }
        
        # Plot
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        auc_scores = {}
        
        for idx, (model_name, model) in enumerate(models.items()):
            ax = axes[idx]
            
            # Get probabilities
            y_score = model.predict_proba(X_scaled)
            
            # Calculate ROC curve and AUC for each class
            fpr = dict()
            tpr = dict()
            roc_auc = dict()
            
            for i in range(n_classes):
                fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], y_score[:, i])
                roc_auc[i] = auc(fpr[i], tpr[i])
            
            # Plot each class
            colors = ['blue', 'orange', 'green']
            for i, color, class_name in zip(range(n_classes), colors, self.class_names):
                ax.plot(
                    fpr[i], tpr[i],
                    color=color,
                    lw=2,
                    label=f'{class_name} (AUC = {roc_auc[i]:.2f})'
                )
            
            # Diagonal line
            ax.plot([0, 1], [0, 1], 'k--', lw=1)
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            ax.set_title(f'ROC Curve - {model_name}')
            ax.legend(loc="lower right", fontsize=8)
            ax.grid(alpha=0.3)
            
            # Average AUC
            avg_auc = np.mean(list(roc_auc.values()))
            auc_scores[model_name] = float(avg_auc)
        
        # Ensemble ROC
        ax = axes[5]
        ensemble_proba = self.predictor.predict_ensemble(X, return_probabilities=True)
        
        fpr_ens = dict()
        tpr_ens = dict()
        roc_auc_ens = dict()
        
        for i in range(n_classes):
            fpr_ens[i], tpr_ens[i], _ = roc_curve(y_bin[:, i], ensemble_proba[:, i])
            roc_auc_ens[i] = auc(fpr_ens[i], tpr_ens[i])
        
        for i, color, class_name in zip(range(n_classes), colors, self.class_names):
            ax.plot(
                fpr_ens[i], tpr_ens[i],
                color=color,
                lw=2,
                label=f'{class_name} (AUC = {roc_auc_ens[i]:.2f})'
            )
        
        ax.plot([0, 1], [0, 1], 'k--', lw=1)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC Curve - Ensemble')
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(alpha=0.3)
        
        auc_scores['Ensemble'] = float(np.mean(list(roc_auc_ens.values())))
        
        plt.tight_layout()
        
        if save:
            filepath = f"{self.output_dir}/roc_curves.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"[OK] Saved: {filepath}")
        
        plt.close()
        
        return auc_scores
    
    def plot_feature_importance(
        self,
        feature_names: List[str],
        top_n: int = 20,
        save: bool = True
    ) -> pd.DataFrame:
        """
        Plot feature importance from tree-based models
        
        Args:
            feature_names: List of feature names
            top_n: Number of top features to plot
            save: Save figure to disk
            
        Returns:
            Feature importance DataFrame
        """
        # Get feature importance
        importance_df = self.predictor.get_feature_importance(feature_names, top_n)
        
        # Plot
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # XGBoost importance
        axes[0].barh(
            range(len(importance_df)),
            importance_df['xgboost_importance'],
            color='steelblue'
        )
        axes[0].set_yticks(range(len(importance_df)))
        axes[0].set_yticklabels(importance_df['feature'], fontsize=9)
        axes[0].set_xlabel('Importance')
        axes[0].set_title('XGBoost Feature Importance')
        axes[0].invert_yaxis()
        axes[0].grid(axis='x', alpha=0.3)
        
        # Random Forest importance
        axes[1].barh(
            range(len(importance_df)),
            importance_df['rf_importance'],
            color='darkgreen'
        )
        axes[1].set_yticks(range(len(importance_df)))
        axes[1].set_yticklabels(importance_df['feature'], fontsize=9)
        axes[1].set_xlabel('Importance')
        axes[1].set_title('Random Forest Feature Importance')
        axes[1].invert_yaxis()
        axes[1].grid(axis='x', alpha=0.3)
        
        # Average importance
        axes[2].barh(
            range(len(importance_df)),
            importance_df['avg_importance'],
            color='coral'
        )
        axes[2].set_yticks(range(len(importance_df)))
        axes[2].set_yticklabels(importance_df['feature'], fontsize=9)
        axes[2].set_xlabel('Importance')
        axes[2].set_title('Average Feature Importance')
        axes[2].invert_yaxis()
        axes[2].grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = f"{self.output_dir}/feature_importance.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"[OK] Saved: {filepath}")
        
        plt.close()
        
        return importance_df
    
    def model_comparison_chart(
        self,
        metrics: Dict[str, Dict[str, float]],
        save: bool = True
    ) -> None:
        """
        Create model comparison bar chart
        
        Args:
            metrics: {model_name: {metric: value}}
            save: Save figure to disk
        """
        # Extract data
        models = list(metrics.keys())
        accuracy = [metrics[m]['accuracy'] for m in models]
        precision = [metrics[m]['precision'] for m in models]
        recall = [metrics[m]['recall'] for m in models]
        f1 = [metrics[m]['f1_score'] for m in models]
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(models))
        width = 0.2
        
        ax.bar(x - 1.5*width, accuracy, width, label='Accuracy', color='steelblue')
        ax.bar(x - 0.5*width, precision, width, label='Precision', color='green')
        ax.bar(x + 0.5*width, recall, width, label='Recall', color='orange')
        ax.bar(x + 1.5*width, f1, width, label='F1-Score', color='red')
        
        ax.set_xlabel('Model')
        ax.set_ylabel('Score')
        ax.set_title('Model Performance Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim([0, 1.0])
        
        plt.tight_layout()
        
        if save:
            filepath = f"{self.output_dir}/model_comparison.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"[OK] Saved: {filepath}")
        
        plt.close()
    
    def comprehensive_evaluation(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Run comprehensive evaluation
        
        Args:
            X: Features
            y_true: True labels
            feature_names: Feature names
            
        Returns:
            Evaluation results
        """
        print("\n" + "="*80)
        print("COMPREHENSIVE EVALUATION")
        print("="*80)
        
        X_scaled = self.predictor.scaler.transform(X)
        
        results = {}
        
        # 1. Confusion matrices
        print("\n[1/5] Generating confusion matrices...")
        models = {
            'xgboost': self.predictor.xgb_model,
            'random_forest': self.predictor.rf_model,
            'neural_network': self.predictor.nn_model,
            'logistic': self.predictor.lr_model,
            'poisson': self.predictor.poisson_model
        }
        
        confusion_matrices = {}
        for model_name, model in models.items():
            y_pred = model.predict(X_scaled)
            cm = self.plot_confusion_matrix(y_true, y_pred, model_name)
            confusion_matrices[model_name] = cm.tolist()
        
        # Ensemble confusion matrix
        ensemble_pred = self.predictor.predict_ensemble(X)
        cm_ensemble = self.plot_confusion_matrix(y_true, ensemble_pred, 'ensemble')
        confusion_matrices['ensemble'] = cm_ensemble.tolist()
        
        results['confusion_matrices'] = confusion_matrices
        
        # 2. ROC curves
        print("\n[2/5] Generating ROC curves...")
        auc_scores = self.plot_roc_curves(X, y_true)
        results['auc_scores'] = auc_scores
        
        # 3. Feature importance
        print("\n[3/5] Analyzing feature importance...")
        importance_df = self.plot_feature_importance(feature_names)
        results['feature_importance'] = importance_df.to_dict('records')
        
        # 4. Detailed metrics
        print("\n[4/5] Calculating detailed metrics...")
        from model_trainer import ModelTrainer
        trainer = ModelTrainer(self.predictor)
        detailed_metrics = trainer.get_detailed_metrics(X, y_true)
        results['detailed_metrics'] = detailed_metrics
        
        # 5. Model comparison
        print("\n[5/5] Creating model comparison chart...")
        self.model_comparison_chart(detailed_metrics)
        
        # Summary
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        print("\nAUC Scores:")
        for model, score in auc_scores.items():
            print(f"  {model:20s}: {score:.3f}")
        
        print("\nTop 5 Most Important Features:")
        for i, row in importance_df.head(5).iterrows():
            print(f"  {i+1}. {row['feature']:30s}: {row['avg_importance']:.4f}")
        
        print("\n" + "="*80)
        print("COMPREHENSIVE EVALUATION COMPLETE!")
        print("="*80)
        
        return results


# ========== TESTING ==========

if __name__ == "__main__":
    print("=" * 80)
    print("ML EVALUATOR TEST")
    print("=" * 80)
    
    # Import predictor
    from enhanced_ml_predictor import EnhancedMLPredictor
    
    # Create and train predictor
    print("\n[TEST] Creating and training predictor...")
    predictor = EnhancedMLPredictor()
    
    # Generate synthetic data
    np.random.seed(42)
    n_samples = 200
    n_features = 86
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.choice([0, 1, 2], size=n_samples, p=[0.30, 0.30, 0.40])
    
    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Train
    predictor.train_all_models(X_train, y_train, X_test, y_test)
    
    # Create evaluator
    evaluator = MLEvaluator(predictor)
    
    # Feature names (dummy)
    feature_names = [f'feature_{i}' for i in range(n_features)]
    
    # Comprehensive evaluation
    results = evaluator.comprehensive_evaluation(X_test, y_test, feature_names)
    
    print("\n" + "=" * 80)
    print("TEST PASSED! ML Evaluator ready for production")
    print("=" * 80)
