# Django Webhook Service - Quick Start

Get the webhook service running in 5 minutes!

## 🚀 Option 1: Deploy to Railway (Recommended for Production)

### 1. Fork/Clone Repository
```bash
# If not already done
git clone your-repo-url
cd webhook_service
```

### 2. Deploy to Railway
1. Go to [Railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Dockerfile and deploys!

### 3. Add Redis
1. In your Railway project, click "+ New"
2. Select "Database" → "Add Redis"
3. Done! `REDIS_URL` is auto-configured

### 4. Add Environment Variables
In Railway project settings, add:
```
DJANGO_SECRET_KEY=generate-random-string-here
DEBUG=False
ALLOWED_HOSTS=*.up.railway.app
CODA_API_KEY=1381964b-b9c2-45b1-88e8-a229fe3712df
CODA_DOC_ID=l_Rj9r5rsm
CODA_TABLE_ID=grid-ZL-gOc_-3e
WHISPER_MODEL=tiny
```

### 5. Add Celery Worker
1. Click "+ New" → "Empty Service"
2. Connect same repo
3. Override start command:
   ```
   celery -A transcription_service worker --loglevel=info --concurrency=2
   ```
4. Add same environment variables

### 6. Test It!
```bash
# Health check
curl https://your-app.up.railway.app/api/health/

# Test webhook
curl -X POST https://your-app.up.railway.app/api/webhook/transcribe/ \
  -H "Content-Type: application/json" \
  -d '{"row_id":"test-123"}'
```

**Total time**: ~10 minutes ⚡

---

## 🧪 Option 2: Local Development with Docker

### 1. Copy Environment File
```bash
cp .env.example .env
# Edit .env with your Coda credentials
```

### 2. Start Services
```bash
docker-compose up
```

That's it! Services running at:
- Web: http://localhost:8000
- Health: http://localhost:8000/api/health/

### 3. Test Webhook
```bash
./test_webhook.sh http://localhost:8000
```

**Total time**: ~5 minutes ⚡

---

## 🎯 Option 3: Local Development (Manual)

### 1. Install Redis
```bash
# macOS
brew install redis
redis-server

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment
```bash
cp .env.example .env
# Edit .env with credentials
```

### 4. Run Migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Start Services

**Terminal 1** - Django:
```bash
python manage.py runserver
```

**Terminal 2** - Celery:
```bash
celery -A transcription_service worker --loglevel=info
```

**Total time**: ~10 minutes ⚡

---

## 🔘 Set Up Coda Button

After your service is running:

### 1. Add Button Column
In your Coda table, add a **Button** column named "Generate Insights"

### 2. Create Webhook Automation
1. Go to Automations (⚙️ → Automations)
2. Create new automation:
   - **Trigger**: When button pushed ("Generate Insights")
   - **Action**: Push to webhook
     - URL: `https://your-app.up.railway.app/api/webhook/transcribe/`
     - Method: POST
     - Body: `{"row_id":"thisRow.id"}`

### 3. Add Status Automation
1. Create another automation:
   - **Trigger**: When rows updated
   - **Condition**: Transcript not empty AND Status = "Processing"
   - **Action**: Set Status to "Transcription Done"

### 4. Test It!
1. Add audio URL to a row
2. Click "Generate Insights" button
3. Watch Status change to "Processing"
4. Wait ~30-60 seconds
5. See transcript and summary appear!

**Total time**: ~5 minutes ⚡

---

## 📊 Architecture Overview

```
Coda Button Click
    ↓
Coda Automation (webhook)
    ↓
Django Web Service (Railway)
    ↓
Celery Task Queue (Redis)
    ↓
Celery Worker
    ├─ Download from Google Drive
    ├─ Transcribe with Whisper
    ├─ Analyze transcript
    └─ Update Coda row
        ↓
Coda Automation (mark complete)
```

---

## 🆘 Troubleshooting

### "Connection refused" error
- **Local**: Is Redis running? `redis-cli ping`
- **Railway**: Check Redis service is deployed

### "Task not processing"
- **Local**: Is Celery worker running?
- **Railway**: Check worker service logs

### "Webhook returns 404"
- Check URL: Should be `/api/webhook/transcribe/` (with trailing slash)
- Verify service is deployed

### "No module named 'api'"
```bash
# Make sure you're in the right directory
cd webhook_service
# And __init__.py files exist
ls transcription_service/api/__init__.py
```

---

## 📚 Next Steps

1. ✅ Service running locally or on Railway
2. ✅ Coda button configured
3. ✅ Test with sample audio
4. 📖 Read [CODA_WEBHOOK_SETUP.md](CODA_WEBHOOK_SETUP.md) for advanced features
5. 📖 Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) before production

---

## 💡 Pro Tips

- Use **`WHISPER_MODEL=tiny`** for faster processing (good for most cases)
- Use **`WHISPER_MODEL=base`** for better accuracy
- Monitor Railway logs to debug issues
- Set webhook secret for security in production

---

**Questions?** Check the [README.md](README.md) for full documentation!
