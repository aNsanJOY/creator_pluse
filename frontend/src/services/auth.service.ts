import apiClient from './api'

export interface LoginCredentials {
  email: string
  password: string
}

export interface SignupData {
  email: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', credentials)
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
    }
    return response.data
  }

  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/auth/signup', data)
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
    }
    return response.data
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/auth/logout')
    } finally {
      localStorage.removeItem('access_token')
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/user/profile')
    return response.data
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }

  getToken(): string | null {
    return localStorage.getItem('access_token')
  }

  async requestPasswordReset(email: string): Promise<{ message: string; reset_token?: string }> {
    const response = await apiClient.post('/api/auth/reset-password', null, {
      params: { email }
    })
    return response.data
  }

  async confirmPasswordReset(resetToken: string, newPassword: string): Promise<{ message: string }> {
    const response = await apiClient.post('/api/auth/reset-password/confirm', null, {
      params: {
        reset_token: resetToken,
        new_password: newPassword
      }
    })
    return response.data
  }
}

export default new AuthService()
