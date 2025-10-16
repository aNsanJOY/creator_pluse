import apiClient from './api'

export interface Newsletter {
  id: string
  user_id: string
  title: string
  content: string
  status: 'draft' | 'sent' | 'scheduled'
  sent_at?: string
  created_at: string
  updated_at?: string
}

export interface CreateNewsletterData {
  title: string
  content: string
}

export interface UpdateNewsletterData {
  title?: string
  content?: string
  status?: 'draft' | 'sent' | 'scheduled'
}

class NewslettersService {
  async getNewsletters(): Promise<Newsletter[]> {
    const response = await apiClient.get<Newsletter[]>('/api/newsletters')
    return response.data
  }

  async getNewsletter(id: string): Promise<Newsletter> {
    const response = await apiClient.get<Newsletter>(`/api/newsletters/${id}`)
    return response.data
  }

  async getDraft(id: string): Promise<Newsletter> {
    const response = await apiClient.get<Newsletter>(`/api/drafts/${id}`)
    return response.data
  }

  async updateDraft(id: string, data: UpdateNewsletterData): Promise<Newsletter> {
    const response = await apiClient.put<Newsletter>(`/api/drafts/${id}`, data)
    return response.data
  }

  async publishDraft(id: string): Promise<void> {
    await apiClient.post(`/api/drafts/${id}/publish`)
  }

  async regenerateDraft(id: string): Promise<Newsletter> {
    const response = await apiClient.post<Newsletter>(`/api/drafts/${id}/regenerate`)
    return response.data
  }

  async uploadSample(content: string, title?: string): Promise<void> {
    await apiClient.post('/api/newsletters/upload', { content, title })
  }

  async uploadSampleFile(file: File, title?: string): Promise<void> {
    const formData = new FormData()
    formData.append('file', file)
    if (title) {
      formData.append('title', title)
    }
    
    await apiClient.post('/api/newsletters/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  async getSamples(): Promise<Array<{ id: string; user_id: string; title?: string; content: string; created_at: string }>> {
    const response = await apiClient.get('/api/newsletters/samples')
    return response.data
  }

  async deleteSample(id: string): Promise<void> {
    await apiClient.delete(`/api/newsletters/samples/${id}`)
  }

  async analyzeVoice(): Promise<{ voice_profile: any; message: string }> {
    const response = await apiClient.post('/api/voice/analyze')
    return response.data
  }

  async getVoiceProfile(): Promise<{ voice_profile: any; summary: string; has_profile: boolean; message: string }> {
    const response = await apiClient.get('/api/voice/profile')
    return response.data
  }
}

export default new NewslettersService()
