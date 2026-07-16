/**
 * contexts/AuthContext.jsx
 * Contexto global de autenticação — persiste sessão no localStorage.
 */
import { createContext, useContext, useState, useCallback } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
  })
  const [token, setToken] = useState(() => localStorage.getItem('token') || null)

  const login = useCallback(async (username, password) => {
    const res   = await authAPI.login({ username, password })
    const t     = res.data.access_token
    const uData = { username }
    localStorage.setItem('token', t)
    localStorage.setItem('user', JSON.stringify(uData))
    setToken(t)
    setUser(uData)
  }, [])

  const register = useCallback(async (data) => {
    await authAPI.register(data)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
