"""
Celery tasks for background transcription processing.
"""

import os
import logging
from celery import shared_task
from django.conf import settings
from .coda_client import CodaTranscriptionClient
from .google_drive_downloader import download_file_from_google_drive, get_filename_from_url
from .transcriber import AudioTranscriber
from .analyzer import TranscriptAnalyzer

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_transcription_task(self, row_id, audio_url=None):
    """
    Background task to process audio transcription.

    Args:
        row_id: Coda row ID to process
        audio_url: Optional Google Drive URL (if not provided, fetched from row)

    Returns:
        dict with processing results
    """
    temp_file_path = None

    try:
        logger.info(f"Starting transcription task for row: {row_id}")

        # Initialize components
        coda_client = CodaTranscriptionClient()
        transcriber = AudioTranscriber(model_name=settings.WHISPER_MODEL)
        analyzer = TranscriptAnalyzer()

        # Create temp directory
        os.makedirs(settings.TEMP_DOWNLOAD_DIR, exist_ok=True)

        # Get the row from Coda
        logger.info("Fetching row from Coda...")
        all_rows = coda_client.table.rows()
        target_row = None

        for row in all_rows:
            if row.id == row_id:
                target_row = row
                break

        if not target_row:
            error_msg = f"Row {row_id} not found in Coda table"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }

        # Get audio URL if not provided
        if not audio_url:
            audio_url = coda_client.get_audio_url_from_row(target_row)

        if not audio_url:
            error_msg = "No audio URL found"
            logger.error(error_msg)
            coda_client.mark_row_as_failed(target_row, error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }

        logger.info(f"Audio URL: {audio_url}")

        # Download audio file
        logger.info("Downloading audio from Google Drive...")
        filename = get_filename_from_url(audio_url)
        temp_file_path = os.path.join(settings.TEMP_DOWNLOAD_DIR, filename)

        if not download_file_from_google_drive(audio_url, temp_file_path):
            error_msg = "Failed to download audio file"
            logger.error(error_msg)
            coda_client.mark_row_as_failed(target_row, error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }

        logger.info(f"Downloaded to: {temp_file_path}")

        # Load Whisper model and transcribe
        logger.info("Loading Whisper model...")
        if not transcriber.load_model():
            error_msg = "Failed to load Whisper model"
            logger.error(error_msg)
            coda_client.mark_row_as_failed(target_row, error_msg)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {
                'status': 'error',
                'error': error_msg
            }

        logger.info("Transcribing audio...")
        transcription_result = transcriber.transcribe(temp_file_path)

        if not transcription_result:
            error_msg = "Transcription failed"
            logger.error(error_msg)
            coda_client.mark_row_as_failed(target_row, error_msg)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {
                'status': 'error',
                'error': error_msg
            }

        full_transcript = transcription_result['text']
        logger.info(f"Transcription successful ({len(full_transcript)} characters)")

        # Analyze transcript
        logger.info("Analyzing transcript...")
        analysis_result = analyzer.analyze(full_transcript)

        if not analysis_result:
            error_msg = "Analysis failed"
            logger.warning(error_msg)
            summary_text = "Analysis failed, but transcription succeeded."
        else:
            summary_text = analyzer.get_short_summary(analysis_result)

        logger.info("Analysis complete")

        # Update Coda row
        logger.info("Updating Coda row with results...")
        if not coda_client.update_row_with_results(target_row, full_transcript, summary_text):
            error_msg = "Failed to update Coda row"
            logger.error(error_msg)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {
                'status': 'error',
                'error': error_msg
            }

        logger.info("✓ Row updated successfully")

        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up temp file: {temp_file_path}")

        return {
            'status': 'success',
            'row_id': row_id,
            'transcript_length': len(full_transcript),
            'language': transcription_result.get('language', 'unknown')
        }

    except Exception as e:
        logger.error(f"Error in transcription task: {e}", exc_info=True)

        # Clean up temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")

        # Retry the task if it hasn't exceeded max retries
        try:
            raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds
        except Exception:
            # Max retries exceeded
            return {
                'status': 'error',
                'error': str(e),
                'retries_exceeded': True
            }
