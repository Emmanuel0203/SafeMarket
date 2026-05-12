import { createContext, useContext, useState } from 'react'
import { loginUser, registerUser } from '../services/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('sm_user')) } catch { return null }
  })
  const [loading, setLoading] = useState(false)

  const login = async (email, password) => {
    setLoading(true)
    try {
      const data = await loginUser(email, password)
      const userObj = data.user
      localStorage.setItem('sm_user', JSON.stringify(userObj))
      setUser(userObj)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message || 'Error al iniciar sesión' }
    } finally {
      setLoading(false)
    }
  }

  const register = async (formData) => {
    setLoading(true)
    try {
      const data = await registerUser(formData)
      const userObj = { id: data.user_id, email: data.email, role: data.role }
      localStorage.setItem('sm_user', JSON.stringify(userObj))
      setUser(userObj)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message || 'Error al registrarse' }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('sm_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)