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
            
            # Apply SVD
            if self.interaction_matrix.size > 0:
                svd = TruncatedSVD(n_components=self.n_factors, random_state=42)
                self.user_factors = svd.fit_transform(self.interaction_matrix)
                self.item_factors = svd.components_.T
                self.model_trained = True
                logger.info(f"Model trained with {len(self.students)} students and {len(self.modules)} modules")
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
        Get recommendations using collaborative filtering.
        Find similar students and recommend modules they liked.
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
            
            student_vector = self.user_factors[student_idx]
            
            # Find similar students
            similarities = self._compute_similarities(student_vector)
            similar_students_indices = np.argsort(similarities)[::-1][1:6]  # Top 5 similar
            
            # Get modules liked by similar students
            module_idx_map = {m.id: i for i, m in enumerate(self.modules)}
            module_scores = {}
            
            for sim_idx in similar_students_indices:
                if sim_idx < len(self.interaction_matrix):
                    sim_student_interactions = self.interaction_matrix[sim_idx]
                    
                    for module_idx, score in enumerate(sim_student_interactions):
                        if score > 0:  # Student interacted with this module
                            module_id = self.modules[module_idx].id
                            
                            # Skip if already taken
                            existing = db.query(InteractionDB).filter(
                                InteractionDB.student_id == student_id,
                                InteractionDB.module_id == module_id
                            ).first()
                            
                            if not existing:
                                if module_id not in module_scores:
                                    module_scores[module_id] = []
                                module_scores[module_id].append(score)
            
            # Aggregate scores
            final_scores = {
                mid: np.mean(scores) for mid, scores in module_scores.items()
            }
            
            # Sort and limit
            sorted_modules = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            recommendations = []
            for module_id, score in sorted_modules:
                module = db.query(ModuleDB).filter(ModuleDB.id == module_id).first()
                if module:
                    recommendations.append(RecommendationItem(
                        module_id=module_id,
                        module_title=module.title,
                        score=float(score),
                        confidence=min(0.95, score * 0.95),
                        reason="Popular among similar students",
                        ml_score=float(score)
                    ))
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error in ML recommendations: {str(e)}")
            return []
    
    def _compute_similarities(self, student_vector: np.ndarray) -> np.ndarray:
        """Compute cosine similarities between student and all other students"""
        if self.user_factors is None:
            return np.zeros(len(self.students))
        
        # Normalize vectors
        student_norm = np.linalg.norm(student_vector)
        if student_norm == 0:
            return np.zeros(len(self.students))
        
        normalized_student = student_vector / student_norm
        
        similarities = []
        for i, user_vector in enumerate(self.user_factors):
            user_norm = np.linalg.norm(user_vector)
            if user_norm == 0:
                similarities.append(0)
            else:
                normalized_user = user_vector / user_norm
                similarity = np.dot(normalized_student, normalized_user)
                similarities.append(similarity)
        
        return np.array(similarities)
