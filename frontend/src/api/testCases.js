import api from './client';

export const generateTestCases = (payload) => api.post('/test-cases/generate', payload);
export const listTestCases = (params) => api.get('/test-cases', { params });
export const getTestCase = (id) => api.get(`/test-cases/${id}`);
export const updateStatus = (id, status, comment) =>
  api.patch(`/test-cases/${id}/status`, { status, comment });
export const editTestCase = (id, gherkin_text, scenario) =>
  api.put(`/test-cases/${id}`, { gherkin_text, scenario });
export const bulkUpdateStatus = (test_case_ids, status, comment) =>
  api.post('/test-cases/bulk-status', { test_case_ids, status, comment });
export const deleteTestCase = (id) => api.delete(`/test-cases/${id}`);
