import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { modulesAPI, interactionsAPI } from '../api';
import { useAuth } from '../AuthContext';
import '../styles/CourseDetail.css';

export const CourseDetail = () => {
  const { courseId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [interaction, setInteraction] = useState(null);
  const [rating, setRating] = useState(0);
  const [completion, setCompletion] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    loadCourseData();
  }, [courseId, user, navigate]);

  const loadCourseData = async () => {
    setLoading(true);
    setError('');
    try {
      const courseResponse = await modulesAPI.getById(parseInt(courseId));
      setCourse(courseResponse.data);

      const interactionsResponse = await interactionsAPI.getStudentInteractions(user.id);
      const studentInteraction = interactionsResponse.data.find(
        i => i.module_id === parseInt(courseId)
      );

      if (studentInteraction) {
        setInteraction(studentInteraction);
        setRating(studentInteraction.rating);
        setCompletion(studentInteraction.completion_rate);
      } else {
        setRating(0);
        setCompletion(0);
      }
    } catch (err) {
      setError('Failed to load course details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await interactionsAPI.createOrUpdate(user.id, parseInt(courseId), {
        rating,
        completion_rate: completion
      });
      setSuccess('Progress saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to save progress');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="course-detail-container">Loading...</div>;
  }

  if (!course) {
    return <div className="course-detail-container">Course not found</div>;
  }

  return (
    <div className="course-detail-container">
      <button onClick={() => navigate('/home')} className="back-btn">← Back to Dashboard</button>

      <div className="course-detail-card">
        <div className="course-header">
          <h1>{course.title}</h1>
          <span className="course-code">{course.code}</span>
        </div>

        <div className="course-info-grid">
          <div className="info-item">
            <label>Difficulty</label>
            <p>{course.difficulty}</p>
          </div>
          <div className="info-item">
            <label>Credits</label>
            <p>{course.credits}</p>
          </div>
        </div>

        <div className="description-section">
          <h3>Description</h3>
          <p>{course.description}</p>
        </div>

        <div className="progress-section">
          <h3>Your Progress</h3>

          <div className="form-group">
            <label htmlFor="rating">
              Rating: {rating}/5
            </label>
            <div className="rating-input">
              <input
                id="rating"
                type="range"
                min="0"
                max="5"
                step="0.5"
                value={rating}
                onChange={(e) => setRating(parseFloat(e.target.value))}
                disabled={saving}
              />
              <span className="rating-value">{rating.toFixed(1)}</span>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="completion">
              Completion: {Math.round(completion)}%
            </label>
            <div className="progress-bar-container">
              <input
                id="completion"
                type="range"
                min="0"
                max="100"
                step="1"
                value={completion}
                onChange={(e) => setCompletion(parseInt(e.target.value))}
                disabled={saving}
                className="progress-input"
              />
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${completion}%` }}></div>
              </div>
              <span className="completion-value">{Math.round(completion)}%</span>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button
            onClick={handleSave}
            disabled={saving}
            className="save-btn"
          >
            {saving ? 'Saving...' : 'Save Progress'}
          </button>
        </div>

        {interaction && (
          <div className="info-section">
            <p>Last updated: {new Date(interaction.timestamp).toLocaleString()}</p>
          </div>
        )}
      </div>
    </div>
  );
};
