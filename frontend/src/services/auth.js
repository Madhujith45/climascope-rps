/**
 * ClimaScope - Authentication Service
 * Handles user authentication with JWT tokens.
 * Uses relative URLs so requests go through the Vite dev-server proxy.
 */

import axios from 'axios'

// Use relative URLs → Vite proxy forwards /auth/* to the backend.
// For production builds, set VITE_BACKEND_URL to the real backend origin.
const BASE = import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') || ''

const api = axios.create({
  baseURL: BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const signup = async (userData) => {
  try {
    const response = await api.post('/auth/signup', userData)
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Signup failed')
  }
}

export const login = async (credentials) => {
  try {
    const response = await api.post('/auth/login', credentials)
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Login failed')
  }
}

export const forgotPassword = async (email) => {
  try {
    const response = await api.post('/auth/forgot-password', { email })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to request password reset')
  }
}

export const verifyOtp = async (email, otp) => {
  try {
    const response = await api.post('/auth/verify-otp', { email, otp })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Invalid OTP')
  }
}

export const resetPassword = async (email, newPassword, resetToken) => {
  try {
    const response = await api.post('/auth/reset-password', {
      email,
      new_password: newPassword,
      reset_token: resetToken
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to reset password')
  }
}

export const logout = async () => {
  try {
    await api.post('/auth/logout')
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  } catch (error) {
    // Even if API call fails, clear local storage
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }
}

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}

export const isAuthenticated = () => {
  return !!localStorage.getItem('token')
}

export const getAuthToken = () => {
  return localStorage.getItem('token')
}
