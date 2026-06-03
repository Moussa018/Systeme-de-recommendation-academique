import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationsAPI, modulesAPI } from '../api';
import { useAuth } from '../AuthContext';
import { formatNumber } from '../utils/formatters';
import { RecommendationCard } from '../components/RecommendationCard';
import { Coefficients } from '../components/Coefficients';
import '../styles/Home.css';

export const Home = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [allModules, setAllModules] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [coefficients, setCoefficients] = useState(null);

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    loadData();
  }, [user, navigate]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [recsResponse, modulesResponse] = await Promise.all([
        recommendationsAPI.get(user.id, 10),
        modulesAPI.getAll()
      ]);

      setRecommendations(recsResponse.data.recommendations);
      setAllModules(modulesResponse.data);
      setCoefficients({
        alpha: recsResponse.data.alpha,
        beta: recsResponse.data.beta,
        interactionCount: recsResponse.data.interaction_count
      });
    } catch (err) {
      setError('Failed to load recommendations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredModules = allModules.filter(module =>
    module.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    module.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredRecommendations = recommendations.filter(rec =>
    rec.module_title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="home-container">
      <header className="header">
        <div className="header-content">
          <h1>Dashboard</h1>
          <div className="user-info">
            <span>Welcome, {user?.name}</span>
            <button onClick={logout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="search-section">
          <input
            type="text"
            placeholder="Search courses by name or code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-bar"
          />
          <button onClick={loadData} className="refresh-btn">
            Refresh Recommendations
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading">Loading recommendations...</div>
        ) : (
          <div className="content-grid">
            <div className="recommendations-section">
              <h2>Recommended Courses For You</h2>
              <div className="recommendations-list">
                {filteredRecommendations.length > 0 ? (
                  filteredRecommendations.map(rec => (
                    <RecommendationCard
                      key={rec.module_id}
                      recommendation={rec}
                      onClick={() => navigate(`/course/${rec.module_id}`)}
                    />
                  ))
                ) : (
                  <p className="no-results">
                    {searchQuery ? 'No recommended courses match your search' : 'No recommendations available'}
                  </p>
                )}
              </div>
            </div>

            <div className="right-column">
              <div className="search-section-side">
                <h2>All Courses</h2>
                <div className="courses-list">
                  {filteredModules.length > 0 ? (
                    filteredModules.map(module => (
                      <div
                        key={module.id}
                        className="course-item"
                        onClick={() => navigate(`/course/${module.id}`)}
                      >
                        <div className="course-item-header">
                          <h4>{module.title}</h4>
                          <span className="course-code">{module.code}</span>
                        </div>
                        <p>{module.difficulty}</p>
                      </div>
                    ))
                  ) : (
                    <p className="no-results">No courses match your search</p>
                  )}
                </div>
              </div>

              {coefficients && (
                <Coefficients
                  alpha={coefficients.alpha}
                  beta={coefficients.beta}
                  interactionCount={coefficients.interactionCount}
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
