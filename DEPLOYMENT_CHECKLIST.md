# Deployment Checklist

Complete checklist for deploying the webhook service to Railway.app.

## 📋 Pre-Deployment

### Local Testing

- [ ] Copy `.env.example` to `.env`
- [ ] Add Coda API credentials to `.env`
- [ ] Test locally with `docker-compose up`
- [ ] Verify health endpoint: `curl http://localhost:8000/api/health/`
- [ ] Test webhook with `./test_webhook.sh http://localhost:8000`
- [ ] Confirm Celery worker is processing tasks
- [ ] Test end-to-end with real audio file

### Code Preparation

- [ ] All sensitive data in environment variables (not hardcoded)
- [ ] `.gitignore` includes `.env`, `db.sqlite3`, etc.
- [ ] `requirements.txt` is up to date
- [ ] `Dockerfile` builds successfully
- [ ] `docker-compose.yml` works locally

## 🚀 Railway Deployment

### Step 1: GitHub Setup

- [ ] Create GitHub repository
- [ ] Push code to GitHub:
  ```bash
  cd webhook_service
  git init
  git add .
  git commit -m "Initial commit"
  git branch -M main
  git remote add origin <your-repo-url>
  git push -u origin main
  ```

### Step 2: Railway Project Creation

- [ ] Sign up at [Railway.app](https://railway.app)
- [ ] Create new project
- [ ] Connect GitHub repository
- [ ] Railway auto-detects Dockerfile

### Step 3: Add Redis Service

- [ ] In Railway project, click "+ New"
- [ ] Select "Database" → "Redis"
- [ ] Note the `REDIS_URL` (auto-configured)

### Step 4: Configure Web Service

- [ ] Go to web service settings
- [ ] Add environment variables:
  - [ ] `DJANGO_SECRET_KEY` (generate new)
  - [ ] `DEBUG=False`
  - [ ] `ALLOWED_HOSTS=*.up.railway.app`
  - [ ] `CODA_API_KEY=1381964b-b9c2-45b1-88e8-a229fe3712df`
  - [ ] `CODA_DOC_ID=l_Rj9r5rsm`
  - [ ] `CODA_TABLE_ID=grid-ZL-gOc_-3e`
  - [ ] `COLUMN_AUDIO_URL=Audio File URL`
  - [ ] `COLUMN_STATUS=Status`
  - [ ] `COLUMN_TRANSCRIPT=Transcript`
  - [ ] `COLUMN_SUMMARY=Summary`
  - [ ] `COLUMN_PROCESSED_DATE=Processed Date`
  - [ ] `WHISPER_MODEL=tiny`
  - [ ] `TEMP_DOWNLOAD_DIR=/tmp/audio`
  - [ ] `WEBHOOK_SECRET` (generate secure token)
- [ ] Verify `REDIS_URL` is set (auto-added by Railway)

### Step 5: Deploy Celery Worker

- [ ] Click "+ New" → "Empty Service"
- [ ] Connect same GitHub repo
- [ ] In service settings → Override start command:
  ```
  celery -A transcription_service worker --loglevel=info --concurrency=2
  ```
- [ ] Copy ALL environment variables from web service
- [ ] Ensure `REDIS_URL` matches web service

### Step 6: Verify Deployment

- [ ] Web service deployed successfully
- [ ] Worker service running
- [ ] Redis service healthy
- [ ] No errors in deployment logs
- [ ] Note your app URL: `https://your-app.up.railway.app`

## ✅ Post-Deployment Testing

### Test Endpoints

- [ ] Health check:
  ```bash
  curl https://your-app.up.railway.app/api/health/
  ```
  Expected: `{"status":"healthy",...}`

- [ ] Webhook endpoint:
  ```bash
  curl -X POST https://your-app.up.railway.app/api/webhook/transcribe/ \
    -H "Content-Type: application/json" \
    -H "X-Webhook-Secret: your-secret" \
    -d '{"row_id":"i-test123"}'
  ```
  Expected: `{"status":"queued","task_id":"..."}`

- [ ] Task status:
  ```bash
  curl https://your-app.up.railway.app/api/status/TASK_ID/
  ```

### End-to-End Test

- [ ] Add test row in Coda table
- [ ] Set up "Generate Insights" button
- [ ] Configure webhook automation
- [ ] Click button
- [ ] Verify row status changes to "Processing"
- [ ] Wait for transcription (~30-60 seconds)
- [ ] Confirm transcript and summary appear
- [ ] Verify status changes to "Transcription Done"

## 🔧 Coda Configuration

### Table Setup

- [ ] Columns exist:
  - [ ] Audio File URL
  - [ ] Generate Insights (Button)
  - [ ] Status (Select: Pending, Processing, Done, Failed)
  - [ ] Transcript (Text)
  - [ ] Summary (Text)
  - [ ] Processed Date (Date/Time)

### Button Configuration

- [ ] Button column added
- [ ] Named "Generate Insights"

### Automations

- [ ] **Automation 1**: Trigger webhook on button click
  - [ ] Trigger: When button pushed
  - [ ] Action: Set Status to "Processing"
  - [ ] Action: Push to webhook with row data
  - [ ] Active ✓

- [ ] **Automation 2**: Mark complete
  - [ ] Trigger: When rows updated
  - [ ] Condition: Transcript not empty AND Status = Processing
  - [ ] Action: Set Status to "Transcription Done"
  - [ ] Active ✓

## 📊 Monitoring Setup

### Railway Monitoring

- [ ] Enable Railway metrics
- [ ] Set up alerts for:
  - [ ] Service downtime
  - [ ] High error rate
  - [ ] High memory usage

### External Monitoring (Optional)

- [ ] UptimeRobot health check monitor
- [ ] Pingdom uptime monitoring
- [ ] Email/Slack alerts configured

### Log Monitoring

- [ ] Know how to access Railway logs
- [ ] Understand log levels (INFO, WARNING, ERROR)
- [ ] Can identify common error patterns

## 🔒 Security Checklist

- [ ] Django `SECRET_KEY` is randomly generated
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] Webhook secret token configured
- [ ] Webhook secret documented securely
- [ ] Coda API key not committed to git
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS enabled (automatic with Railway)

