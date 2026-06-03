import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const authAPI = {
  login: (studentId) => api.post('/auth/login', { student_id: studentId })
};

export const modulesAPI = {
  getAll: () => api.get('/modules'),
  getById: (id) => api.get(`/modules/${id}`)
};

export const recommendationsAPI = {
  get: (studentId, limit = 5) => api.get('/recommendations', {
    params: { student_id: studentId, limit }
  })
};

export const interactionsAPI = {
  getStudentInteractions: (studentId) => api.get(`/students/${studentId}/interactions`),
  createOrUpdate: (studentId, moduleId, data) =>
    api.post(`/students/${studentId}/modules/${moduleId}/interact`, data)
};

export const studentAPI = {
  getProfile: (studentId) => api.get(`/students/${studentId}/profile`)
};

export default api;
