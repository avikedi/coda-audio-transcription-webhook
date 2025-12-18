# Render.com Deployment Guide

Complete step-by-step guide for deploying the Coda Audio Transcription webhook service to Render.com.

## 📋 Prerequisites

- [x] Render.com account created
- [x] GitHub repository: https://github.com/avikedi/coda-audio-transcription-webhook
- [x] Coda API credentials available

## 🎯 What You're Deploying

This is a Django webhook service with 3 components:
1. **Web Service** - Django API that receives webhooks from Coda
2. **Worker Service** - Celery background worker that processes audio transcription
3. **Redis** - Message broker for task queue

## 🚀 Deployment Steps

### Step 1: Create Redis Service

**Why first?** You'll need the Redis URL for both web and worker services.

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Redis"**
3. Configure:
   - **Name**: `coda-transcription-redis`
   - **Region**: Oregon (or closest to you)
   - **Plan**: **Free**
   - **Maxmemory Policy**: `noeviction`
4. Click **"Create Redis"**
5. **IMPORTANT**: Copy the **Internal Redis URL** from the Redis page
   - Should look like: `redis://red-xxxxx:6379`
   - You'll need this for Step 2 and Step 3

---

### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Click **"Build and deploy from a Git repository"** → **"Next"**
3. **Connect GitHub** (if not already connected)
4. Select repository: **`avikedi/coda-audio-transcription-webhook`**
5. Click **"Connect"**

#### Configure Web Service:

**Basic Settings:**
- **Name**: `coda-transcription-web`
- **Region**: Oregon (same as Redis)
- **Branch**: `main`
- **Root Directory**: (leave blank)
- **Runtime**: `Docker`

**Build & Deploy:**
- Render auto-detects the Dockerfile ✅
- **Docker Build Context Directory**: (leave blank)

**Instance Type:**
- Select: **Free** (for testing) or **Starter** ($7/month for production)

**Environment Variables:**

Click **"Advanced"** and add these environment variables:

| Key | Value |
|-----|-------|
| `DJANGO_SECRET_KEY` | `jdv3TSddnTiAbz4jB-kxtjDciTH65SC5j5bGOREbO3EWuVZTHUBUurRnk8uz9andM3U` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `*.onrender.com` |
| `REDIS_URL` | *Paste the Internal Redis URL from Step 1* |
| `CODA_API_KEY` | `1381964b-b9c2-45b1-88e8-a229fe3712df` |
| `CODA_DOC_ID` | `l_Rj9r5rsm` |
| `CODA_TABLE_ID` | `grid-ZL-gOc_-3e` |
| `COLUMN_AUDIO_URL` | `Audio File URL` |
| `COLUMN_STATUS` | `Status` |
| `COLUMN_TRANSCRIPT` | `Transcript` |
| `COLUMN_SUMMARY` | `Summary` |
| `COLUMN_PROCESSED_DATE` | `Processed Date` |
| `WHISPER_MODEL` | `tiny` |
| `TEMP_DOWNLOAD_DIR` | `/tmp/audio` |

6. Click **"Create Web Service"**

**Build time**: ~5-10 minutes

---

### Step 3: Create Worker Service (Celery)

1. Click **"New +"** → **"Background Worker"**
2. Select the same repository: **`avikedi/coda-audio-transcription-webhook`**
3. Click **"Connect"**

#### Configure Worker Service:

**Basic Settings:**
- **Name**: `coda-transcription-worker`
- **Region**: Oregon (same as Redis and Web)
- **Branch**: `main`
- **Root Directory**: (leave blank)
- **Runtime**: `Docker`

**Docker Command** (CRITICAL):
```bash
celery -A transcription_service worker --loglevel=info --concurrency=2
```

**Instance Type:**
- Select: **Free** (for testing) or **Starter** ($7/month for production)

**Environment Variables:**

Add the **EXACT SAME** environment variables as the web service (from Step 2).

**Pro tip**: Copy the Redis URL carefully - it must match exactly between all services.

4. Click **"Create Background Worker"**

**Build time**: ~5-10 minutes

---

## ✅ Verification

After all services are deployed, verify:

### 1. Check Service Status

In your Render dashboard, you should see:
- ✅ **coda-transcription-web** - Status: **Live** (green)
- ✅ **coda-transcription-worker** - Status: **Live** (green)
- ✅ **coda-transcription-redis** - Status: **Available**

### 2. Test Health Endpoint

1. Click on your **web service**
2. Copy the service URL (e.g., `https://coda-transcription-web.onrender.com`)
3. Open in browser: `https://your-service-url.onrender.com/api/health/`

**Expected response:**
```json
{
  "status": "healthy",
  "service": "transcription-webhook",
  "version": "1.0.0"
}
```

### 3. Check Logs

**Web Service Logs:**
- Go to web service → **"Logs"** tab
- Should see: `Booting worker with pid: X`

**Worker Service Logs:**
- Go to worker service → **"Logs"** tab
- Should see: `celery@hostname ready`

### 4. Test Webhook Endpoint (Optional)

```bash
curl -X POST https://your-service-url.onrender.com/api/webhook/transcribe/ \
  -H "Content-Type: application/json" \
  -d '{"row_id":"test-123","audio_url":"https://example.com/test.mp3"}'
```

**Expected response:**
```json
{
  "status": "queued",
  "task_id": "some-uuid",
  "row_id": "test-123",
  "message": "Transcription task has been queued"
}
```

---

## 🔧 Configuration Notes

### Free Tier Limitations

**Important**: Render's free tier services spin down after 15 minutes of inactivity.

**What this means:**
- First request after inactivity may take 30-60 seconds (cold start)
- Subsequent requests are fast
- Good for testing, not ideal for production

