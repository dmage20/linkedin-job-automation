# LinkedIn Job Automation System

An automated system for searching, analyzing, and applying to jobs on LinkedIn using React, Ruby on Rails, and GraphQL.

## 🚀 Features

- **Automated Job Search**: Scrapes LinkedIn for job postings based on configurable criteria
- **Intelligent Job Analysis**: AI-powered job matching and analysis
- **Application Management**: Tracks applications and manages the application process
- **Real-time Dashboard**: React frontend for monitoring and managing job applications
- **GraphQL API**: Efficient data querying and manipulation
- **Background Processing**: Automated job searching and application processing

## 🏗️ Architecture

### Frontend (`/frontend`)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI
- **GraphQL Client**: Apollo Client
- **Routing**: React Router v6

### Backend (`/backend`)
- **Framework**: Ruby on Rails 7
- **Database**: PostgreSQL
- **API**: GraphQL with GraphiQL
- **Background Jobs**: Sidekiq
- **Authentication**: JWT
- **Web Scraping**: Playwright integration

### Additional Directories
- **`/demo`**: Demo scripts and examples
- **`/scripts`**: Automation and build scripts
- **`/docs`**: Project documentation
- **`/deploy`**: Deployment configurations

## 📦 Installation

### Prerequisites
- Node.js 18+
- Ruby 3.2+
- PostgreSQL 14+
- Redis (for background jobs)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd linkedin-job-automation
   ```

2. **Setup Backend**
   ```bash
   cd backend
   bundle install
   rails db:create db:migrate
   rails server -p 3001
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Setup Background Jobs**
   ```bash
   cd backend
   bundle exec sidekiq
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://username:password@localhost/linkedin_job_automation_development
REDIS_URL=redis://localhost:6379
JWT_SECRET=your_jwt_secret_here
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

### Job Search Configuration

Configure search criteria in the Rails backend settings or through the GraphQL API.

## 🚦 Usage

1. **Start the application**:
   - Backend: `cd backend && rails server -p 3001`
   - Frontend: `cd frontend && npm run dev`
   - Workers: `cd backend && bundle exec sidekiq`

2. **Access the dashboard**: Navigate to `http://localhost:3000`

3. **GraphQL Playground**: Visit `http://localhost:3001/graphiql` for API exploration

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd backend
bundle exec rspec
```

## 📊 API Documentation

The GraphQL API provides the following main queries and mutations:

- **Jobs**: Search, filter, and manage job postings
- **Applications**: Track and manage job applications
- **Users**: User authentication and profile management
- **Search**: Configure and execute LinkedIn searches

Visit `/graphiql` for interactive API exploration.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use only. Please respect LinkedIn's Terms of Service and robots.txt file. Use responsibly and consider the ethical implications of automated job applications.

## 🔗 Links

- [Documentation](./docs/)
- [API Schema](./backend/app/graphql/)
- [Contributing Guide](./docs/CONTRIBUTING.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)