import logging
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
import warnings

from models import StudentDB, ModuleDB, InteractionDB
from schemas import RecommendationItem

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class MLService:
    """
    Machine Learning Service for collaborative filtering based recommendations.
    Implements both SVD (Matrix Factorization) and basic Neural Collaborative Filtering.
    """
    
    def __init__(self, n_factors: int = 10):
        self.n_factors = n_factors
        self.user_factors = None
        self.item_factors = None
        self.user_means = None
        self.students = []
        self.modules = []
        self.interaction_matrix = None
        self.model_trained = False
    
    def train(self, db: Session):
        """Train the collaborative filtering model"""
        try:
            logger.info("Training ML model...")

            # Get all students and modules
            self.students = db.query(StudentDB).all()
            self.modules = db.query(ModuleDB).all()

            if not self.students or not self.modules:
                logger.warning("Insufficient data for training")
                return False

            # Create interaction matrix
            interactions = db.query(InteractionDB).all()
            self.interaction_matrix = self._create_interaction_matrix(interactions)

            # Apply SVD with adaptive n_components
            if self.interaction_matrix.size > 0:
                # SVD requires n_components <= min(n_rows, n_cols)
                max_components = min(self.interaction_matrix.shape[0], self.interaction_matrix.shape[1])
                n_components = min(self.n_factors, max_components)

                if n_components < 1:
                    logger.warning("Not enough data for SVD training")
                    return False

                # Mean-center over OBSERVED (non-zero) entries per user. Unseen
                # cells stay 0, so after factorization they reconstruct toward the
                # user's mean rather than toward 0 (avoids the implicit-feedback
                # bias of treating "not taken" as a rating of zero).
                observed_mask = self.interaction_matrix > 0
                row_sums = self.interaction_matrix.sum(axis=1)
                row_counts = observed_mask.sum(axis=1)
                self.user_means = np.divide(
                    row_sums, row_counts,
                    out=np.zeros_like(row_sums, dtype=float),
                    where=row_counts > 0
                )
                centered = self.interaction_matrix - self.user_means[:, None] * observed_mask

                svd = TruncatedSVD(n_components=n_components, random_state=42)
                self.user_factors = svd.fit_transform(centered)
                self.item_factors = svd.components_.T
                self.model_trained = True
                logger.info(f"Model trained with {len(self.students)} students and {len(self.modules)} modules (n_components={n_components})")
                return True

            return False
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def _create_interaction_matrix(self, interactions: List) -> np.ndarray:
        """Create user-item interaction matrix"""
        n_students = len(self.students)
        n_modules = len(self.modules)
        
        matrix = np.zeros((n_students, n_modules))
        
        # Map student and module IDs to indices
        student_idx_map = {s.id: i for i, s in enumerate(self.students)}
        module_idx_map = {m.id: i for i, m in enumerate(self.modules)}
        
        # Fill matrix with ratings
        for interaction in interactions:
            if (interaction.student_id in student_idx_map and 
                interaction.module_id in module_idx_map):
                student_idx = student_idx_map[interaction.student_id]
                module_idx = module_idx_map[interaction.module_id]
                # Use weighted combination of rating and completion
                score = (interaction.rating * 0.6 + interaction.completion_rate / 100 * 0.4)
                matrix[student_idx, module_idx] = score
        
        return matrix
    
    def get_recommendations(self, student_id: int, limit: int, db: Session) -> List[RecommendationItem]:
        """
        Get recommendations using collaborative filtering with SVD matrix reconstruction.
        Uses predicted scores from matrix factorization.
        """
        try:
            # Train if not already trained
            if not self.model_trained:
                if not self.train(db):
                    logger.warning("Training failed, returning empty recommendations")
                    return []

            student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
            if not student:
                return []

            # Find student index
            student_idx_map = {s.id: i for i, s in enumerate(self.students)}
            if student_id not in student_idx_map:
                return []

            student_idx = student_idx_map[student_id]

            # Get student's latent factors
            if self.user_factors is None or student_idx >= len(self.user_factors):
                return []

            # SVD reconstruction + user mean (we centered before factorizing).
            predicted_scores = (
                self.user_factors[student_idx] @ self.item_factors.T
                + self.user_means[student_idx]
            )
            predicted_scores = np.clip(predicted_scores, 0, 5.0)  # Clip to reasonable rating range

            # Get modules student has already taken
            taken_modules = db.query(InteractionDB).filter(
                InteractionDB.student_id == student_id
            ).all()
            taken_module_ids = {i.module_id for i in taken_modules}

            # Score all modules except already-taken
            module_idx_map = {m.id: i for i, m in enumerate(self.modules)}
            scored_modules = []

            for module_id, module in enumerate(self.modules):
                if module.id not in taken_module_ids:
                    # Predicted rating is on a 0-5 scale; normalize to 0-1 so it
                    # matches the graph score's scale for fusion and display.
                    score = float(predicted_scores[module_idx_map[module.id]]) / 5.0
                    scored_modules.append((module.id, module.title, score))

            # Sort by predicted score and limit
            scored_modules.sort(key=lambda x: x[2], reverse=True)
            scored_modules = scored_modules[:limit]

            recommendations = []
            for module_id, title, score in scored_modules:
                recommendations.append(RecommendationItem(
                    module_id=module_id,
                    module_title=title,
                    score=score,
                    confidence=min(0.95, abs(score) * 0.95),
                    reason="Matches your learning profile",
                    ml_score=score
                ))

            return recommendations

        except Exception as e:
            logger.error(f"Error in ML recommendations: {str(e)}")
            return []
    
    def predict_score(self, student_id: int, module_id: int, db: Session) -> float:
        """Predict rating for a (student, module) pair using SVD reconstruction"""
        try:
            if not self.model_trained:
                if not self.train(db):
                    return 0.0

            student_idx_map = {s.id: i for i, s in enumerate(self.students)}
            module_idx_map = {m.id: i for i, m in enumerate(self.modules)}

            if student_id not in student_idx_map or module_id not in module_idx_map:
                return 0.0

            student_idx = student_idx_map[student_id]
            module_idx = module_idx_map[module_id]

            predicted_score = float(
                self.user_factors[student_idx] @ self.item_factors[module_idx]
                + self.user_means[student_idx]
            )
            return np.clip(predicted_score, 0, 5.0)
        except Exception as e:
            logger.error(f"Error predicting score: {str(e)}")
            return 0.0
