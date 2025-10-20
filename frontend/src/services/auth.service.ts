import apiClient from './api'

export interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface SignupCredentials {
  email: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', credentials)
    const { access_token } = response.data
    localStorage.setItem('access_token', access_token)
    return response.data
  }

  async signup(credentials: SignupCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/auth/signup', credentials)
    const { access_token } = response.data
    localStorage.setItem('access_token', access_token)
    return response.data
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me')
    return response.data
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }

  getToken(): string | null {
    return localStorage.getItem('access_token')
  }
}

export default new AuthService()