# CreatorPulse Frontend

React frontend for CreatorPulse - A daily feed curator and newsletter drafting assistant.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for API calls
- **Lucide React** for icons

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

3. Update the `.env` file with your backend API URL:
```env
VITE_API_URL=http://localhost:8000
```

## Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Linting

Run ESLint:
```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   └── ProtectedRoute.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx  # Authentication context
│   ├── pages/
│   │   └── Home.tsx         # Page components
│   ├── services/
│   │   ├── api.ts           # Axios instance
│   │   ├── auth.service.ts
│   │   ├── sources.service.ts
│   │   ├── newsletters.service.ts
│   │   └── feedback.service.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Available Components

### UI Components
- `Button` - Customizable button with variants (primary, secondary, outline, ghost, destructive)
- `Input` - Form input with label and error support
- `Card` - Card container with Header, Title, and Content sub-components

### Context Providers
- `AuthProvider` - Manages authentication state and user session

### Hooks
- `useAuth()` - Access authentication context (user, login, signup, logout)

## API Services

All API calls are centralized in the `services/` directory:

- **auth.service.ts** - Authentication (login, signup, logout)
- **sources.service.ts** - Source management (Twitter, YouTube, RSS)
- **newsletters.service.ts** - Newsletter drafts and samples
- **feedback.service.ts** - User feedback submission

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Features

### Phase 1 (Current)
- ✅ Project setup with Vite + React + TypeScript
- ✅ TailwindCSS configuration
- ✅ API service layer
- ✅ Authentication context
- ✅ Reusable UI components
- ✅ Protected routes

### Phase 2 (Next)
- Authentication pages (Login, Signup)
- User profile management
- Password reset flow

### Phase 3+
- Source connection interface
- Newsletter draft review
- Feedback system
- Dashboard

## Styling

This project uses TailwindCSS with a custom design system. The color palette and theme variables are defined in `src/index.css`.

### Color Scheme
- Primary: Blue (#3B82F6)
- Secondary: Gray
- Accent: Purple
- Success: Green
- Destructive: Red

## Development Tips

1. **Hot Module Replacement (HMR)** is enabled by default
2. Use the `@/` alias for imports from the `src/` directory
3. All API calls automatically include the auth token from localStorage
4. 401 responses automatically redirect to login page
5. TypeScript strict mode is enabled for better type safety

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
