import apiClient from './api'

export interface Feedback {
  id: string
  user_id: string
  newsletter_id: string
  feedback_type: 'thumbs_up' | 'thumbs_down'
  section_id?: string
  comment?: string
  created_at: string
}

export interface CreateFeedbackData {
  newsletter_id: string
  feedback_type: 'thumbs_up' | 'thumbs_down'
  section_id?: string
  comment?: string
}

class FeedbackService {
  async submitFeedback(data: CreateFeedbackData): Promise<Feedback> {
    const response = await apiClient.post<Feedback>('/api/feedback', data)
    return response.data
  }

  async getUserFeedback(userId: string): Promise<Feedback[]> {
    const response = await apiClient.get<Feedback[]>(`/api/feedback/user/${userId}`)
    return response.data
  }
}

export default new FeedbackService()
