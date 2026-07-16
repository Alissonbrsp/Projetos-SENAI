/**
 * services/api.js
 * Camada de comunicação com o backend FastAPI.
 * Injeta JWT em toda requisição e redireciona para login em caso de 401.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Injeta token em cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redireciona para login em 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.reload()
    }
    return Promise.reject(err)
  }
)

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
}

export const scannerAPI = {
  startScan: (data) => api.post('/scanner/scan', data),
  getScan:   (id)   => api.get(`/scanner/scan/${id}`),
  listScans: ()     => api.get('/scanner/scans'),
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
}

export const logsAPI = {
  getLogs: (params) => api.get('/logs/', { params }),
}

export const reportsAPI = {
  list:        (date) => api.get('/reports/', { params: date ? { date_filter: date } : {} }),
  downloadPDF: (id)   => api.get(`/reports/${id}/pdf`, { responseType: 'blob' }),
}

export default api
