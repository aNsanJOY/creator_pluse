import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Newspaper, Zap, TrendingUp } from 'lucide-react'
import { Button } from '../components/ui/Button'

export function Home() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Welcome to CreatorPulse
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your AI-powered newsletter assistant. Curate, draft, and send newsletters in under 20 minutes.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mb-4">
              <Newspaper className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Source Aggregation</h3>
            <p className="text-gray-600">
              Connect Twitter, YouTube, and RSS feeds to aggregate content from your trusted sources.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-4">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Trend Detection</h3>
            <p className="text-gray-600">
              AI-powered detection of trending topics from your connected sources.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-4">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Voice Matching</h3>
            <p className="text-gray-600">
              Learns your writing style to generate drafts that sound like you.
            </p>
          </div>
        </div>

        <div className="text-center mt-16">
          {isAuthenticated ? (
            <Link to="/dashboard">
              <Button size="lg" className="shadow-lg">
                Go to Dashboard
              </Button>
            </Link>
          ) : (
            <div className="flex gap-4 justify-center">
              <Link to="/signup">
                <Button size="lg" className="shadow-lg">
                  Get Started
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="lg" className="shadow-lg">
                  Log In
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
