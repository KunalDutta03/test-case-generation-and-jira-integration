import api from './client';

export const saveJiraConfig = (payload) => api.post('/jira/config', payload);
export const listJiraConfigs = () => api.get('/jira/config');
export const testJiraConnection = (payload) => api.post('/jira/test-connection', payload);
export const injectToJira = (test_case_ids, jira_config_id) =>
  api.post('/jira/inject', { test_case_ids, jira_config_id });
export const getJiraDefaults = () => api.get('/jira/defaults');
