web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 transcription_service.wsgi:application
worker: celery -A transcription_service worker --loglevel=info --concurrency=2
