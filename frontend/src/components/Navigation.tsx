import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from './ui/Button'
import { LogOut, Home, Rss, Sparkles, User, FileText } from 'lucide-react'

interface NavigationProps {
  currentPage?: string
}

export function Navigation({ currentPage }: NavigationProps) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Sources', path: '/sources', icon: Rss },
    { name: 'Drafts', path: '/drafts', icon: FileText },
    { name: 'Voice Training', path: '/voice-training', icon: Sparkles },
    { name: 'Profile', path: '/profile', icon: User },
  ]

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          {/* Left side - Logo and breadcrumb */}
          <div className="flex items-center gap-4">
            <h1 
              className="text-2xl font-bold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors"
              onClick={() => navigate('/dashboard')}
            >
              CreatorPulse
            </h1>
            {currentPage && (
              <>
                <span className="text-gray-400">/</span>
                <span className="text-lg text-gray-600">{currentPage}</span>
              </>
            )}
          </div>

          {/* Right side - Navigation and logout */}
          <div className="flex items-center gap-4">
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = currentPage === item.name
                return (
                  <Button
                    key={item.path}
                    variant={isActive ? 'primary' : 'ghost'}
                    size="sm"
                    onClick={() => navigate(item.path)}
                    className="flex items-center gap-2"
                  >
                    <Icon className="w-4 h-4" />
                    {item.name}
                  </Button>
                )
              })}
            </nav>

            {/* Logout Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <nav className="md:hidden mt-4 flex flex-wrap gap-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentPage === item.name
            return (
              <Button
                key={item.path}
                variant={isActive ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => navigate(item.path)}
                className="flex items-center gap-2"
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Button>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
