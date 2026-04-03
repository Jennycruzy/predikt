# 🚀 PREDIKT: Production Deployment Checklist

Before deploying to production, complete this comprehensive checklist.

---

## 📋 Pre-Deployment Verification (2 hours)

### Backend Code Quality

- [ ] All endpoints tested with cURL/Postman
- [ ] Error handling implemented for all edge cases
- [ ] Input validation on all POST endpoints
- [ ] Database migrations tested
- [ ] LLM API fallbacks working (if API key fails, uses simulation)
- [ ] Rate limiting configured
- [ ] CORS properly configured for frontend domain
- [ ] Database connection pooling configured (pool_size=10)
- [ ] Logging configured (INFO level for production)
- [ ] Security headers added (no CORS wildcards in prod)

**Verification script:**
```bash
cd /Users/user/Downloads/PREDIKT/backend
python -m pytest tests/  # If tests exist
curl http://localhost:8000/docs  # Swagger UI loads
```

---

### Frontend Code Quality

- [ ] All components tested in dev mode
- [ ] No console errors in browser DevTools
- [ ] Responsiveness tested on mobile (375px width)
- [ ] Dark mode toggle working
- [ ] All images optimized (use Next.js Image component)
- [ ] Wallet connection tested end-to-end
- [ ] Token balance real-time updates
- [ ] Error messages user-friendly
- [ ] Loading states visible on all async operations
- [ ] Analytics/telemetry configured

**Verification script:**
```bash
cd /Users/user/Downloads/PREDIKT/frontend
npm run build  # Should complete without errors
npm run lint   # Should pass all checks
```

---

### Smart Contract Security

- [ ] Contract audited or reviewed by security expert
- [ ] All state changes emit events
- [ ] Reentrancy guards implemented
- [ ] Integer overflow/underflow protected
- [ ] Access control (only owner can finalize)
- [ ] No hardcoded addresses (use environment variables)
- [ ] Test coverage >80%

**Verification:**
```bash
cd /Users/user/Downloads/PREDIKT/contracts
npx hardhat test
npx hardhat coverage
```

---

## 🔒 Security Hardening

### Secrets Management

- [ ] All private keys in secure vault (not in .env)
- [ ] API keys not committed to Git
- [ ] `.env` added to `.gitignore`
- [ ] `.env.example` has only placeholder values
- [ ] Database password is strong (>16 characters, mixed case)
- [ ] No sensitive logs printed to console

**Check:**
```bash
git status  # Should NOT show .env file
cat .gitignore | grep ".env"  # Should show .env in ignore list
grep -r "sk-" . --exclude-dir=node_modules  # No API keys in code
```

---

### API Security

- [ ] Authentication/authorization implemented
- [ ] Rate limiting per IP (100 req/min)
- [ ] Request body size limit (1MB)
- [ ] HTTPS enforced (use reverse proxy in production)
- [ ] CORS only allows frontend domain
- [ ] SQL injection prevention (using SQLAlchemy ORM)
- [ ] API keys rotated monthly
- [ ] Audit logging for sensitive operations

**Example CORS config:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://PREDIKT.example.com"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

### Database Security

- [ ] Encrypted password authentication
- [ ] All connections use SSL/TLS
- [ ] Regular backups (daily)
- [ ] Backup encryption configured
- [ ] Database user has limited permissions
- [ ] Foreign key constraints enabled
- [ ] No production data in tests
- [ ] Audit trail table for modifications

**Backup setup:**
```bash
# Schedule daily backups
0 2 * * * pg_dump predikt_db | gzip > /backup/predikt_db_$(date +\%Y\%m\%d).sql.gz
```

---

## 🚀 Deployment Target Options

### Option 1: Docker (Recommended)

#### Create Dockerfile for Backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Create Dockerfile for Frontend

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
CMD ["npm", "run", "start"]
```

#### Create docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/predikt_db
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: predikt_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Deploy:**
```bash
docker-compose up -d
```

---

### Option 2: Cloud Deployment

#### AWS EC2 + RDS

```bash
# 1. Create EC2 instance (Ubuntu 22.04)
# 2. Create RDS PostgreSQL database
# 3. SSH into EC2
ssh ubuntu@<instance-ip>

# 4. Clone repository
git clone https://github.com/yourorg/PREDIKT.git
cd PREDIKT

# 5. Install dependencies
bash setup.sh  # Creates setup script

# 6. Deploy with systemd
sudo cp predikt-backend.service /etc/systemd/system/
sudo systemctl enable predikt-backend
sudo systemctl start predikt-backend
```

---

#### Vercel (Frontend only)

```bash
# 1. Push to GitHub
git push origin main

