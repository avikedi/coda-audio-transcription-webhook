#!/usr/bin/env python3
"""
Google Drive file downloader utility.
Handles downloading audio files from Google Drive URLs.
"""

import os
import re
import requests
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def extract_file_id(google_drive_url):
    """
    Extract Google Drive file ID from various URL formats.

    Supported formats:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID

    Args:
        google_drive_url: Google Drive URL string

    Returns:
        File ID string or None if not found
    """
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, google_drive_url)
        if match:
            return match.group(1)

    logger.error(f"Could not extract file ID from URL: {google_drive_url}")
    return None


def download_file_from_google_drive(file_url, destination_path):
    """
    Download a file from Google Drive.

    Args:
        file_url: Google Drive URL (any supported format)
        destination_path: Local path where file should be saved

    Returns:
        True if download successful, False otherwise
    """
    try:
        file_id = extract_file_id(file_url)
        if not file_id:
            return False

        logger.info(f"Downloading file ID: {file_id}")

        # Use Google Drive download URL
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        # Create session for cookies
        session = requests.Session()

        # First request to get the file
        response = session.get(download_url, stream=True)

        # Check if we need to confirm download (large files)
        if 'download_warning' in response.cookies:
            params = {'id': file_id, 'confirm': response.cookies['download_warning']}
            response = session.get(download_url, params=params, stream=True)

        # Check for virus scan warning (very large files)
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Try to extract the confirm token from HTML
            token_match = re.search(r'confirm=([^&]+)', response.text)
            if token_match:
                confirm_token = token_match.group(1)
                params = {'id': file_id, 'confirm': confirm_token}
                response = session.get(download_url, params=params, stream=True)

        # Save the file
        if response.status_code == 200:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(destination_path)
            logger.info(f"Downloaded file successfully: {destination_path} ({file_size} bytes)")
            return True
        else:
            logger.error(f"Download failed with status code: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False


def get_filename_from_url(file_url):
    """
    Try to get filename from Google Drive URL.
    Falls back to using file ID if filename not available.

    Args:
        file_url: Google Drive URL

    Returns:
        Suggested filename string
    """
    file_id = extract_file_id(file_url)
    if file_id:
        return f"audio_{file_id}.m4a"
    return "downloaded_audio.m4a"


if __name__ == "__main__":
    # Test the downloader
    logging.basicConfig(level=logging.INFO)

    test_url = input("Enter Google Drive URL to test: ")
    test_destination = "./temp_audio/test_download.m4a"

    success = download_file_from_google_drive(test_url, test_destination)

    if success:
        print(f"✓ Download successful: {test_destination}")
    else:
        print("✗ Download failed")
