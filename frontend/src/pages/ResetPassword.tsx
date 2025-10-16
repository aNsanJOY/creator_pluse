import { useState, FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import authService from '../services/auth.service'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { KeyRound, Mail, Lock, CheckCircle } from 'lucide-react'

export function ResetPassword() {
  const [searchParams] = useSearchParams()
  const resetToken = searchParams.get('token')
  
  const [email, setEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const step = resetToken ? 'confirm' : 'request'
  
  const navigate = useNavigate()

  const handleRequestReset = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!email) {
      setError('Email is required')
      return
    }

    setLoading(true)

    try {
      const response = await authService.requestPasswordReset(email)
      setSuccess(response.message)
      
      // In development, if we get a token back, show it
      if (response.reset_token) {
        setSuccess(`${response.message}. Token: ${response.reset_token}`)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to request password reset')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmReset = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!newPassword || !confirmPassword) {
      setError('Both password fields are required')
      return
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (!resetToken) {
      setError('Invalid reset token')
      return
    }

    setLoading(true)

    try {
      await authService.confirmPasswordReset(resetToken, newPassword)
      setSuccess('Password successfully reset! Redirecting to login...')
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <KeyRound className="w-8 h-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl">
            {step === 'request' ? 'Reset your password' : 'Set new password'}
          </CardTitle>
          <p className="text-gray-600 mt-2">
            {step === 'request' 
              ? 'Enter your email to receive reset instructions'
              : 'Enter your new password below'
            }
          </p>
        </CardHeader>

        <CardContent>
          {step === 'request' ? (
            <form onSubmit={handleRequestReset} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {success && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{success}</span>
                </div>
              )}

              <div className="relative">
                <Mail className="absolute left-3 top-9 w-5 h-5 text-gray-400" />
                <Input
                  label="Email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="pl-10"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? 'Sending...' : 'Send reset instructions'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleConfirmReset} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {success && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{success}</span>
                </div>
              )}

              <div className="relative">
                <Lock className="absolute left-3 top-9 w-5 h-5 text-gray-400" />
                <Input
                  label="New Password"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="pl-10"
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-3 top-9 w-5 h-5 text-gray-400" />
                <Input
                  label="Confirm New Password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="pl-10"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? 'Resetting...' : 'Reset password'}
              </Button>
            </form>
          )}

          <div className="mt-6 text-center">
            <Link to="/login" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
              Back to login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
