# Phase 6: Deployment — CI/CD & Release

## Purpose

Automate the path from code commit to production, ensuring consistent, reliable, and safe releases.

## Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **GitHub Actions** | Platform | CI/CD automation | [github.com/actions](https://github.com/features/actions) |
| **Docker** | OSS | Containerization | [docker.com](https://docker.com) |
| **Vercel** | Platform | Frontend deployment | [vercel.com](https://vercel.com) |
| **Railway** | Platform | Backend + DB deployment | [railway.app](https://railway.app) |
| **Terraform** | OSS | Infrastructure as Code | [terraform.io](https://terraform.io) |
| **ArgoCD** | OSS | Kubernetes GitOps | [argoproj.github.io](https://argoproj.github.io/cd) |

## Key Steps

```
Step 1: Containerize Your Application
  └─→ Write Dockerfiles for frontend & backend

Step 2: Set Up CI Pipeline (Build + Test)
  └─→ On every PR: lint → test → build → security scan

Step 3: Set Up CD Pipeline (Deploy)
  └─→ On merge to main: deploy to staging
  └─→ On release tag: deploy to production

Step 4: Configure Environment Management
  └─→ Development → Staging → Production
  └─→ Use environment-specific secrets

Step 5: Set Up Monitoring & Alerting
  └─→ Health checks, error tracking, performance monitoring

Step 6: Implement Rollback Strategy
  └─→ Blue-green or canary deployments for zero-downtime
```

## CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                              │
│                                                                 │
│  Developer Push                                                 │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  LINT    │→│   TEST   │→│  BUILD   │→│ SECURITY │    │
│  │ ESLint   │  │ Unit     │  │ Docker   │  │  Scan    │    │
│  │ Prettier │  │ Integr.  │  │ Image    │  │ Trivy    │    │
│  │          │  │ E2E      │  │          │  │ Snyk     │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                 │               │
│                                                 ▼               │
│                              ┌──────────────────────────┐       │
│                              │    DEPLOY TO STAGING     │       │
│                              │    (automatic on main)   │       │
│                              └────────────┬─────────────┘       │
│                                           │                     │
│                                    Manual Approval               │
│                                           │                     │
│                                           ▼                     │
│                              ┌──────────────────────────┐       │
│                              │   DEPLOY TO PRODUCTION   │       │
│                              │   (on release tag)       │       │
│                              └──────────────┬───────────┘       │
│                                             │                   │
│                                             ▼                   │
│                              ┌──────────────────────────┐       │
│                              │      MONITOR & ALERT     │       │
│                              │   Health checks, logs,   │       │
│                              │   error rates, latency   │       │
│                              └──────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Demo: Complete GitHub Actions CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ──────────────────────────────
  # Stage 1: Lint & Format Check
  # ──────────────────────────────
  lint:
    name: 🔍 Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run format:check

  # ──────────────────────────────
  # Stage 2: Unit & Integration Tests
  # ──────────────────────────────
  test:
    name: 🧪 Test
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: tasktracker_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run test:ci
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/tasktracker_test
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  # ──────────────────────────────
  # Stage 3: E2E Tests
  # ──────────────────────────────
  e2e:
    name: 🌐 E2E Tests
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - name: Upload E2E results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/

  # ──────────────────────────────
  # Stage 4: Build & Push Docker Image
  # ──────────────────────────────
  build:
    name: 🐳 Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, e2e]
    if: github.ref == 'refs/heads/main' || github.event_name == 'release'
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha
            type=ref,event=branch
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  # ──────────────────────────────
  # Stage 5: Security Scan
  # ──────────────────────────────
  security:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  # ──────────────────────────────
  # Stage 6: Deploy to Staging
  # ──────────────────────────────
  deploy-staging:
    name: 🚀 Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, security]
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.tasktracker.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # Example: Deploy to Railway, Vercel, or Kubernetes
          # railway up --environment staging
          # OR
          # kubectl set image deployment/tasktracker \
          #   api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
      - name: Run smoke tests
        run: |
          curl -f https://staging.tasktracker.example.com/health || exit 1

  # ──────────────────────────────
  # Stage 7: Deploy to Production
  # ──────────────────────────────
  deploy-production:
    name: 🎯 Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.event_name == 'release'
    environment:
      name: production
      url: https://tasktracker.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # railway up --environment production
      - name: Verify deployment
        run: |
          curl -f https://tasktracker.example.com/health || exit 1
      - name: Notify team
        run: |
          echo "✅ Deployed version ${{ github.event.release.tag_name }} to production"
```

## Demo: Dockerfile

```dockerfile
# Dockerfile — Multi-stage build for Task Tracker API

# ── Stage 1: Build ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# ── Stage 2: Production ──
FROM node:20-alpine AS production
WORKDIR /app

# Security: run as non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S tasktracker -u 1001
USER tasktracker

COPY --from=builder --chown=tasktracker:nodejs /app/dist ./dist
COPY --from=builder --chown=tasktracker:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=tasktracker:nodejs /app/package.json ./

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/health || exit 1

CMD ["node", "dist/server.js"]
```


---

← [Back to Overview](../overall-view.md)