**Solution for production:**
- Upgrade to **Starter** plan ($7/month per service)
- Services stay always-on
- No cold starts

### Whisper Model Options

The `WHISPER_MODEL` environment variable controls transcription quality vs speed:

| Model | Speed | Accuracy | Memory | Recommendation |
|-------|-------|----------|--------|----------------|
| `tiny` | ⚡⚡⚡ | ⭐⭐ | ~1GB | Free tier ✅ |
| `base` | ⚡⚡ | ⭐⭐⭐ | ~1GB | Free tier ✅ |
| `small` | ⚡ | ⭐⭐⭐⭐ | ~2GB | Starter+ |
| `medium` | 🐌 | ⭐⭐⭐⭐⭐ | ~5GB | Not on Render |
| `large` | 🐌🐌 | ⭐⭐⭐⭐⭐⭐ | ~10GB | Not on Render |

**Current setting**: `tiny` (fast, works on free tier)

### Scaling Celery Workers

To process more transcriptions in parallel, adjust concurrency:

1. Go to worker service → **"Settings"**
2. Edit **Docker Command**:
   ```bash
   celery -A transcription_service worker --loglevel=info --concurrency=4
   ```
3. Higher concurrency = more parallel tasks (but more memory)

---

## 🔗 Next Steps: Coda Integration

After deployment is verified, configure Coda:

### 1. Get Your Webhook URL

Your webhook endpoint will be:
```
https://coda-transcription-web.onrender.com/api/webhook/transcribe/
```

### 2. Set Up Coda Button

See [CODA_WEBHOOK_SETUP.md](CODA_WEBHOOK_SETUP.md) for detailed instructions.

**Quick summary:**
1. Add "Generate Insights" button column to Coda table
2. Create automation that triggers on button click
3. Automation sends POST request to webhook URL with:
   ```json
   {
     "row_id": "thisRow.id",
     "audio_url": "thisRow.[Audio File URL]"
   }
   ```

### 3. Test End-to-End

1. Add audio URL to Coda table
2. Click "Generate Insights" button
3. Wait ~30-60 seconds
4. See transcript and summary appear in table

---

## 🐛 Troubleshooting

### Build Fails

**Error: "Error building image"**

**Solution:**
- Check Dockerfile syntax
- Ensure all files are committed to GitHub
- Try manual redeploy: Service → **"Manual Deploy"** → **"Deploy latest commit"**

### Web Service Not Starting

**Check logs for errors:**
```
ALLOWED_HOSTS validation failed
```
**Solution**: Add your Render URL to `ALLOWED_HOSTS`:
```
ALLOWED_HOSTS=your-service.onrender.com,*.onrender.com
```

### Worker Not Processing Tasks

**Check worker logs**: Should see "celery@hostname ready"

**Common issues:**
1. `REDIS_URL` not set correctly
2. Redis service not running
3. Wrong celery command

**Verify Redis connection:**
```bash
# In worker logs, look for:
Connected to redis://red-xxxxx:6379
```

### Transcription Times Out

**Error in logs**: "Task timeout"

**Solutions:**
1. Use smaller Whisper model (`tiny` instead of `base`)
2. Upgrade to Starter plan (more CPU)
3. Increase timeout in Dockerfile:
   ```
   CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 600 ...
   ```

### Cold Start Issues (Free Tier)

**Problem**: First request after 15 min takes 30-60 seconds

**Solutions:**
1. Accept it (free tier limitation)
2. Set up external monitoring to ping service every 10 minutes
3. Upgrade to Starter plan ($7/month)

---

## 💰 Cost Breakdown

### Free Tier (Testing)
- Web service: $0
- Worker service: $0
- Redis: $0
- **Total**: $0/month
- **Limitation**: Services spin down after 15 min inactivity

### Production (Starter)
- Web service: $7/month
- Worker service: $7/month
- Redis: $0 (free tier sufficient)
- **Total**: $14/month
- **Benefits**: Always-on, no cold starts, better performance

### Upgrading

To upgrade a service:
1. Go to service → **"Settings"**
2. Scroll to **"Instance Type"**
3. Select **"Starter"**
4. Click **"Save Changes"**

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Whisper Documentation](https://github.com/openai/whisper)

---

## 🆘 Support

If you encounter issues:

1. **Check service logs** in Render dashboard
2. **Check GitHub Actions** (if set up for CI/CD)
3. **Review environment variables** - typos are common
4. **Test locally** with Docker Compose first

---

## ✅ Deployment Checklist

Before marking deployment as complete:

- [ ] Redis service is "Available"
- [ ] Web service is "Live" (green)
- [ ] Worker service is "Live" (green)
- [ ] All services have `REDIS_URL` set to same value
- [ ] Health endpoint returns 200 OK
- [ ] Web service logs show Gunicorn started
- [ ] Worker logs show Celery ready
- [ ] Test webhook returns task_id
- [ ] Coda table configured with button
- [ ] End-to-end test completed successfully
- [ ] Monitoring/alerting set up (optional)

---

## 🎉 Success Criteria

**Deployment is complete when:**

1. Health check responds: ✅
   ```
   curl https://your-service.onrender.com/api/health/
   ```

2. Webhook accepts requests: ✅
   ```
   curl -X POST https://your-service.onrender.com/api/webhook/transcribe/ \
     -H "Content-Type: application/json" \
     -d '{"row_id":"test"}'
   ```

3. Worker processes tasks: ✅
   - Check worker logs for task processing

4. Coda integration works: ✅
   - Button click triggers transcription
   - Results appear in table

---

**Deployment completed by**: _________________

**Date**: _________________

**Service URLs**:
- Web: _________________________________
- Worker: _________________________________
- Redis: _________________________________

**Notes**:
