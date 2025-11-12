# Fly.io Deployment Guide

This guide will help you deploy the AbleToCompete MVP to Fly.io with both backend and frontend apps.

## Prerequisites

1. Install the Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login to Fly.io:
   ```bash
   flyctl auth login
   ```

3. Create a Fly.io account if you don't have one

## Step 1: Deploy Backend

### 1.1 Create PostgreSQL Database

```bash
# Create a PostgreSQL database
flyctl postgres create --name abletocompete-db --region cdg

# Save the connection string that appears - you'll need it!
# It will look like: postgres://username:password@hostname:5432/dbname
```

### 1.2 Create Redis Instance

```bash
# Create a Redis instance using Upstash (Fly.io's recommended Redis provider)
flyctl redis create --name abletocompete-redis --region cdg

# Save the Redis URL - you'll need it!
```

### 1.3 Set Backend Secrets

Navigate to the backend directory and set the required secrets:

```bash
cd backend

# Set database URL (use the connection string from step 1.1, replace postgres:// with postgresql+asyncpg://)
flyctl secrets set DATABASE_URL="postgresql+asyncpg://username:password@hostname:5432/dbname"

# Set Redis URL (from step 1.2)
flyctl secrets set REDIS_URL="redis://your-redis-url"

# Set a secure secret key (generate a random string)
flyctl secrets set SECRET_KEY="$(openssl rand -hex 32)"

# Set OpenAI API key (if you want AI agents to work)
flyctl secrets set OPENAI_API_KEY="your-openai-api-key"

# Set CORS origins (add your frontend URL once deployed)
flyctl secrets set ALLOWED_ORIGINS="https://frontend-cool-glade-1606.fly.dev"
```

### 1.4 Deploy Backend

```bash
# Still in the backend directory
flyctl deploy

# Wait for deployment to complete
# Your backend will be available at: https://backend-dark-bird-9186.fly.dev
```

### 1.5 Verify Backend Deployment

```bash
# Check the health endpoint
curl https://backend-dark-bird-9186.fly.dev/health

# Check the API docs
open https://backend-dark-bird-9186.fly.dev/docs
```

## Step 2: Deploy Frontend

### 2.1 Update Backend URL (if needed)

If your backend app name is different, update the `frontend/fly.toml`:

```toml
[env]
  BACKEND_URL = "https://your-backend-app-name.fly.dev"
```

### 2.2 Deploy Frontend

```bash
cd ../frontend

# Deploy the frontend
flyctl deploy

# Wait for deployment to complete
# Your frontend will be available at: https://frontend-cool-glade-1606.fly.dev
```

### 2.3 Update Backend CORS

Now that you have the frontend URL, update the backend CORS settings:

```bash
cd ../backend

# Update ALLOWED_ORIGINS to include the frontend URL
flyctl secrets set ALLOWED_ORIGINS="https://frontend-cool-glade-1606.fly.dev,https://backend-dark-bird-9186.fly.dev"

# This will trigger a backend redeployment
```

## Step 3: Verify Deployment

1. Visit your frontend: `https://frontend-cool-glade-1606.fly.dev`
2. Try logging in (any email/password works in demo mode)
3. Test creating a board or monitor
4. Check the status page: `https://frontend-cool-glade-1606.fly.dev/status`

## Monitoring and Logs

### View Backend Logs
```bash
cd backend
flyctl logs
```

### View Frontend Logs
```bash
cd frontend
flyctl logs
```

### Check App Status
```bash
flyctl status
```

### SSH into Container (for debugging)
```bash
flyctl ssh console
```

## Scaling

### Scale Backend
```bash
cd backend

# Scale to 2 instances
flyctl scale count 2

# Scale memory
flyctl scale memory 2048
```

### Scale Frontend
```bash
cd frontend

# Frontend typically needs less resources
flyctl scale count 1
flyctl scale memory 512
```

## Cost Optimization

To reduce costs on Fly.io:

1. **Auto-stop machines** (already configured in fly.toml):
   - Machines automatically stop when idle
   - Start automatically on incoming requests

2. **Shared CPU** (already configured):
   - Uses shared CPU resources instead of dedicated

