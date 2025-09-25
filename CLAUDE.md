# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (React + TypeScript + Vite)
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start development server (http://localhost:3000)
npm run build        # Build for production
npm run lint         # Run ESLint
npm run preview      # Preview production build
```

### Backend (Rails 7 + GraphQL)
```bash
cd backend
bundle install       # Install Ruby dependencies
rails db:create      # Create database
rails db:migrate     # Run migrations
rails server -p 3001 # Start Rails server (http://localhost:3001)
bundle exec rspec    # Run test suite
bundle exec sidekiq  # Start background job worker
```

### Testing
- Frontend: `cd frontend && npm test`
- Backend: `cd backend && bundle exec rspec`

## Architecture Overview

### Tech Stack
- **Frontend**: React 18 + TypeScript, Vite build tool, Material-UI components, Apollo Client for GraphQL
- **Backend**: Rails 7 API-only, GraphQL with GraphiQL, PostgreSQL database, Sidekiq for background jobs
- **Authentication**: JWT tokens
- **Web Scraping**: LinkedIn automation using Playwright integration

### Key Directories
```
frontend/src/
├── components/     # React components
├── pages/          # Page-level components
├── hooks/          # Custom React hooks
├── services/       # API calls and external services
├── types/          # TypeScript type definitions
└── utils/          # Utility functions

backend/app/
├── controllers/    # API endpoints
├── graphql/        # GraphQL schema and resolvers
├── models/         # ActiveRecord models
├── jobs/           # Sidekiq background jobs
└── services/       # Business logic services
```

### Data Flow
1. React frontend communicates with Rails backend via GraphQL API
2. Background jobs handle LinkedIn scraping and job processing via Sidekiq
3. PostgreSQL stores job data, applications, and user information
4. Redis powers background job queue and caching

### Key Configuration
- Backend runs on port 3001, frontend on port 3000
- GraphQL playground available at http://localhost:3001/graphiql
- Environment variables configured via `.env` file in backend directory
- Database: PostgreSQL, Redis required for background jobs

### Common Patterns
- GraphQL mutations and queries for all API interactions
- Material-UI components for consistent styling
- Background jobs for LinkedIn scraping operations
- JWT authentication for API access