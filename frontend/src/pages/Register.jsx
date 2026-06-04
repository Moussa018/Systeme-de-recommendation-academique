import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI, competenciesAPI } from '../api';
import { useAuth } from '../AuthContext';
import '../styles/Login.css';

export const Register = () => {
  const [name, setName] = useState('');
  const [major, setMajor] = useState('');
  const [competencies, setCompetencies] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    competenciesAPI
      .getAll()
      .then((res) => setCompetencies(res.data))
      .catch(() => setError('Could not load skills. Is the backend running?'));
  }, []);

  const toggleSkill = (id) => {
    setSelectedSkills((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Please enter your name.');
      return;
    }
    if (selectedSkills.length === 0) {
      setError('Please select at least one skill so we can recommend courses.');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.register({
        name: name.trim(),
        major: major.trim() || 'Undeclared',
        competency_ids: selectedSkills,
      });
      // Log the new student straight in
      login(response.data);
      navigate('/home');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Create Your Account</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="major">Major (optional)</label>
            <input
              id="major"
              type="text"
              value={major}
              onChange={(e) => setMajor(e.target.value)}
              placeholder="e.g. Computer Science"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Your Skills</label>
            <p className="hint">
              Pick the skills you already have — we use these to recommend courses
              before you've rated anything.
            </p>
            <div className="skills-grid">
              {competencies.map((c) => (
                <button
                  type="button"
                  key={c.id}
                  className={`skill-chip ${selectedSkills.includes(c.id) ? 'selected' : ''}`}
                  onClick={() => toggleSkill(c.id)}
                  disabled={loading}
                >
                  {c.name}
                </button>
              ))}
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>
        <p className="info">
          Already have an ID? <Link to="/">Log in</Link>
        </p>
      </div>
    </div>
  );
};
