import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import { useAuth } from '../AuthContext';
import '../styles/Login.css';

export const Login = () => {
  const [studentId, setStudentId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(parseInt(studentId));
      login(response.data);
      navigate('/home');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check the student ID.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Academic Recommendation System</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="studentId">Student ID</label>
            <input
              id="studentId"
              type="number"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="Enter your student ID"
              required
              disabled={loading}
              min="1"
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <button
          type="button"
          className="secondary-btn"
          onClick={() => navigate('/register')}
          disabled={loading}
        >
          Create a new account
        </button>
        <p className="info">
          Try student IDs from 1-15 (sample data), or{' '}
          <Link to="/register">register</Link> a new student.
        </p>
      </div>
    </div>
  );
};
