import axios from 'axios'
import { useAuthStore } from '../store/authStore'

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
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
}

export const boards = {
  list: () => api.get('/boards'),
  get: (id: string) => api.get(`/boards/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post('/boards', data),
  update: (id: string, data: { name: string; description?: string }) =>
    api.put(`/boards/${id}`, data),
  delete: (id: string) => api.delete(`/boards/${id}`),
}

export const lists = {
  create: (boardId: string, data: { name: string; position: number }) =>
    api.post(`/boards/${boardId}/lists`, data),
}

export const cards = {
  create: (listId: string, data: { title: string; description?: string }) =>
    api.post(`/lists/${listId}/cards`, data),
  move: (cardId: string, data: { list_id: string; position: number }) =>
    api.put(`/cards/${cardId}/move`, data),
}

export const monitors = {
  list: () => api.get('/monitors'),
  get: (id: string) => api.get(`/monitors/${id}`),
  create: (data: { name: string; url: string; interval?: number }) =>
    api.post('/monitors', data),
  uptime: (id: string, hours: number = 24) =>
    api.get(`/monitors/${id}/uptime`, { params: { hours } }),
  check: (id: string) => api.post(`/monitors/${id}/check`),
}

export const dashboard = {
  metrics: () => api.get('/metrics/dashboard'),
  statusPage: () => api.get('/status-page'),
}
