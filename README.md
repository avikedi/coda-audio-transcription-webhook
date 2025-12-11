# Audio Transcription Webhook Service

Django-based webhook service for automated audio transcription triggered from Coda. Click a button in your Coda table, and this cloud service handles the transcription automatically!

## 🎯 How It Works

```
1. User clicks "Generate Insights" button in Coda
2. Coda automation sends webhook to your deployed service
3. Service queues transcription task (Celery + Redis)
4. Downloads audio from Google Drive
5. Transcribes with Whisper
6. Analyzes and generates summary
7. Updates Coda row with results
8. Returns success response
```

## 🏗️ Architecture

- **Django**: Web framework and API endpoints
- **Django REST Framework**: RESTful API
- **Celery**: Background task processing
- **Redis**: Task queue and caching
- **Gunicorn**: Production WSGI server
- **Docker**: Containerization
- **Railway.app**: Cloud hosting (recommended)

## 📁 Project Structure

```
webhook_service/
├── transcription_service/          # Django project
│   ├── settings.py                 # Configuration
│   ├── urls.py                     # URL routing
│   ├── celery.py                   # Celery configuration
│   └── api/                        # API app
│       ├── views.py                # Webhook endpoints
│       ├── tasks.py                # Celery background tasks
│       ├── coda_client.py          # Coda API integration
│       ├── google_drive_downloader.py
│       ├── transcriber.py          # Whisper transcription
│       └── analyzer.py             # Text analysis
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Local development
├── railway.json                    # Railway deployment config
├── Procfile                        # Process configuration
├── requirements.txt                # Python dependencies
└── manage.py                       # Django CLI
```

## 🚀 Deployment to Railway.app

### Step 1: Prepare Your Code

