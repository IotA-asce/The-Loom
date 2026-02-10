# Deployment Guide

This guide covers deploying The Loom in various environments.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [Production Checklist](#production-checklist)
- [Monitoring Setup](#monitoring-setup)

## Docker Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/IotA-asce/The-Loom.git
cd The-Loom

# Create environment file
cat > .env << EOF
JWT_SECRET=$(openssl rand -hex 32)
GEMINI_API_KEY=your-gemini-key
LOOM_ENV=production
EOF

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f api
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | Main FastAPI application |
| redis | 6379 | Rate limiting cache (optional) |
| prometheus | 9090 | Metrics collection (optional) |
| grafana | 3000 | Dashboards (optional) |

### Docker Compose Profiles

```bash
# Basic deployment
docker-compose up -d

# With Redis for distributed rate limiting
docker-compose --profile distributed up -d

# With full monitoring stack
docker-compose --profile monitoring up -d

# All features
docker-compose --profile distributed --profile monitoring up -d
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT signing | `openssl rand -hex 32` |

### LLM Providers (at least one required)

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LOOM_ENV` | `development` | Environment name |
| `LOOM_DATA_DIR` | `/app/data` | Data directory |
| `LOOM_RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `LOOM_CORS_ORIGINS` | `*` | Allowed CORS origins |
| `STABILITY_API_KEY` | - | Stability AI for cloud images |

### Database Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `LOOM_GRAPH_DB` | `/app/.loom/graph.db` | Graph database |
| `LOOM_EVENTS_DB` | `/app/.loom/events.db` | Event store |

## Production Checklist

### Security

- [ ] Change default `JWT_SECRET` to a secure random value
- [ ] Enable rate limiting (`LOOM_RATE_LIMIT_ENABLED=true`)
- [ ] Configure CORS origins (`LOOM_CORS_ORIGINS`)
- [ ] Use HTTPS (terminate TLS at reverse proxy)
- [ ] Run as non-root user (handled by Dockerfile)

### Performance

- [ ] Set appropriate worker count in Dockerfile
- [ ] Enable Redis for distributed rate limiting (multi-instance)
- [ ] Configure database connection pooling
- [ ] Set up CDN for static assets

### Monitoring

- [ ] Enable Prometheus metrics collection
- [ ] Set up Grafana dashboards
- [ ] Configure log aggregation
- [ ] Set up alerting for SLO breaches

### Backup

- [ ] Backup SQLite databases regularly
- [ ] Backup ChromaDB vector store
- [ ] Backup generated images

## Monitoring Setup

### Prometheus

Prometheus scrapes metrics from `/api/ops/metrics/prometheus`.

### Grafana Dashboards

Default dashboards available at `http://localhost:3000`:

- **API Metrics**: Request rates, latencies, error rates
- **System Health**: Component status, resource usage
- **SLO Status**: Availability, latency targets

### Health Checks

```bash
# API health
curl http://localhost:8000/api/ops/health

# Metrics
curl http://localhost:8000/api/ops/metrics

# Prometheus format
curl http://localhost:8000/api/ops/metrics/prometheus
```

## Kubernetes (Coming Soon)

Kubernetes manifests will be provided for:
- Horizontal pod autoscaling
- Rolling updates
- ConfigMap/Secret management
- Ingress configuration

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Verify environment
docker-compose exec api env | grep LOOM
```

### Database issues

```bash
# Check database files
docker-compose exec api ls -la /app/.loom/

# Database permissions
docker-compose exec api chown -R loom:loom /app/.loom
```

### Performance issues

```bash
# Check metrics
curl http://localhost:8000/api/ops/metrics

# Check rate limits
curl http://localhost:8000/api/auth/rate-limit \
  -H "X-Client-ID: test-client"
```

---

For more information, see the main [README](../../README.md).
