import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import type { Board, List, Card, Monitor, StatusData, ActivityEntry } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API functions
export const auth = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string }>('/auth/login', { email, password }),
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
}

export const boards = {
  list: () => api.get<Board[]>('/boards'),
  get: (id: string) => api.get<Board>(`/boards/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post<Board>('/boards', data),
  update: (id: string, data: { name: string; description?: string }) =>
    api.put<Board>(`/boards/${id}`, data),
  delete: (id: string) => api.delete(`/boards/${id}`),
  activity: (boardId: string, limit = 20) =>
    api.get<ActivityEntry[]>(`/boards/${boardId}/activity?limit=${limit}`),
}

export const lists = {
  create: (boardId: string, data: { name: string; position: number }) =>
    api.post<List>(`/boards/${boardId}/lists`, data),
}

export const cards = {
  create: (listId: string, data: { title: string; description?: string }) =>
    api.post<Card>(`/lists/${listId}/cards`, data),
  move: (cardId: string, data: { list_id: string; position: number }) =>
    api.put<Card>(`/cards/${cardId}/move`, data),
}

export interface CheckResponse {
  status: string
  check_id: string
}

export const monitors = {
  list: () => api.get<Monitor[]>('/monitors'),
  get: (id: string) => api.get<Monitor>(`/monitors/${id}`),
  create: (data: { name: string; url: string; interval?: number }) =>
    api.post<Monitor>('/monitors', data),
  uptime: (id: string, hours: number = 24) =>
    api.get<{ uptime_percentage: number; total_checks: number; failed_checks: number; avg_response_time: number | null }>(`/monitors/${id}/uptime`, { params: { hours } }),
  check: (id: string) => api.post<CheckResponse>(`/monitors/${id}/check`),
}

export const dashboard = {
  metrics: () => api.get('/metrics/dashboard'),
  statusPage: () => api.get<StatusData>('/status-page'),
}

export interface SpecResponse {
  specification: string
  type: string
  requirements: string
}

export interface TestResponse {
  test_code: string
  test_type: string
  specification: string
}

export interface DevResponse {
  code: string
  code_type: string
  specification: string
  language: string
}

export const agents = {
  spec: (data: { requirements: string; type: string }) =>
    api.post<SpecResponse>('/agents/spec', data),
  test: (data: { specification: string; type: string }) =>
    api.post<TestResponse>('/agents/test', data),
  dev: (data: { specification: string; type: string }) =>
    api.post<DevResponse>('/agents/dev', data),
}
