import apiClient from './api'

export interface UserProfile {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface UpdateProfileData {
  full_name?: string
  email?: string
}

class UserService {
  async getProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>('/api/user/profile')
    return response.data
  }

  async updateProfile(data: UpdateProfileData): Promise<UserProfile> {
    const response = await apiClient.put<UserProfile>('/api/user/profile', data)
    return response.data
  }

  async deleteAccount(): Promise<{ message: string; detail: string }> {
    const response = await apiClient.delete<{ message: string; detail: string }>('/api/user/account')
    return response.data
  }
}

export default new UserService()