3. **Minimum machines**:
   - Set to 0 for development
   - Increase for production availability

## Environment Variables Reference

### Backend Environment Variables

**Required Secrets** (set via `flyctl secrets set`):
- `DATABASE_URL` - PostgreSQL connection string (postgresql+asyncpg://...)
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT signing secret (32+ character random string)
- `ALLOWED_ORIGINS` - Comma-separated CORS origins

**Optional Secrets**:
- `OPENAI_API_KEY` - For AI agent functionality

**Public Environment Variables** (in fly.toml [env] section):
- `APP_NAME` - Application name
- `DEBUG` - Enable/disable debug mode (False for production)
- `ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `MONITOR_CHECK_INTERVAL` - Health check interval in seconds
- `ALERT_COOLDOWN` - Time between alerts in seconds
- `ENABLE_AI_AGENTS` - Enable/disable AI features
- `LLM_MODEL` - AI model to use (gpt-4)

### Frontend Environment Variables

**Public Environment Variables** (in fly.toml [env] section):
- `BACKEND_URL` - Backend API URL (https://backend-app-name.fly.dev)

## Troubleshooting

### Backend not starting
```bash
# Check logs
cd backend
flyctl logs

# Common issues:
# 1. DATABASE_URL not set correctly
# 2. Port mismatch (should be 8000)
# 3. Missing required secrets
```

### Frontend can't connect to backend
```bash
# Verify BACKEND_URL in frontend fly.toml
# Check CORS settings in backend
# View frontend logs
cd frontend
flyctl logs
```

### Database connection issues
```bash
# Test database connection
cd backend
flyctl ssh console
# Then inside the container:
python -c "from app.utils.database import engine; print('DB connected')"
```

### Frontend shows blank page
```bash
# Check if build completed successfully
cd frontend
flyctl logs

# Verify nginx is serving files
flyctl ssh console
ls -la /usr/share/nginx/html
```

## Updating After Code Changes

### Update Backend
```bash
cd backend
flyctl deploy
```

### Update Frontend
```bash
cd frontend
flyctl deploy
```

### Update Secrets
```bash
# Backend
cd backend
flyctl secrets set SECRET_KEY="new-secret"

# This will automatically restart the app
```

## Custom Domains (Optional)

### Add Custom Domain to Backend
```bash
cd backend
flyctl certs create api.yourdomain.com
```

### Add Custom Domain to Frontend
```bash
cd frontend
flyctl certs create yourdomain.com
flyctl certs create www.yourdomain.com
```

Don't forget to update DNS records as instructed by Fly.io!

## Backup and Recovery

### Database Backups
```bash
# Fly.io PostgreSQL includes automatic backups
# To restore from backup:
flyctl postgres db list --app abletocompete-db
```

## Security Checklist

- [ ] Set a strong SECRET_KEY (32+ characters, random)
- [ ] Use HTTPS only (force_https = true in fly.toml)
- [ ] Restrict CORS origins to your frontend domain
- [ ] Set DEBUG=False in production
- [ ] Keep dependencies updated
- [ ] Monitor logs for unusual activity
- [ ] Use secrets for sensitive data (not environment variables)

## Cost Estimate

Typical monthly costs on Fly.io (as of 2024):

- **Backend** (1GB RAM, shared CPU, auto-stop): ~$2-5/month
- **Frontend** (1GB RAM, shared CPU, auto-stop): ~$2-5/month
- **PostgreSQL** (256MB): ~$2/month
- **Redis** (100MB): ~$0-2/month

**Total**: ~$6-14/month for development/low-traffic use

Free tier includes:
- Up to 3 shared-cpu-1x VMs
- 160GB outbound data transfer

## Next Steps

1. Set up monitoring and alerts
2. Configure custom domains
3. Set up CI/CD with GitHub Actions
4. Enable database backups
5. Configure SSL certificates for custom domains

## Support

For issues with Fly.io deployment:
- Fly.io Documentation: https://fly.io/docs/
- Fly.io Community: https://community.fly.io/
- Project Issues: https://github.com/your-repo/issues
