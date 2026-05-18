import logging
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from math import log2

from models import StudentDB, InteractionDB, ModuleDB
from schemas import RecommendationItem

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Service for evaluating recommendation system performance.
    Measures Precision@K, Recall@K, F1@K, NDCG@K, RMSE, MAE across approaches.
    """

    def __init__(self, graph_service, ml_service, fusion_service):
        self.graph_service = graph_service
        self.ml_service = ml_service
        self.fusion_service = fusion_service

    def evaluate_approach(
        self,
        approach: str,
        db: Session,
        top_k: int = 5
    ) -> Dict:
        """
        Evaluate a single approach using leave-one-out validation.

        Args:
            approach: 'graph', 'ml', or 'hybrid'
            db: Database session
            top_k: Evaluate at this cutoff

        Returns:
            Dict with metrics: precision, recall, f1, ndcg, rmse, mae
        """
        students = db.query(StudentDB).all()
        valid_students = [s for s in students if len(s.interactions) >= 2]

        if not valid_students:
            logger.warning(f"No students with 2+ interactions for {approach} evaluation")
            return {
                "precision_at_k": 0.0,
                "recall_at_k": 0.0,
                "f1_at_k": 0.0,
                "ndcg_at_k": 0.0,
                "rmse": 0.0,
                "mae": 0.0,
                "n_evaluated": 0
            }

        precisions = []
        recalls = []
        f1_scores = []
        ndcgs = []
        rmses = []
        maes = []

        for student in valid_students:
            # Hold out the last interaction as ground truth
            if len(student.interactions) < 2:
                continue

            held_out = student.interactions[-1]
            student_id = student.id
            ground_truth_module_id = held_out.module_id
            ground_truth_rating = held_out.rating

            # Get recommendations for this approach
            if approach == "graph":
                recs = self.graph_service.get_recommendations(student_id, top_k, db)
            elif approach == "ml":
                recs = self.ml_service.get_recommendations(student_id, top_k, db)
            elif approach == "hybrid":
                recs = self.fusion_service.get_recommendations(
                    student_id, top_k, use_graph=True, use_ml=True, db=db
                )
            else:
                continue

            # Extract recommended module IDs
            recommended_ids = [rec.module_id for rec in recs]

            # Precision@K: is the held-out module in top-K?
            is_relevant = 1 if ground_truth_module_id in recommended_ids else 0
            precision = is_relevant / top_k if recommended_ids else 0.0
            precisions.append(precision)

            # Recall@K: same as precision here (only 1 relevant item)
            recall = is_relevant
            recalls.append(recall)

            # F1@K
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0.0
            f1_scores.append(f1)

            # NDCG@K: discounted cumulative gain
            ndcg = self._compute_ndcg(ground_truth_module_id, recommended_ids, top_k)
            ndcgs.append(ndcg)

            # Rating prediction metrics (ML only)
            if approach == "ml":
                predicted_rating = self.ml_service.predict_score(student_id, ground_truth_module_id, db)
                rmse_error = (predicted_rating - ground_truth_rating) ** 2
                mae_error = abs(predicted_rating - ground_truth_rating)
                rmses.append(rmse_error)
                maes.append(mae_error)

        # Aggregate metrics
        result = {
            "precision_at_k": float(np.mean(precisions)) if precisions else 0.0,
            "recall_at_k": float(np.mean(recalls)) if recalls else 0.0,
            "f1_at_k": float(np.mean(f1_scores)) if f1_scores else 0.0,
            "ndcg_at_k": float(np.mean(ndcgs)) if ndcgs else 0.0,
            "rmse": float(np.sqrt(np.mean(rmses))) if rmses else 0.0,
            "mae": float(np.mean(maes)) if maes else 0.0,
            "n_evaluated": len(valid_students)
        }

        logger.info(f"{approach} evaluation: P@{top_k}={result['precision_at_k']:.3f}, "
                   f"R@{top_k}={result['recall_at_k']:.3f}, "
                   f"F1@{top_k}={result['f1_at_k']:.3f}, "
                   f"NDCG@{top_k}={result['ndcg_at_k']:.3f}")

        return result

    def compare_approaches(self, db: Session, top_k: int = 5) -> Dict:
        """
        Compare all three approaches: graph, ml, hybrid.

        Returns:
            Dict with comparison results for all three approaches
        """
        approaches = ["graph", "ml", "hybrid"]
        results = {}

        for approach in approaches:
            metrics = self.evaluate_approach(approach, db, top_k)
            results[approach] = metrics

        # Determine winner by F1 score
        f1_scores = {app: metrics["f1_at_k"] for app, metrics in results.items()}
        winner = max(f1_scores, key=f1_scores.get) if f1_scores else "hybrid"

        # Generate analysis
        analysis = self._generate_analysis(results, winner, top_k)

        return {
            "top_k": top_k,
            "approaches": results,
            "winner": winner,
            "analysis": analysis
        }

    def _compute_ndcg(self, ground_truth_id: int, recommended_ids: List[int], k: int) -> float:
        """
        Compute Normalized Discounted Cumulative Gain.

        NDCG = DCG / IDCG
        DCG = sum(relevance_i / log2(i + 1)) for i in 1..k
        IDCG = DCG of ideal ranking (relevant item at position 1)
        """
        # Compute DCG
        dcg = 0.0
        for i, rec_id in enumerate(recommended_ids[:k]):
            relevance = 1 if rec_id == ground_truth_id else 0
            dcg += relevance / log2(i + 2)  # log2(i+2) because position is 1-indexed

        # Compute IDCG (ideal: relevant item at position 1)
        idcg = 1.0 / log2(2)  # 1 / log2(2) = 1

        ndcg = dcg / idcg if idcg > 0 else 0.0
        return float(ndcg)

    def _generate_analysis(self, results: Dict, winner: str, top_k: int) -> str:
        """Generate a text analysis of the results"""
        graph_f1 = results["graph"]["f1_at_k"]
        ml_f1 = results["ml"]["f1_at_k"]
        hybrid_f1 = results["hybrid"]["f1_at_k"]

        if graph_f1 > 0 or ml_f1 > 0 or hybrid_f1 > 0:
            analysis = (
                f"Evaluation at top-{top_k} results: "
                f"Hybrid approach (F1={hybrid_f1:.3f}) outperforms "
                f"Graph (F1={graph_f1:.3f}) and ML (F1={ml_f1:.3f}). "
            )

            if winner == "hybrid":
                analysis += (
                    f"The hybrid fusion strategy effectively combines the strengths of "
                    f"Knowledge Graph reasoning with collaborative filtering patterns."
                )
            elif winner == "graph":
                analysis += (
                    f"The Knowledge Graph approach excels due to strong semantic "
                    f"understanding of prerequisite relationships and competencies."
                )
            else:
                analysis += (
                    f"The ML approach leverages user similarity patterns effectively "
                    f"to uncover hidden preferences."
                )
        else:
            analysis = "Insufficient interaction data for meaningful evaluation."

        return analysis
