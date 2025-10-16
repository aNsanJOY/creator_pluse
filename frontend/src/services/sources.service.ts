import apiClient from './api'

// Common source types (extensible)
export type SourceType = 
  | 'twitter' 
  | 'youtube' 
  | 'rss' 
  | 'substack' 
  | 'medium' 
  | 'linkedin' 
  | 'podcast' 
  | 'newsletter' 
  | 'custom'
  | string // Allow any string for future source types

export interface Source {
  id: string
  user_id: string
  source_type: string // Changed to string for flexibility
  name: string
  url?: string
  config?: Record<string, any> // Additional configuration per source
  status: 'active' | 'error' | 'pending'
  last_crawled_at?: string
  error_message?: string
  created_at: string
  updated_at?: string
}

export interface CreateSourceData {
  source_type: string // Changed to string for flexibility
  name: string
  url?: string
  credentials?: Record<string, any>
  config?: Record<string, any> // Additional configuration per source
}

export interface UpdateSourceData {
  name?: string
  url?: string
  credentials?: Record<string, any>
  config?: Record<string, any>
  status?: 'active' | 'error' | 'pending'
}

class SourcesService {
  async getSources(): Promise<Source[]> {
    const response = await apiClient.get<Source[]>('/api/sources')
    return response.data
  }

  async getSource(id: string): Promise<Source> {
    const response = await apiClient.get<Source>(`/api/sources/${id}`)
    return response.data
  }

  async createSource(data: CreateSourceData): Promise<Source> {
    const response = await apiClient.post<Source>('/api/sources', data)
    return response.data
  }

  async updateSource(id: string, data: UpdateSourceData): Promise<Source> {
    const response = await apiClient.put<Source>(`/api/sources/${id}`, data)
    return response.data
  }

  async deleteSource(id: string): Promise<void> {
    await apiClient.delete(`/api/sources/${id}`)
  }

  async getSourceStatus(id: string): Promise<{ status: string; message?: string }> {
    const response = await apiClient.get(`/api/sources/${id}/status`)
    return response.data
  }
}

export default new SourcesService()
