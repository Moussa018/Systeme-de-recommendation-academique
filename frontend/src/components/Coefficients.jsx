import React from 'react';
import { formatCoefficient } from '../utils/formatters';
import '../styles/Coefficients.css';

export const Coefficients = ({ alpha, beta, interactionCount }) => {
  const getPhase = () => {
    if (interactionCount < 5) return 'Cold Start';
    if (interactionCount < 20) return 'Transition';
    return 'Mature';
  };

  const alphaPercent = alpha * 100;
  const betaPercent = beta * 100;
  const formattedAlpha = formatCoefficient(alpha);
  const formattedBeta = formatCoefficient(beta);

  return (
    <div className="coefficients-box">
      <h3>Recommendation Weights</h3>

      <div className="phase-indicator">
        <span className="phase-label">Phase:</span>
        <span className={`phase-badge ${getPhase().toLowerCase()}`}>
          {getPhase()}
        </span>
      </div>

      <div className="interaction-count">
        <span>Interactions:</span>
        <strong>{interactionCount}</strong>
      </div>

      <div className="weights-display">
        <div className="weight-item">
          <label>Knowledge Graph</label>
          <div className="weight-bar">
            <div
              className="weight-fill graph"
              style={{ width: `${alphaPercent}%` }}
            ></div>
          </div>
          <span className="weight-value">α = {formattedAlpha}</span>
        </div>

        <div className="weight-item">
          <label>Machine Learning</label>
          <div className="weight-bar">
            <div
              className="weight-fill ml"
              style={{ width: `${betaPercent}%` }}
            ></div>
          </div>
          <span className="weight-value">β = {formattedBeta}</span>
        </div>
      </div>

      <div className="info-text">
        <p>
          {getPhase() === 'Cold Start' &&
            'Starting phase: Recommendations based mainly on semantic knowledge graph.'}
          {getPhase() === 'Transition' &&
            'Transitioning: Gradually incorporating machine learning patterns.'}
          {getPhase() === 'Mature' &&
            'Mature phase: Recommendations based mainly on your learning patterns.'}
        </p>
      </div>
    </div>
  );
};
