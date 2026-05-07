import logging
from typing import List, Dict
from sqlalchemy.orm import Session
import numpy as np

from schemas import RecommendationItem

logger = logging.getLogger(__name__)

class FusionService:
    """
    Fusion Service that combines Graph-based and ML-based recommendations.
    Implements dynamic weighting based on data maturity (cold start vs. mature profile).
    """
    
    def __init__(self, graph_service, ml_service):
        self.graph_service = graph_service
        self.ml_service = ml_service
    
    def get_recommendations(
        self,
        student_id: int,
        limit: int,
        use_graph: bool = True,
        use_ml: bool = True,
        db: Session = None
    ) -> List[RecommendationItem]:
        """
        Get hybrid recommendations by combining graph and ML approaches.
        
        Args:
            student_id: ID of the student
            limit: Number of recommendations to return
            use_graph: Include graph-based recommendations
            use_ml: Include ML-based recommendations
            db: Database session
        """
        try:
            recommendations_by_module = {}
            
            # Get graph-based recommendations
            if use_graph:
                graph_recs = self.graph_service.get_recommendations(student_id, limit * 2, db)
                for rec in graph_recs:
                    if rec.module_id not in recommendations_by_module:
                        recommendations_by_module[rec.module_id] = {
                            "module_id": rec.module_id,
                            "module_title": rec.module_title,
                            "graph_score": rec.graph_score or rec.score,
                            "ml_score": None,
                            "graph_reason": rec.reason
                        }
                    else:
                        recommendations_by_module[rec.module_id]["graph_score"] = rec.graph_score or rec.score
            
            # Get ML-based recommendations
            if use_ml:
                ml_recs = self.ml_service.get_recommendations(student_id, limit * 2, db)
                for rec in ml_recs:
                    if rec.module_id not in recommendations_by_module:
                        recommendations_by_module[rec.module_id] = {
                            "module_id": rec.module_id,
                            "module_title": rec.module_title,
                            "graph_score": None,
                            "ml_score": rec.ml_score or rec.score,
                            "ml_reason": rec.reason
                        }
                    else:
                        recommendations_by_module[rec.module_id]["ml_score"] = rec.ml_score or rec.score
            
            # Calculate dynamic weights based on student maturity
            alpha, beta = self._calculate_weights(student_id, db)
            
            # Fuse scores
            fused_recommendations = []
            for module_id, data in recommendations_by_module.items():
                graph_score = data.get("graph_score", 0) or 0
                ml_score = data.get("ml_score", 0) or 0
                
                # Handle cold start vs. mature profile
                if use_graph and use_ml:
                    final_score = alpha * graph_score + beta * ml_score
                elif use_graph:
                    final_score = graph_score
                else:
                    final_score = ml_score
                
                # Determine reason
                reason = "Hybrid recommendation"
                if data.get("graph_reason"):
                    reason = data["graph_reason"]
                
                fused_recommendations.append(RecommendationItem(
                    module_id=module_id,
                    module_title=data["module_title"],
                    score=float(final_score),
                    confidence=self._calculate_confidence(graph_score, ml_score, alpha, beta),
                    reason=reason,
                    graph_score=graph_score if use_graph else None,
                    ml_score=ml_score if use_ml else None
                ))
            
            # Sort by final score and limit
            fused_recommendations.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(
                f"Generated {len(fused_recommendations[:limit])} hybrid recommendations "
                f"for student {student_id} (α={alpha:.2f}, β={beta:.2f})"
            )
            
            return fused_recommendations[:limit]
        
        except Exception as e:
            logger.error(f"Error in fusion: {str(e)}")
            return []
    
    def _calculate_weights(self, student_id: int, db: Session) -> tuple:
        """
        Calculate dynamic weights based on student data maturity.
        
        Returns:
            (alpha, beta): Weights for graph and ML components
            - Cold start profile: high alpha, low beta
            - Mature profile: low alpha, high beta
        """
        try:
            from models import InteractionDB
            
            # Count student interactions
            interaction_count = db.query(InteractionDB).filter(
                InteractionDB.student_id == student_id
            ).count()
            
            # Dynamic weighting based on interaction count
            # Cold start (< 5 interactions): prioritize knowledge graph
            # Mature (>= 20 interactions): prioritize ML predictions
            
            if interaction_count < 5:
                # Cold start profile
                alpha = 0.8
                beta = 0.2
            elif interaction_count < 20:
                # Transition phase
                progress = (interaction_count - 5) / 15
                alpha = 0.8 - (0.5 * progress)
                beta = 0.2 + (0.5 * progress)
            else:
                # Mature profile
                alpha = 0.3
                beta = 0.7
            
            return (alpha, beta)
        
        except Exception as e:
            logger.warning(f"Error calculating weights: {str(e)}, using default")
            return (0.5, 0.5)
    
    def _calculate_confidence(self, graph_score: float, ml_score: float, alpha: float, beta: float) -> float:
        """Calculate confidence score for the recommendation"""
        if graph_score and ml_score:
            # Both methods agree - high confidence
            agreement = 1 - abs(graph_score - ml_score)
            return float(min(0.95, 0.7 + agreement * 0.25))
        elif graph_score or ml_score:
            # Only one method available
            return float(min(0.85, 0.6 + max(graph_score, ml_score) * 0.25))
        else:
            return 0.5
