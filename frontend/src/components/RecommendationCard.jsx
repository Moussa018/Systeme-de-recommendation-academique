import React from 'react';
import '../styles/RecommendationCard.css';

export const RecommendationCard = ({ recommendation, onClick }) => {
  const scorePercent = (recommendation.score / 5) * 100;

  return (
    <div className="recommendation-card" onClick={onClick}>
      <div className="card-header">
        <h3>{recommendation.module_title}</h3>
        <div className="score-badge">
          {recommendation.score.toFixed(1)}/5
        </div>
      </div>

      <div className="score-bar">
        <div className="score-fill" style={{ width: `${scorePercent}%` }}></div>
      </div>

      <p className="reason">{recommendation.reason}</p>

      <div className="confidence">
        <span>Confidence: {(recommendation.confidence * 100).toFixed(0)}%</span>
      </div>

      {(recommendation.graph_score || recommendation.ml_score) && (
        <div className="method-scores">
          {recommendation.graph_score && (
            <span className="method-score">Graph: {recommendation.graph_score.toFixed(2)}</span>
          )}
          {recommendation.ml_score && (
            <span className="method-score">ML: {recommendation.ml_score.toFixed(2)}</span>
          )}
        </div>
      )}
    </div>
  );
};
