import React from 'react';
import { formatScore, formatNumber } from '../utils/formatters';
import '../styles/RecommendationCard.css';

export const RecommendationCard = ({ recommendation, onClick }) => {
  const scorePercent = recommendation.score * 100;
  const hasGraphScore = recommendation.graph_score !== null && recommendation.graph_score !== undefined && recommendation.graph_score > 0;
  const hasMLScore = recommendation.ml_score !== null && recommendation.ml_score !== undefined && recommendation.ml_score > 0;

  return (
    <div className="recommendation-card" onClick={onClick}>
      <div className="card-header">
        <h3>{recommendation.module_title}</h3>
        <div className="score-badge">
          {formatNumber(scorePercent)}%
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
              <span className="method-value">{formatNumber(recommendation.graph_score * 100)}%</span>
            </span>
          )}
          {hasMLScore && (
            <span className="method-score">
              <span className="method-label">ML:</span>
              <span className="method-value">{formatNumber(recommendation.ml_score * 100)}%</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
};
