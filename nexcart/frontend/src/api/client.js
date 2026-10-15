/**
 * NexCart — API Client
 * Axios instance + typed query functions for every endpoint.
 */

import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Response Interceptor ────────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';
    } else if (!error.response) {
      console.error('Network error: Cannot reach server');
    }
    return Promise.reject(error);
  }
);

// ── Dashboard & Health ──────────────────────────────────────
export const getHealth = () => client.get('/health').then(r => r.data);
export const testDbConnection = () => client.get('/health/db').then(r => r.data);
export const getStats = () => client.get('/dashboard/stats').then(r => r.data);

// ── SKUs ────────────────────────────────────────────────────
export const getSkus = (params = {}) => client.get('/skus', { params }).then(r => r.data);
export const getSku = (skuId) => client.get(`/skus/${skuId}`).then(r => r.data);
export const createSku = (data) => client.post('/skus', data).then(r => r.data);
export const overrideSkuRisk = (skuId, data) => client.patch(`/skus/${skuId}/risk`, data).then(r => r.data);

// ── Disruptions ─────────────────────────────────────────────
export const getDisruptions = (params = {}) => client.get('/disruptions', { params }).then(r => r.data);
export const getDisruption = (eventId) => client.get(`/disruptions/${eventId}`).then(r => r.data);

// ── Signals ─────────────────────────────────────────────────
export const getSignalHistory = (params = {}) => client.get('/signals/history', { params }).then(r => r.data);
export const ingestSignal = (data) => client.post('/signals/ingest', data).then(r => r.data);

// ── Nudges ──────────────────────────────────────────────────
export const getNudges = (params = {}) => client.get('/nudges', { params }).then(r => r.data);
export const getNudge = (campaignId) => client.get(`/nudges/${campaignId}`).then(r => r.data);
export const updateNudgeStatus = (campaignId, data) => client.patch(`/nudges/${campaignId}/status`, data).then(r => r.data);

// ── Analytics ───────────────────────────────────────────────
export const getRiskTrend = () => client.get('/analytics/risk-trend').then(r => r.data);
export const getNudgeConversion = () => client.get('/analytics/nudge-conversion').then(r => r.data);

// ── Agents ──────────────────────────────────────────────────
export const triggerDisruptionAgent = () => client.post('/agents/run-disruption').then(r => r.data);
export const triggerNudgeAgent = (skuIds = []) => client.post('/agents/run-nudge', { sku_ids: skuIds }).then(r => r.data);

// ── Customers ───────────────────────────────────────────────
export const getCustomers = (params = {}) => client.get('/customers', { params }).then(r => r.data);
export const createCustomer = (data) => client.post('/customers', data).then(r => r.data);

export default client;

// ✓ client.js complete
