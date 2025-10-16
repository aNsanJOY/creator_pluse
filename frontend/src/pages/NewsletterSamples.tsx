import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Navigation } from '../components/Navigation'
import { Upload, FileText, Trash2, AlertCircle, Loader2, CheckCircle, Sparkles, MessageCircle, Zap, BookOpen, TrendingUp } from 'lucide-react'
import newslettersService from '../services/newsletters.service'

interface NewsletterSample {
  id: string
  user_id: string
  title?: string
  content: string
  created_at: string
}

interface VoiceProfile {
  tone?: string
  style?: string
  vocabulary_level?: string
  sentence_structure?: string
  personality_traits?: string[]
  writing_patterns?: {
    uses_questions?: boolean
    uses_examples?: boolean
    uses_lists?: boolean
    uses_humor?: boolean
    uses_personal_anecdotes?: boolean
    uses_data_statistics?: boolean
  }
  content_preferences?: {
    intro_style?: string
    conclusion_style?: string
    section_transitions?: string
  }
  formatting_preferences?: {
    paragraph_length?: string
    uses_headings?: boolean
    uses_bullet_points?: boolean
    uses_emphasis?: boolean
    uses_emojis?: boolean
  }
  unique_characteristics?: string[]
  sample_phrases?: string[]
  source?: string
  samples_count?: number
  model_used?: string
}

