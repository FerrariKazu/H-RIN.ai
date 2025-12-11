import pickle
import json
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.ml.feature_builder import build_features

class MLEvaluator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self._load_config()
        self.model_a = self._load_model("ai_score_model.pkl")
        self.model_b = self._load_model("model.pkl") # This is recruiter_model.pkl
        
        # Adjust weights to balance Experience vs Skills
        self._adjust_weights()
        
    def _adjust_weights(self):
        """
        Manually adjusts model weights to prevent 'Experience' from dominating 
        and to give more importance to 'Skills'.
        """
        features = self.config['features_used']
        weights = np.array(self.model_a['weights'])
        
        print("DEBUG: Adjusting weights...")
        
        for i, feature in enumerate(features):
            # Reduce Experience Weight
            if feature == "Experience (Years)":
                print(f"DEBUG: Reducing weight for {feature} from {weights[i]:.2f} to {weights[i] * 0.5:.2f}")
                weights[i] *= 0.5
                
            # Remove Salary Expectation Weight
            if feature == "Salary Expectation ($)":
                print(f"DEBUG: Zeroing weight for {feature}")
                weights[i] = 0.0
                
            # Increase Skill Weights
            if feature.startswith("feat_skill_") or feature == "feat_num_skills_matched":
                # Boost skills significantly
                weights[i] *= 3.0
        
        # Update the model dictionary
        self.model_a['weights'] = weights.tolist()
        
    def _load_config(self) -> Dict:
        path = os.path.join(self.base_dir, "config.json")
        with open(path, 'r') as f:
            return json.load(f)

    def _load_model(self, filename: str) -> Dict:
        path = os.path.join(self.base_dir, filename)
        with open(path, 'rb') as f:
            return pickle.load(f)

    def _impute_and_scale(self, df: pd.DataFrame, params: Dict) -> np.ndarray:
        """
        Applies the saved preprocessing parameters (median imputation + scaling) to the dataframe.
        Re-implements the logic from train_two_model_pipeline.py
        """
        X_vals = df.values.astype(float)
        medians = params["medians"]
        modes = params["modes"]
        mean = np.array(params["mean"], dtype=float)
        std = np.array(params["std"], dtype=float)
        bool_flags = params["bool_flags"]
        
        for j in range(X_vals.shape[1]):
            col = X_vals[:, j]
            if bool_flags[j]:
                mode_val = modes[j]
                col[np.isnan(col)] = mode_val
            else:
                m = medians[j]
                col[np.isnan(col)] = m
            X_vals[:, j] = col
            
        X_std = X_vals.copy()
        for j in range(X_vals.shape[1]):
            if not bool_flags[j]:
                X_std[:, j] = (X_vals[:, j] - mean[j]) / std[j]
                
        return X_std

    def _add_intercept(self, X: np.ndarray) -> np.ndarray:
        return np.hstack([X, np.ones((X.shape[0], 1))])

    def _predict_linear(self, X: np.ndarray, w: np.ndarray) -> float:
        return float(X @ w)

    def _predict_logistic_prob(self, X: np.ndarray, w: np.ndarray) -> float:
        z = X @ w
        return float(1 / (1 + np.exp(-z)))

    def evaluate(self, text: str, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full prediction pipeline:
        1. Build features
        2. Predict AI Score (Model A)
        3. Predict Recruiter Decision (Model B)
        4. Explain prediction
        """
        feature_cols = self.config['features_used']
        
        # 1. Build Features
        df_features = build_features(text, structured_data, feature_cols)
        
        # 2. Model A: AI Score
        params_a = self.model_a['preproc']
        weights_a = np.array(self.model_a['weights'])
        
        X_a = self._impute_and_scale(df_features, params_a)
        X_a_bias = self._add_intercept(X_a)
        
        # Calculate raw score first!
        ai_score_pred = self._predict_linear(X_a_bias, weights_a)
        
        # Normalize Score to prevent saturation
        # The intercept is ~42. Skills can add 70+.
        # We want a score of ~100 to require exceptional skills.
        
        # 1. Remove the intercept bias to start from 0-ish
        intercept = weights_a[-1]
        score_without_intercept = ai_score_pred - intercept
        
        # 2. Scale the remaining score (skills + exp)
        # If we have 2 good skills (35+35=70) + exp (5) = 75.
        # We want that to be maybe 80/100 total?
        # Let's scale it down slightly.
        scaled_score = score_without_intercept * 0.8
        
        # 3. Add a base score (e.g., 20) so empty resumes aren't 0
        final_score = 20 + scaled_score
        
        print(f"DEBUG: Normalized Score: {final_score} (Raw: {ai_score_pred}, Intercept: {intercept})")
        
        if ai_score_pred > 200:
            print("DEBUG: 🚨 HIGH SCORE DETECTED! Checking features...")
            for i, feature in enumerate(feature_cols):
                val_std = X_a[0, i]
                weight = weights_a[i]
                contrib = val_std * weight
                if abs(contrib) > 50:
                    print(f"  🚨 OUTLIER: {feature} | StdVal: {val_std:.2f} | Weight: {weight:.2f} | Contrib: {contrib:.2f}")

        ai_score_pred = max(0.0, min(100.0, final_score)) # Clip
        
        # 3. Model B: Recruiter Decision
        params_b = self.model_b['preproc']
        weights_b = np.array(self.model_b['weights'])
        ai_stats = self.model_b['ai_feature_standardization']
        
        # Preprocess base features again (same as A, but conceptually for B)
        # Note: In the training pipeline, X_std_full is reused.
        # Here we re-compute it to be safe, using Model B's stored params (should be identical to A's if from same run)
        X_b = self._impute_and_scale(df_features, params_b)
        
        # Standardize AI Score
        ai_score_std = (ai_score_pred - ai_stats['mean']) / ai_stats['std']
        
        # Combine
        X_b_combined = np.column_stack([X_b, np.array([[ai_score_std]])])
        X_b_bias = self._add_intercept(X_b_combined)
        
        hire_prob = self._predict_logistic_prob(X_b_bias, weights_b)
        
        # 4. Feature Importance (Explanation)
        # We use Model B's weights.
        # The last weight is intercept, second to last is AI Score.
        # The rest correspond to feature_cols.
        
        feature_contributions = {}
        # Base features
        for i, col in enumerate(feature_cols):
            # Contribution = weight * standardized_value
            # This is a rough approximation for logistic regression explanation
            val_std = X_b[0, i]
            weight = weights_b[i]
            feature_contributions[col] = weight * val_std
            
        # AI Score contribution
        feature_contributions['AI Score'] = weights_b[len(feature_cols)] * ai_score_std
        
        # Sort features
        sorted_feats = sorted(feature_contributions.items(), key=lambda x: x[1], reverse=True)
        top_positive = [{"feature": k, "contribution": v} for k, v in sorted_feats[:5] if v > 0]
        top_negative = [{"feature": k, "contribution": v} for k, v in sorted_feats[-5:] if v < 0]
        
        return {
            "hire_probability": hire_prob,
            "predicted_ai_score": ai_score_pred,
            "top_positive_features": top_positive,
            "top_negative_features": top_negative,
            "all_features": df_features.to_dict(orient='records')[0]
        }

# Singleton
evaluator = MLEvaluator()
