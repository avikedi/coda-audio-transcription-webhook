#!/usr/bin/env python3
"""
Audio transcription module using OpenAI Whisper.
Refactored from the original transcribe_audio.py script.
"""

import ssl
import whisper
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Bypass SSL certificate verification for model download
ssl._create_default_https_context = ssl._create_unverified_context


class AudioTranscriber:
    """Handles audio transcription using OpenAI Whisper."""

    def __init__(self, model_name=None):
        """
        Initialize the transcriber with a Whisper model.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
                       Defaults to environment variable or "tiny"
        """
        if model_name is None:
            model_name = os.getenv('WHISPER_MODEL', 'tiny')

        self.model_name = model_name
        self.model = None
        logger.info(f"Initializing AudioTranscriber with model: {model_name}")

    def load_model(self):
        """Load the Whisper model."""
        if self.model is not None:
            logger.info("Model already loaded")
            return True

        try:
            logger.info(f"Loading Whisper model '{self.model_name}'...")
            self.model = whisper.load_model(self.model_name)
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def transcribe(self, audio_file_path):
        """
        Transcribe an audio file.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary with transcription results or None if error
            {
                'text': str,           # Full transcript
                'language': str,       # Detected language
                'segments': list,      # Detailed segments with timestamps
            }
        """
        if self.model is None:
            logger.error("Model not loaded. Call load_model() first.")
            return None

        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None

        try:
            logger.info(f"Transcribing {audio_file_path}...")
            result = self.model.transcribe(audio_file_path)

            logger.info("Transcription completed successfully")
            logger.info(f"Detected language: {result.get('language', 'unknown')}")
            logger.info(f"Transcript length: {len(result['text'])} characters")

            return {
                'text': result['text'],
                'language': result.get('language', 'unknown'),
                'segments': result.get('segments', []),
            }

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None

    def format_transcript_markdown(self, transcription_result, audio_filename):
        """
        Format transcription results as Markdown.

        Args:
            transcription_result: Result from transcribe()
            audio_filename: Original audio filename

        Returns:
            Formatted markdown string
        """
        if not transcription_result:
            return "Transcription failed"

        md_output = f"# Transcript: {audio_filename}\n\n"
        md_output += f"**Language:** {transcription_result['language']}\n\n"
        md_output += "## Full Transcription\n\n"
        md_output += transcription_result['text']
        md_output += "\n\n## Detailed Segments\n\n"

        for i, segment in enumerate(transcription_result.get('segments', []), 1):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
            md_output += f"**Segment {i}** ({start:.2f}s - {end:.2f}s): {text}\n\n"

        return md_output

    def get_full_transcript_text(self, transcription_result):
        """
        Extract just the full transcript text.

        Args:
            transcription_result: Result from transcribe()

        Returns:
            Full transcript as string
        """
        if not transcription_result:
            return ""
        return transcription_result.get('text', '')


if __name__ == "__main__":
    # Test the transcriber
    logging.basicConfig(level=logging.INFO)

    test_audio = input("Enter path to audio file for testing: ")

    if os.path.exists(test_audio):
        transcriber = AudioTranscriber(model_name='tiny')

        if transcriber.load_model():
            result = transcriber.transcribe(test_audio)

            if result:
                print("\n--- TRANSCRIPTION RESULT ---")
                print(f"Language: {result['language']}")
                print(f"Text: {result['text'][:500]}...")
                print(f"Total segments: {len(result['segments'])}")
                print("✓ Transcription successful")
            else:
                print("✗ Transcription failed")
        else:
            print("✗ Model loading failed")
    else:
        print(f"✗ File not found: {test_audio}")
