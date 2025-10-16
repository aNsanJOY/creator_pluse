# Changelog

All notable changes to CreatorPulse will be documented in this file.

## [Unreleased]

### Added - Phase 1 Complete (2025-10-13)

#### Infrastructure
- Initialized Git repository with comprehensive .gitignore
- Set up backend with FastAPI framework
- Set up frontend with React + Vite + TypeScript
- Configured TailwindCSS with custom design system
- Created complete project structure (50+ files)

#### Backend
- FastAPI application with CORS configuration
- Core modules: config, security (JWT), database (Supabase)
- Pydantic schemas for all data models
- API dependencies for authentication
- Database schema with 7 tables and RLS policies
- Testing setup with pytest
- Requirements.txt with 30+ dependencies

#### Frontend
- React 18 with TypeScript and Vite
- API service layer for all backend endpoints
- AuthContext for state management
- Reusable UI components (Button, Input, Card)
- ProtectedRoute component
- ESLint configuration
- Package.json with 20+ dependencies

#### Database
- Users table with voice profile support
- Sources table (extensible for any source type)
- Source content cache table
- Newsletters table (drafts and sent)
- Newsletter samples table (voice training)
- Feedback table (thumbs up/down)
- Trends table
- Row Level Security policies
- Indexes and triggers

#### Documentation
- Main README.md with project overview
- QUICK_START.md for rapid setup
- GETTING_STARTED.md comprehensive guide
- EXTERNAL_SERVICES_SETUP.md for all services
- SUPABASE_SETUP.md for database configuration
- PHASE1_COMPLETE.md summary
- Backend and Frontend specific READMEs

### Added - Extensibility Update (2025-10-13)

#### Plugin Architecture
- BaseSourceConnector abstract class
- SourceRegistry for connector management
- SourceContent standardized format
- RSS connector implementation (example)

#### Database Updates
- Removed CHECK constraint on source_type
- Added config JSONB column to sources table
- Updated table and column comments
- Support for unlimited source types

#### Backend Updates
- Flexible source_type validation (string instead of enum)
- Added config field to all source schemas
- Expanded SourceType enum with new types
- Source validator for lowercase normalization

#### Frontend Updates
- Updated source_type to accept any string
- Added config field to Source interfaces
- Expanded SourceType definition
- Fixed TypeScript environment types

#### Documentation
- ADDING_NEW_SOURCES.md comprehensive guide
- Source connectors README.md
- EXTENSIBILITY_UPDATE.md summary
- Updated plan.md with Phase 3.6

#### New Source Types Supported
- twitter (planned)
- youtube (planned)
- rss (implemented)
- substack (documented)
- medium (documented)
- linkedin (documented)
- podcast (documented)
- newsletter (documented)
- custom (user-defined)

### Changed
- source_type from enum to string for flexibility
- Database schema to support extensible sources
- Pydantic schemas to allow any source type
- Frontend TypeScript types for source flexibility

### Technical Debt
- None! Clean implementation from the start

## [0.1.0] - Phase 1 Complete - 2025-10-13

### Summary
- Complete project infrastructure
- Extensible source system
- Comprehensive documentation
- Ready for Phase 2 development

---

## Version Format

We follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for new functionality (backward compatible)
- PATCH version for bug fixes (backward compatible)

## Phases

- **Phase 1**: Project Setup & Infrastructure ✅
- **Phase 2**: Authentication & User Management (Next)
- **Phase 3**: Source Connection System
- **Phase 4**: Voice Training System
- **Phase 5**: Content Aggregation & Trend Detection
- **Phase 6**: Newsletter Draft Generation
- **Phase 7**: Feedback Loop
- **Phase 8**: Newsletter Publishing
- **Phase 9**: Dashboard (Optional)
- **Phase 10**: Testing & QA
- **Phase 11**: Security & Compliance
- **Phase 12**: Private Beta Launch
- **Phase 13**: Public MVP Launch