## 💰 Cost Management

- [ ] Understand Railway pricing
- [ ] Monitor monthly usage
- [ ] Optimize Whisper model choice (tiny vs base vs small)
- [ ] Adjust Celery concurrency as needed
- [ ] Consider auto-scaling settings

## 📚 Documentation

- [ ] README.md updated with deployment URL
- [ ] CODA_WEBHOOK_SETUP.md reviewed
- [ ] Team members know how to use button
- [ ] Troubleshooting guide accessible
- [ ] Railway login credentials saved securely

## 🎯 Production Readiness

### Performance

- [ ] Whisper model appropriate for use case
- [ ] Celery concurrency optimized
- [ ] Redis connection stable
- [ ] No memory leaks observed
- [ ] Response times acceptable

### Reliability

- [ ] Error handling tested
- [ ] Retry logic works
- [ ] Failed tasks marked properly in Coda
- [ ] Logs are informative
- [ ] Health check responds quickly

### Scalability

- [ ] Can handle multiple concurrent requests
- [ ] Queue doesn't back up under load
- [ ] Memory usage within limits
- [ ] Can add more workers if needed

## 🔄 Maintenance

### Regular Tasks

- [ ] Review logs weekly
- [ ] Monitor error rates
- [ ] Check Railway usage/costs
- [ ] Update dependencies monthly
- [ ] Test backups (if using database)

### Emergency Procedures

- [ ] Know how to restart services in Railway
- [ ] Can quickly disable webhook if needed
- [ ] Have rollback plan for failed deployments
- [ ] Emergency contact list ready

## 📈 Success Metrics

Track these metrics after deployment:

- [ ] Number of transcriptions processed
- [ ] Average processing time
- [ ] Success rate vs failures
- [ ] User satisfaction
- [ ] Cost per transcription

## ✨ Final Checks

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Team trained on usage
- [ ] Monitoring active
- [ ] Backup plan in place
- [ ] Celebrate! 🎉

---

## Quick Reference

**Railway App URL**: `https://your-app.up.railway.app`

**Endpoints**:
- Health: `/api/health/`
- Webhook: `/api/webhook/transcribe/`
- Status: `/api/status/{task_id}/`

**Webhook Payload**:
```json
{
  "row_id": "i-abc123",
  "audio_url": "https://drive.google.com/..." (optional)
}
```

**Environment Variables**: See `.env.example`

---

**Ready for production!** ✅
