"""
API views for webhook endpoints.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .tasks import process_transcription_task
from django.conf import settings

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'transcription-webhook',
        'version': '1.0.0'
    })


@csrf_exempt
@api_view(['POST'])
def transcribe_webhook(request):
    """
    Webhook endpoint to receive transcription requests from Coda.

    Expected payload:
    {
        "row_id": "i-abc123",  # Coda row ID
        "audio_url": "https://drive.google.com/..."  # Optional, can fetch from row
    }
    """
    try:
        data = request.data
        logger.info(f"Received webhook request: {data}")

        # Get row ID from payload
        row_id = data.get('row_id')
        audio_url = data.get('audio_url')  # Optional

        if not row_id:
            return Response({
                'error': 'Missing row_id in request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate webhook secret if configured
        webhook_secret = request.headers.get('X-Webhook-Secret')
        if settings.WEBHOOK_SECRET and webhook_secret != settings.WEBHOOK_SECRET:
            logger.warning(f"Invalid webhook secret from {request.META.get('REMOTE_ADDR')}")
            return Response({
                'error': 'Invalid webhook secret'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Queue the transcription task
        task = process_transcription_task.delay(row_id, audio_url)

        logger.info(f"Queued transcription task {task.id} for row {row_id}")

        return Response({
            'status': 'queued',
            'task_id': task.id,
            'row_id': row_id,
            'message': 'Transcription task has been queued'
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Error in transcribe_webhook: {e}", exc_info=True)
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_http_methods(["GET"])
def task_status(request, task_id):
    """
    Check the status of a transcription task.
    """
    from celery.result import AsyncResult

    try:
        task = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'status': task.state,
        }

        if task.state == 'PENDING':
            response_data['message'] = 'Task is waiting to be processed'
        elif task.state == 'STARTED':
            response_data['message'] = 'Task is being processed'
        elif task.state == 'SUCCESS':
            response_data['message'] = 'Task completed successfully'
            response_data['result'] = task.result
        elif task.state == 'FAILURE':
            response_data['message'] = 'Task failed'
            response_data['error'] = str(task.info)
        else:
            response_data['message'] = f'Task state: {task.state}'

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)