export function NewsletterSamples() {
  const navigate = useNavigate()
  const [samples, setSamples] = useState<NewsletterSample[]>([])
  const [voiceProfile, setVoiceProfile] = useState<VoiceProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingProfile, setLoadingProfile] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  // Upload form state
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('text')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const loadSamples = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await newslettersService.getSamples()
      setSamples(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load samples')
      console.error('Failed to load samples:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadVoiceProfile = async () => {
    try {
      setLoadingProfile(true)
      const result = await newslettersService.getVoiceProfile()
      if (result.has_profile) {
        setVoiceProfile(result.voice_profile)
      }
    } catch (err: any) {
      console.error('Failed to load voice profile:', err)
    } finally {
      setLoadingProfile(false)
    }
  }

  useEffect(() => {
    loadSamples()
    loadVoiceProfile()
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (!['txt', 'md', 'html'].includes(ext || '')) {
        setError('Only .txt, .md, and .html files are supported')
        return
      }
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    try {
      setUploading(true)

      if (uploadMode === 'text') {
        if (!content.trim()) {
          setError('Please enter some content')
          return
        }
        if (content.trim().length < 10) {
          setError('Content must be at least 10 characters long')
          return
        }
        await newslettersService.uploadSample(content, title || undefined)
      } else {
        if (!selectedFile) {
          setError('Please select a file')
          return
        }
        await newslettersService.uploadSampleFile(selectedFile, title || undefined)
      }

      setSuccess('Newsletter sample uploaded successfully!')
      setTitle('')
      setContent('')
      setSelectedFile(null)
      
      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''

      // Reload samples
      await loadSamples()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload sample')
      console.error('Failed to upload sample:', err)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this sample?')) {
      return
    }

    try {
      await newslettersService.deleteSample(id)
      setSamples(samples.filter(s => s.id !== id))
      setSuccess('Sample deleted successfully')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete sample')
      console.error('Failed to delete sample:', err)
    }
  }

  const handleAnalyzeVoice = async () => {
    try {
      setAnalyzing(true)
      setError(null)
      const result = await newslettersService.analyzeVoice()
      setSuccess(result.message || 'Voice analysis completed successfully!')
      // Reload voice profile after analysis
      await loadVoiceProfile()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze voice')
      console.error('Failed to analyze voice:', err)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
      {/* Header */}
      <Navigation currentPage="Voice Training" />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Train Your Writing Voice
          </h2>
          <p className="text-gray-600">
            Upload sample newsletters to help AI learn your unique writing style and tone.
          </p>
        </div>

        {/* Success Message */}
        {success && (
          <Card className="mb-6 border-l-4 border-green-500">
            <CardContent className="flex items-center gap-3 py-4">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <p className="text-green-700">{success}</p>
            </CardContent>
          </Card>
        )}

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-l-4 border-red-500">
            <CardContent className="flex items-center gap-3 py-4">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Newsletter Sample
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpload} className="space-y-4">
                {/* Upload Mode Toggle */}
                <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
                  <button
                    type="button"
                    onClick={() => setUploadMode('text')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                      uploadMode === 'text'
                        ? 'bg-white text-purple-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Paste Text
                  </button>
                  <button
                    type="button"
                    onClick={() => setUploadMode('file')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                      uploadMode === 'file'
                        ? 'bg-white text-purple-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Upload File
                  </button>
                </div>

                {/* Title Input */}
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                    Title (Optional)
                  </label>
                  <input
                    type="text"
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Weekly Tech Update #42"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Content Input (Text Mode) */}
                {uploadMode === 'text' && (
                  <div>
                    <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
                      Newsletter Content *
                    </label>
                    <textarea
                      id="content"
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      placeholder="Paste your newsletter content here..."
                      rows={10}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Minimum 10 characters required
                    </p>
                  </div>
                )}

                {/* File Input (File Mode) */}
                {uploadMode === 'file' && (
                  <div>
                    <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-1">
                      Select File *
                    </label>
                    <input
                      type="file"
                      id="file-upload"
                      accept=".txt,.md,.html"
                      onChange={handleFileChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Supported formats: .txt, .md, .html
                    </p>
                    {selectedFile && (
                      <p className="text-sm text-purple-600 mt-2">
                        Selected: {selectedFile.name}
                      </p>
                    )}
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={uploading}
                  className="w-full"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Sample
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Voice Analysis Card */}
          <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-purple-900">
                <Sparkles className="w-5 h-5" />
                Voice Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-purple-800">
                Once you've uploaded 3-5 newsletter samples, click the button below to analyze your writing style.
              </p>
              
              <div className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Samples Uploaded</span>
                  <span className="text-lg font-bold text-purple-600">{samples.length}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min((samples.length / 5) * 100, 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {samples.length < 3 ? `Upload ${3 - samples.length} more sample${3 - samples.length === 1 ? '' : 's'} to get started` : 'Ready for analysis!'}
                </p>
              </div>

              <Button
                onClick={handleAnalyzeVoice}
                disabled={analyzing}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Analyze My Voice
                  </>
                )}
              </Button>

              <div className="text-xs text-purple-700 space-y-1">
                <p className="font-medium">What happens during analysis:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>AI extracts your writing patterns</li>
                  <li>Identifies your unique tone and style</li>
                  <li>Creates a personalized voice profile</li>
                  <li>Uses profile for future draft generation</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Voice Profile Overview */}
        {voiceProfile && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl font-bold text-gray-900">
                Your Voice Profile
              </h3>
              {voiceProfile.source === 'analyzed' && (
                <span className="text-sm text-green-600 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" />
                  AI Analyzed
                </span>
              )}
              {voiceProfile.source === 'default' && (
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  Default Profile
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Tone Card */}
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2 text-blue-900">
                    <MessageCircle className="w-4 h-4" />
                    Tone
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-lg font-semibold text-blue-900 capitalize">
                    {voiceProfile.tone || 'Not analyzed'}
                  </p>
                </CardContent>
              </Card>

              {/* Style Card */}
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2 text-purple-900">
                    <Zap className="w-4 h-4" />
                    Style
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-lg font-semibold text-purple-900 capitalize">
                    {voiceProfile.style || 'Not analyzed'}
                  </p>
                </CardContent>
              </Card>

              {/* Vocabulary Card */}
              <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2 text-green-900">
                    <BookOpen className="w-4 h-4" />
                    Vocabulary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-lg font-semibold text-green-900 capitalize">
                    {voiceProfile.vocabulary_level || 'Not analyzed'}
                  </p>
                </CardContent>
              </Card>

              {/* Samples Count Card */}
              <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2 text-orange-900">
                    <TrendingUp className="w-4 h-4" />
                    Samples Analyzed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-lg font-semibold text-orange-900">
                    {voiceProfile.samples_count || 0}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Detailed Characteristics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Personality Traits */}
              {voiceProfile.personality_traits && voiceProfile.personality_traits.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Personality Traits</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {voiceProfile.personality_traits.map((trait, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Writing Patterns */}
              {voiceProfile.writing_patterns && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Writing Patterns</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {voiceProfile.writing_patterns.uses_questions !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Questions</span>
                          <span className={voiceProfile.writing_patterns.uses_questions ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.writing_patterns.uses_questions ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                      {voiceProfile.writing_patterns.uses_examples !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Examples</span>
                          <span className={voiceProfile.writing_patterns.uses_examples ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.writing_patterns.uses_examples ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                      {voiceProfile.writing_patterns.uses_lists !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Lists</span>
                          <span className={voiceProfile.writing_patterns.uses_lists ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.writing_patterns.uses_lists ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                      {voiceProfile.writing_patterns.uses_humor !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Humor</span>
                          <span className={voiceProfile.writing_patterns.uses_humor ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.writing_patterns.uses_humor ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Content Preferences */}
              {voiceProfile.content_preferences && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Content Preferences</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {voiceProfile.content_preferences.intro_style && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Intro Style</p>
                        <p className="text-sm text-gray-700">{voiceProfile.content_preferences.intro_style}</p>
                      </div>
                    )}
                    {voiceProfile.content_preferences.conclusion_style && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Conclusion Style</p>
                        <p className="text-sm text-gray-700">{voiceProfile.content_preferences.conclusion_style}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Formatting Preferences */}
              {voiceProfile.formatting_preferences && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Formatting Preferences</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {voiceProfile.formatting_preferences.paragraph_length && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Paragraph Length</span>
                          <span className="text-gray-900 font-medium capitalize">
                            {voiceProfile.formatting_preferences.paragraph_length}
                          </span>
                        </div>
                      )}
                      {voiceProfile.formatting_preferences.uses_headings !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Headings</span>
                          <span className={voiceProfile.formatting_preferences.uses_headings ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.formatting_preferences.uses_headings ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                      {voiceProfile.formatting_preferences.uses_bullet_points !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Bullet Points</span>
                          <span className={voiceProfile.formatting_preferences.uses_bullet_points ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.formatting_preferences.uses_bullet_points ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                      {voiceProfile.formatting_preferences.uses_emojis !== undefined && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">Uses Emojis</span>
                          <span className={voiceProfile.formatting_preferences.uses_emojis ? 'text-green-600 font-medium' : 'text-gray-400'}>
                            {voiceProfile.formatting_preferences.uses_emojis ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Unique Characteristics */}
            {voiceProfile.unique_characteristics && voiceProfile.unique_characteristics.length > 0 && (
              <Card className="mt-6 bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
                <CardHeader>
                  <CardTitle className="text-base text-indigo-900">Unique Characteristics</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {voiceProfile.unique_characteristics.map((char, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-indigo-800">
                        <span className="text-indigo-600 mt-1">•</span>
                        <span>{char}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Samples List */}
        <div className="mt-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Your Newsletter Samples ({samples.length})
          </h3>

          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
            </div>
          )}

          {!loading && samples.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <div className="max-w-md mx-auto">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileText className="w-8 h-8 text-purple-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    No samples uploaded yet
                  </h3>
                  <p className="text-gray-600">
                    Upload your first newsletter sample to start training your AI writing voice.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {!loading && samples.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {samples.map((sample) => (
                <Card key={sample.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-base line-clamp-1">
                          {sample.title || 'Untitled Sample'}
                        </CardTitle>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(sample.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(sample.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 line-clamp-4">
                      {sample.content}
                    </p>
                    <p className="text-xs text-gray-400 mt-2">
                      {sample.content.length} characters
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Info Card */}
        <Card className="mt-8 bg-purple-50 border border-purple-200">
          <CardHeader>
            <CardTitle className="text-purple-900">Tips for Better Voice Training</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-purple-800">
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-600 rounded-full mt-1.5"></div>
                <span>Upload 3-5 diverse newsletter samples for best results</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-600 rounded-full mt-1.5"></div>
                <span>Include different types of content (announcements, tutorials, updates)</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-600 rounded-full mt-1.5"></div>
                <span>Ensure samples represent your desired writing style</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-600 rounded-full mt-1.5"></div>
                <span>Re-analyze your voice after uploading new samples</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
