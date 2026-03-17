import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  r => r,
  err => {
    const msg = err.response?.data?.error || err.message || 'Something went wrong';
    return Promise.reject(new Error(typeof msg === 'object' ? JSON.stringify(msg) : msg));
  }
);

export const getWorkflows = (params) => api.get('/workflows', { params });
export const getWorkflow = (id) => api.get(`/workflows/${id}`);
export const createWorkflow = (data) => api.post('/workflows', data);
export const updateWorkflow = (id, data) => api.put(`/workflows/${id}`, data);
export const deleteWorkflow = (id) => api.delete(`/workflows/${id}`);

export const getSteps = (workflowId) => api.get(`/workflows/${workflowId}/steps`);
export const createStep = (workflowId, data) => api.post(`/workflows/${workflowId}/steps`, data);
export const updateStep = (id, data) => api.put(`/steps/${id}`, data);
export const deleteStep = (id) => api.delete(`/steps/${id}`);

export const getRules = (stepId) => api.get(`/steps/${stepId}/rules`);
export const createRule = (stepId, data) => api.post(`/steps/${stepId}/rules`, data);
export const updateRule = (id, data) => api.put(`/rules/${id}`, data);
export const deleteRule = (id) => api.delete(`/rules/${id}`);

export const executeWorkflow = (workflowId, data) => api.post(`/workflows/${workflowId}/execute`, data);
export const getExecution = (id) => api.get(`/executions/${id}`);
export const getExecutions = (params) => api.get('/executions', { params });
export const cancelExecution = (id) => api.post(`/executions/${id}/cancel`);
export const retryExecution = (id) => api.post(`/executions/${id}/retry`);
export const approveStep = (execId, data) => api.post(`/executions/${execId}/approve`, data);

export default api;