# 2. Go to https://vercel.com/
# 3. Import from GitHub
# 4. Add environment variables in Vercel dashboard
# 5. Deploy

# Verify
curl https://PREDIKT.vercel.app
```

---

#### Railway (Full stack)

```bash
# 1. Create account at https://railway.app/
# 2. Create new project
# 3. Add services: PostgreSQL, Backend, Frontend
# 4. Configure environment variables
# 5. Deploy from GitHub

# Verify
curl https://PREDIKT-production.up.railway.app/docs
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions for Automated Testing

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: cd backend && pytest tests/

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install & build
        run: |
          cd frontend
          npm install
          npm run build
          npm run lint
```

---

## 📊 Monitoring & Observability

### Application Monitoring

```python
# Add to backend main.py
from prometheus_client import Counter, Histogram, start_http_server
import time

# Metrics
request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_metrics(request, call_next):
    request_count.inc()
    start = time.time()
    response = await call_next(request)
    request_duration.observe(time.time() - start)
    return response

# Start Prometheus exporter
start_http_server(8001)  # Metrics on :8001/metrics
```

**Monitor with Prometheus + Grafana:**
1. Install Prometheus: `brew install prometheus`
2. Configure scrape targets in `prometheus.yml`
3. Install Grafana: `brew install grafana`
4. Create dashboards for request rates, latency, errors

---

### Error Tracking

```python
# Add to backend main.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://key@sentry.io/project",
    traces_sample_rate=0.1,  # 10% of transactions
    environment="production"
)
```

---

### Logging

```python
# Add to backend main.py
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'logs/predikt.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

---

## 🧪 Load Testing

Before going live, test at scale:

```bash
# Install k6
brew install k6

# Create load test
cat > load-test.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 100 },   // Ramp up
    { duration: '5m', target: 100 },   // Stay at 100
    { duration: '5m', target: 0 },     // Ramp down
  ],
};

export default function () {
  const res = http.get('http://localhost:8000/markets');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
EOF

# Run test
k6 run load-test.js
```

---

## 📝 Deployment Checklist

### Day Before Deployment

- [ ] All tests passing (backend + frontend)
- [ ] Production database backed up
- [ ] SSL certificate valid for domain
- [ ] Fire wall rules configured (allow ports 80, 443 only)
- [ ] Team notified of deployment window
- [ ] Rollback plan documented
- [ ] Status page prepared for downtime notice

### Deployment Day

- [ ] Backup database (take snapshot)
- [ ] Deploy backend to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy frontend to staging
- [ ] End-to-end test on staging
- [ ] Deploy to production
- [ ] Monitor error rates for 1 hour
- [ ] Run health checks
- [ ] Update status page
- [ ] Notify team of successful deployment

**Health check script:**
```bash
#!/bin/bash
while true; do
  curl -f https://PREDIKT.example.com/docs || exit 1
  curl -f https://PREDIKT.example.com/markets || exit 1
  echo "✅ Health check passed"
  sleep 30
done
```

---

## 🔄 Rollback Plan

If something breaks:

```bash
# Rollback backend
docker-compose down
git checkout <previous-tag>
docker-compose up -d

# Rollback database (from backup)
psql predikt_db < backup_20240322.sql

# Rollback frontend
# Vercel: Revert to previous deployment in dashboard
# AWS/Railway: Redeploy from previous commit
```

---

## 📞 Post-Deployment

- [ ] Monitor error rates and latency
- [ ] Check database disk usage
- [ ] Review API logs for unusual patterns
- [ ] Get user feedback
- [ ] Document any issues discovered
- [ ] Schedule post-mortem if any incidents
- [ ] Plan next improvements

---

## ✅ Success Criteria

Production deployment is successful when:

✅ **Availability:** 99.9% uptime (11.5 minutes downtime/month max)  
✅ **Performance:** API response time <200ms (p95)  
✅ **Reliability:** Error rate <0.1%  
✅ **Security:** No security vulnerabilities in OWASP Top 10  
✅ **Scalability:** Handles 1000+ concurrent users  
✅ **Data:** All transactions persisted to database  
✅ **Monitoring:** Real-time alerts configured for critical metrics  

---

## 📚 Additional Resources

- [Docker Deployment](https://docs.docker.com/compose/)
- [Vercel Deployment](https://vercel.com/docs)
- [Railway Deployment](https://docs.railway.app/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Sentry Error Tracking](https://docs.sentry.io/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
