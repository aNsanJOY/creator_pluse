# Navigation System

## Overview
The CreatorPulse frontend features a unified navigation system that provides consistent access to all major features across the application.

## Navigation Component

### Location
`frontend/src/components/Navigation.tsx`

### Features
- **Responsive Design**: Desktop and mobile-friendly navigation
- **Active Page Highlighting**: Current page is visually indicated
- **Quick Access**: One-click access to all major sections
- **Breadcrumb Display**: Shows current location in app
- **Logout Functionality**: Integrated logout button

### Navigation Items

| Page | Route | Icon | Description |
|------|-------|------|-------------|
| Dashboard | `/dashboard` | Home | Main overview and quick actions |
| Sources | `/sources` | Rss | Manage content sources (Twitter, YouTube, RSS) |
| Voice Training | `/voice-training` | Sparkles | Upload samples and train AI voice |
| Profile | `/profile` | User | User settings and account management |

## Usage

### In Pages
```tsx
import { Navigation } from '../components/Navigation'

export function MyPage() {
  return (
    <div className="min-h-screen">
      <Navigation currentPage="My Page" />
      {/* Page content */}
    </div>
  )
}
```

### Props
- `currentPage` (optional): String - Name of the current page for breadcrumb display

## Dashboard Quick Actions

The Dashboard page includes a "Quick Actions" card with direct links to:

1. **Connect Sources** → `/sources`
   - Icon: Rss
   - Add Twitter, YouTube, RSS feeds

2. **Train Your Voice** → `/voice-training`
   - Icon: Sparkles
   - Upload newsletter samples for AI training

3. **View Drafts** → Coming soon
   - Icon: FileText
   - Review generated newsletter drafts

4. **Profile Settings** → `/profile`
   - Icon: User
   - Manage account settings

## Mobile Navigation

On mobile devices (< 768px):
- Navigation items appear below the header
- Flex wrap layout for better mobile UX
- Same functionality as desktop
- Touch-friendly button sizes

## Styling

### Desktop
- Horizontal navigation bar
- Items displayed in header
- Active page highlighted with primary button style
- Inactive pages use ghost button style

### Mobile
- Vertical stacked navigation
- Appears below header
- Wraps to multiple rows if needed
- Same color scheme as desktop

## Implementation Details

### Active Page Detection
```tsx
const isActive = currentPage === item.name
```

### Button Variants
- **Active**: `variant="primary"` (blue background)
- **Inactive**: `variant="ghost"` (transparent, hover effect)

### Icons
All navigation items use Lucide React icons:
- `Home` - Dashboard
- `Rss` - Sources
- `Sparkles` - Voice Training
- `User` - Profile
- `LogOut` - Logout button

## Pages Using Navigation

### ✅ Implemented
- [x] Sources (`/sources`)
- [x] Voice Training (`/voice-training`)

### 🔄 To Be Updated
- [ ] Dashboard (`/dashboard`) - Has quick actions, could add nav bar
- [ ] Profile (`/profile`) - Should add navigation component

## Future Enhancements

- [ ] Dropdown menus for sub-sections
- [ ] Notification badges
- [ ] Search functionality
- [ ] Keyboard shortcuts
- [ ] Breadcrumb navigation for nested pages
- [ ] Recently visited pages
- [ ] Favorites/pinned pages

## Accessibility

- Keyboard navigation support
- ARIA labels for screen readers
- Focus indicators on all interactive elements
- Semantic HTML structure

## Responsive Breakpoints

- **Desktop**: ≥ 768px (md breakpoint)
  - Horizontal navigation in header
  - All items visible

- **Mobile**: < 768px
  - Vertical navigation below header
  - Wrapped layout
  - Logout button always visible

## Code Example

### Full Implementation
```tsx
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from './ui/Button'
import { LogOut, Home, Rss, Sparkles, User } from 'lucide-react'

export function Navigation({ currentPage }: { currentPage?: string }) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Sources', path: '/sources', icon: Rss },
    { name: 'Voice Training', path: '/voice-training', icon: Sparkles },
    { name: 'Profile', path: '/profile', icon: User },
  ]

  return (
    <header className="bg-white shadow-sm">
      {/* Navigation content */}
    </header>
  )
}
```

## Related Components

- `Button` - UI component for navigation items
- `AuthContext` - Provides logout functionality
- React Router - Handles navigation routing

## Testing

### Manual Testing
1. Navigate to each page
2. Verify active page is highlighted
3. Click navigation items
4. Test on mobile and desktop
5. Verify logout functionality

### Automated Testing (Future)
- Component rendering tests
- Navigation click tests
- Active state tests
- Responsive layout tests

## Troubleshooting

### Navigation Not Showing
- Ensure component is imported correctly
- Check that it's placed in the page component
- Verify routing is set up in App.tsx

### Active Page Not Highlighted
- Ensure `currentPage` prop matches navigation item name exactly
- Check button variant logic

### Mobile Navigation Issues
- Verify Tailwind breakpoints
- Check responsive classes (md:hidden, md:flex)
- Test on actual mobile devices

## Best Practices

1. **Consistent Naming**: Use exact page names for `currentPage` prop
2. **Icon Usage**: Use appropriate Lucide icons for visual clarity
3. **Accessibility**: Always include proper ARIA labels
4. **Mobile First**: Design for mobile, enhance for desktop
5. **Performance**: Minimize re-renders with proper React patterns

## Migration Guide

### Updating Existing Pages

**Before:**
```tsx
<header className="bg-white shadow-sm">
  <div className="max-w-7xl mx-auto px-4 py-4">
    <h1 onClick={() => navigate('/dashboard')}>CreatorPulse</h1>
    <Button onClick={handleLogout}>Logout</Button>
  </div>
</header>
```

**After:**
```tsx
<Navigation currentPage="Your Page Name" />
```

### Benefits
- ✅ Consistent navigation across all pages
- ✅ Reduced code duplication
- ✅ Easier maintenance
- ✅ Better UX with active page indication
- ✅ Mobile-responsive out of the box

## Version History

- **v1.0** (Oct 2025): Initial navigation component
  - Basic navigation with 4 main sections
  - Mobile responsive design
  - Active page highlighting
  - Integrated logout

## Support

For issues or questions about navigation:
1. Check this documentation
2. Review component code in `frontend/src/components/Navigation.tsx`
3. Test in browser dev tools
4. Check console for errors
