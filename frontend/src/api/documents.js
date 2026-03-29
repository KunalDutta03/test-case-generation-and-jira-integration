import api from './client';

export const uploadDocument = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => onProgress && onProgress(Math.round((e.loaded * 100) / e.total)),
  });
};

export const listDocuments = () => api.get('/documents');
export const getDocument = (id) => api.get(`/documents/${id}`);
export const deleteDocument = (id) => api.delete(`/documents/${id}`);
export const previewDocument = (id) => api.get(`/documents/${id}/preview`);
