import React from 'react';
import { formatScore, formatNumber } from '../utils/formatters';
import '../styles/RecommendationCard.css';

export const RecommendationCard = ({ recommendation, onClick }) => {
  const scorePercent = (recommendation.score / 5) * 100;
  const hasGraphScore = recommendation.graph_score !== null && recommendation.graph_score !== undefined && recommendation.graph_score > 0;
  const hasMLScore = recommendation.ml_score !== null && recommendation.ml_score !== undefined && recommendation.ml_score > 0;

  return (
    <div className="recommendation-card" onClick={onClick}>
      <div className="card-header">
        <h3>{recommendation.module_title}</h3>
        <div className="score-badge">
          {formatScore(recommendation.score)}/5.00
        </div>
      </div>

      <div className="score-bar">
        <div className="score-fill" style={{ width: `${scorePercent}%` }}></div>
      </div>

      <p className="reason">{recommendation.reason}</p>

      <div className="confidence">
        <span>Confidence: {formatNumber(recommendation.confidence * 100)}%</span>
      </div>

      {(hasGraphScore || hasMLScore) && (
        <div className="method-scores">
          {hasGraphScore && (
            <span className="method-score">
              <span className="method-label">Graph:</span>
              <span className="method-value">{formatScore(recommendation.graph_score)}</span>
            </span>
          )}
          {hasMLScore && (
            <span className="method-score">
              <span className="method-label">ML:</span>
              <span className="method-value">{formatScore(recommendation.ml_score)}</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
};