1. **Push to GitHub** (if you haven't already):
   ```bash
   cd webhook_service
   git init
   git add .
   git commit -m "Initial commit: Django webhook service"
   git remote add origin your-repo-url
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. **Sign up** at [Railway.app](https://railway.app)
2. **Create New Project** → "Deploy from GitHub repo"
3. **Select your repository**
4. Railway will auto-detect the Dockerfile and deploy!

### Step 3: Add Redis Service

1. In your Railway project, click **"+ New"**
2. Select **"Database" → "Add Redis"**
3. Railway will provision Redis and set `REDIS_URL` automatically

### Step 4: Configure Environment Variables

In Railway project settings, add these environment variables:

```
DJANGO_SECRET_KEY=generate-a-long-random-string-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.up.railway.app
CODA_API_KEY=1381964b-b9c2-45b1-88e8-a229fe3712df
CODA_DOC_ID=l_Rj9r5rsm
CODA_TABLE_ID=grid-ZL-gOc_-3e
COLUMN_AUDIO_URL=Audio File URL
COLUMN_STATUS=Status
COLUMN_TRANSCRIPT=Transcript
COLUMN_SUMMARY=Summary
COLUMN_PROCESSED_DATE=Processed Date
WHISPER_MODEL=tiny
TEMP_DOWNLOAD_DIR=/tmp/audio
WEBHOOK_SECRET=your-optional-security-token
```

### Step 5: Deploy Celery Worker

1. In Railway project, click **"+ New" → "Empty Service"**
2. Connect to same GitHub repo
3. In service settings, override start command:
   ```
   celery -A transcription_service worker --loglevel=info --concurrency=2
   ```
4. Add same environment variables as web service

### Step 6: Get Your Webhook URL

Your webhook URL will be:
```
https://your-app-name.up.railway.app/api/webhook/transcribe/
```

## 🧪 Local Development

### Using Docker Compose (Recommended)

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your Coda credentials
   ```

2. **Start services**:
   ```bash
   docker-compose up
   ```

3. **Access the service**:
   - API: http://localhost:8000
   - Health check: http://localhost:8000/api/health/

### Manual Setup

1. **Install Redis**:
   ```bash
   brew install redis  # macOS
   redis-server
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start Django**:
   ```bash
   python manage.py runserver
   ```

5. **Start Celery** (separate terminal):
   ```bash
   celery -A transcription_service worker --loglevel=info
   ```

## 📡 API Endpoints

### Health Check
```
GET /api/health/
```

Response:
```json
{
  "status": "healthy",
  "service": "transcription-webhook",
  "version": "1.0.0"
}
```

### Transcription Webhook
```
POST /api/webhook/transcribe/
Content-Type: application/json
X-Webhook-Secret: your-secret-token (optional)
```

Request body:
```json
{
  "row_id": "i-OQq0AURiBG",
  "audio_url": "https://drive.google.com/..." (optional)
}
```

Response:
```json
{
  "status": "queued",
  "task_id": "abc-123-def-456",
  "row_id": "i-OQq0AURiBG",
  "message": "Transcription task has been queued"
}
```

### Task Status
```
GET /api/status/{task_id}/
```

Response:
```json
{
  "task_id": "abc-123-def-456",
  "status": "SUCCESS",
  "message": "Task completed successfully",
  "result": {
    "status": "success",
    "row_id": "i-OQq0AURiBG",
    "transcript_length": 8454,
    "language": "en"
  }
}
```

## 🔧 Configuration Options

### Whisper Model Selection

Set `WHISPER_MODEL` environment variable:

| Model | Speed | Accuracy | Memory |
|-------|-------|----------|--------|
| tiny | ⚡⚡⚡ | ⭐⭐ | ~1GB |
| base | ⚡⚡ | ⭐⭐⭐ | ~1GB |
| small | ⚡ | ⭐⭐⭐⭐ | ~2GB |
| medium | 🐌 | ⭐⭐⭐⭐⭐ | ~5GB |
| large | 🐌🐌 | ⭐⭐⭐⭐⭐⭐ | ~10GB |

**Recommended for Railway**: `tiny` or `base`

### Celery Concurrency

Adjust workers in `Procfile`:
```
worker: celery -A transcription_service worker --concurrency=2
```

Higher = more parallel processing, but more memory usage.

## 🔒 Security

### Webhook Secret (Recommended)

1. Generate a secret token:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Set `WEBHOOK_SECRET` in Railway environment variables

3. Include in Coda webhook header:
   ```
   X-Webhook-Secret: your-secret-token
   ```

### Django Secret Key

Generate for production:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📊 Monitoring

### Logs

View Railway logs in real-time:
- Go to your service in Railway dashboard
- Click "Logs" tab

### Health Check

Monitor uptime with the health endpoint:
```bash
curl https://your-app.up.railway.app/api/health/
```

Set up monitoring with services like:
- UptimeRobot
- Pingdom
- Better Uptime

## 🐛 Troubleshooting

### Task Not Processing

**Check Celery worker is running**:
- In Railway, ensure worker service is deployed
- Check worker logs for errors

### Redis Connection Failed

**Check REDIS_URL**:
- Verify Railway Redis service is running
- Check environment variables

### Transcription Fails

**Check logs**:
```bash
# In Railway dashboard → Logs
# Look for errors in worker service
```

**Common issues**:
- Audio file too large (try smaller model)
- Invalid Google Drive URL
- Out of memory (reduce concurrency or use smaller model)

### Webhook Not Received

**Check Coda automation**:
- Verify webhook URL is correct
- Check automation is active
- Test with curl:
  ```bash
  curl -X POST https://your-app.up.railway.app/api/webhook/transcribe/ \
    -H "Content-Type: application/json" \
    -d '{"row_id":"test-123","audio_url":"https://..."}'
  ```

## 💰 Cost Estimation

### Railway.app Pricing

**Free Tier** (Starter Plan):
- $5/month credit
- Suitable for testing and light usage

**Pro Plan** ($20/month):
- More resources
- Better for production use

**Estimated monthly cost for moderate usage**:
- Web service: ~$10-15/month
- Worker service: ~$10-15/month
- Redis: ~$5/month
- **Total**: ~$25-35/month

### Optimization Tips

1. **Use smaller Whisper model** (`tiny` or `base`)
2. **Scale to zero** when not in use
3. **Optimize concurrency** (don't over-provision)
4. **Monitor usage** in Railway dashboard

## 📚 Next Steps

After deployment:

1. ✅ **Test health endpoint**
2. ✅ **Test webhook with curl**
3. ✅ **Set up Coda button and automation** (see CODA_WEBHOOK_SETUP.md)
4. ✅ **Test end-to-end with real audio**
5. ✅ **Set up monitoring**
6. ✅ **Configure webhook secret for security**

## 🆘 Support

- Railway docs: https://docs.railway.app
- Django docs: https://docs.djangoproject.com
- Celery docs: https://docs.celeryproject.org

---

**Ready to deploy?** Follow the Railway deployment steps above!
