# Story UI_005: Development Workflow Setup

## Story Details
- **Story ID**: UI_005
- **Epic**: Epic 1 - Foundation Infrastructure
- **Story Points**: 3
- **Priority**: High
- **Type**: Development Infrastructure
- **Status**: Done

## User Story
**As a** developer
**I want** efficient development tools and processes
**So that** I can work productively on the application with proper code quality and team collaboration

## Acceptance Criteria

### 1. Development Environment
- [ ] Docker development environment configured and working
- [ ] docker-compose.yml for local development with hot reload
- [ ] Package managers configured (pnpm for frontend, pip for backend)
- [ ] Environment variable management system
- [ ] Local development servers start with single command

### 2. Code Quality Tools
- [ ] ESLint and Prettier configured for frontend
- [ ] Black and ruff configured for Python backend
- [ ] Pre-commit hooks installed and working
- [ ] TypeScript strict mode configuration
- [ ] Import sorting and organization rules

### 3. Development Scripts
- [ ] Package.json scripts for common development tasks
- [ ] Makefile or scripts for project setup
- [ ] Database reset and seeding scripts
- [ ] Test running scripts
- [ ] Build and deployment scripts

### 4. Documentation
- [ ] README.md with setup instructions
- [ ] Development guide with common commands
- [ ] Environment setup troubleshooting guide
- [ ] Code style guide documented
- [ ] Contributing guidelines

### 5. Version Control Setup
- [ ] .gitignore properly configured
- [ ] Git hooks for code quality checks
- [ ] Branch protection rules documented
- [ ] Commit message conventions established

## Technical Requirements

### Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=sqlite:///data/dev.db
```

### Development Scripts
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "type-check": "tsc --noEmit",
    "format": "prettier --write .",
    "test": "jest",
    "test:watch": "jest --watch",
    "setup": "pnpm install && pnpm run db:migrate"
  }
}
```

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.285
    hooks:
      - id: ruff
```

### Code Quality Configuration
```javascript
// .eslintrc.js
module.exports = {
  extends: [
    'next/core-web-vitals',
    '@typescript-eslint/recommended',
    'prettier'
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    'prefer-const': 'error',
    'no-var': 'error'
  }
}

// prettier.config.js
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
}
```

## Definition of Done
- [ ] Development environment starts with single command
- [ ] Code quality tools run automatically on commit
- [ ] Both frontend and backend hot reload work
- [ ] All development scripts execute successfully
- [ ] Documentation is complete and accurate
- [ ] New developer can set up environment in < 30 minutes
- [ ] Pre-commit hooks prevent bad code from being committed

## Testing Checklist
- [ ] `make dev` or equivalent starts all services
- [ ] Code changes trigger hot reload in browser
- [ ] Pre-commit hooks reject improperly formatted code
- [ ] Linting catches common code issues
- [ ] TypeScript compilation errors show clearly
- [ ] Environment variables load correctly
- [ ] Database migrations run successfully

## Integration Points
- **CI/CD System**: Preparation for automated testing and deployment
- **Team Collaboration**: Consistent development environment across team members
- **Code Quality**: Integration with future code review processes
- **Deployment**: Foundation for production deployment automation

## Performance Requirements
- Development server startup time < 30 seconds
- Hot reload response time < 5 seconds
- Code quality checks complete < 10 seconds
- Docker container startup < 60 seconds

## Implementation Notes
- Use consistent formatting across all configuration files
- Include comprehensive error handling in setup scripts
- Document common troubleshooting issues
- Consider different development platforms (Windows, Mac, Linux)
- Include database seeding for consistent development data

## Developer Experience Enhancements
- Auto-completion configuration for IDEs
- Debugging configuration for VS Code
- Consistent code organization patterns
- Helpful error messages in development scripts
- Quick command reference in README

## Follow-up Stories
- UI_011: System Dashboard (benefits from dev environment)
- UI_044: Production Deployment (builds on dev workflow)
- All development stories benefit from this foundation
