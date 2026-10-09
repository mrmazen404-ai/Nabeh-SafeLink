import axios from 'axios';
import { getAccessToken } from './authToken';

const API_URL = import.meta.env.VITE_API_URL || (
  import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1'
);

if (
  import.meta.env.PROD &&
  /^https?:\/\//i.test(API_URL) &&
  new URL(API_URL).protocol !== 'https:'
) {
  throw new Error('VITE_API_URL must use HTTPS in production.');
}

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    if (!config.headers.Authorization) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const scanURL = async (inputValue, language = 'ar', isGuest = true, inputType = 'URL') => {
  const endpoint = isGuest ? '/scans/guest' : '/scans/';
  const response = await api.post(endpoint, {
    input_type: inputType,
    input_value: inputValue,
    language,
  });
  return response.data;
};

export const getScans = async () => {
  const response = await api.get('/scans/');
  return response.data;
};

export const getScanDetails = async (scanId) => {
  const response = await api.get(`/scans/${encodeURIComponent(scanId)}`);
  return response.data;
};

export const compareScans = async (scanIds) => {
  const response = await api.get(`/scans/compare?ids=${scanIds.map(encodeURIComponent).join(',')}`);
  return response.data;
};

export const getStatistics = async () => {
  const response = await api.get('/statistics/me');
  return response.data;
};

export const submitSupportRequest = async ({ requestType, email, subject, scanId, details }) => {
  const response = await api.post('/support/contact', {
    request_type: requestType,
    email,
    subject,
    scan_id: scanId || null,
    details,
  });
  return response.data;
};

export default api;
