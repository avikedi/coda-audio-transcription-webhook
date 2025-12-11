#!/usr/bin/env python3
"""
Coda API client for managing transcription workflow.
Handles reading pending rows and updating them with transcription results.
"""

import os
import logging
from datetime import datetime
from codaio import Coda, Document, Cell
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class CodaTranscriptionClient:
    """Client for managing transcription workflow in Coda."""

    def __init__(self):
        """Initialize Coda client with API credentials."""
        self.api_key = os.getenv('CODA_API_KEY')
        self.doc_id = os.getenv('CODA_DOC_ID')
        self.table_id = os.getenv('CODA_TABLE_ID')

        # Column names
        self.col_audio_url = os.getenv('COLUMN_AUDIO_URL', 'Audio File URL')
        self.col_status = os.getenv('COLUMN_STATUS', 'Status')
        self.col_transcript = os.getenv('COLUMN_TRANSCRIPT', 'Transcript')
        self.col_summary = os.getenv('COLUMN_SUMMARY', 'Summary')
        self.col_processed_date = os.getenv('COLUMN_PROCESSED_DATE', 'Processed Date')

        if not all([self.api_key, self.doc_id, self.table_id]):
            raise ValueError("Missing required environment variables. Check CODA_API_KEY, CODA_DOC_ID, CODA_TABLE_ID")

        # Initialize Coda client
        self.coda = Coda(self.api_key)
        self.doc = Document(self.doc_id, coda=self.coda)
        self.table = self.doc.get_table(self.table_id)

        logger.info("Coda client initialized successfully")

    def get_pending_rows(self):
        """
        Fetch all rows with status "Pending".

        Returns:
            List of row objects that need processing
        """
        try:
            all_rows = self.table.rows()
            pending_rows = []

            for row in all_rows:
                # Get the status value from the row
                status_value = self._get_cell_value(row, self.col_status)

                if status_value and status_value.lower() == "pending":
                    pending_rows.append(row)

            logger.info(f"Found {len(pending_rows)} pending row(s)")
            return pending_rows

        except Exception as e:
            logger.error(f"Error fetching pending rows: {e}")
            return []

    def get_audio_url_from_row(self, row):
        """
        Extract audio URL from a row.

        Args:
            row: Coda row object

        Returns:
            Audio URL string or None
        """
        return self._get_cell_value(row, self.col_audio_url)

    def update_row_with_results(self, row, transcript, summary):
        """
        Update a row with transcription and summary results.

        Args:
            row: Coda row object to update
            transcript: Full transcript text
            summary: Summary text

        Returns:
            True if successful, False otherwise
        """
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cells = [
                Cell(column=self.col_transcript, value_storage=transcript),
                Cell(column=self.col_summary, value_storage=summary),
                Cell(column=self.col_processed_date, value_storage=current_date),
            ]

            # Update the row
            self.table.update_row(row, cells=cells)

            logger.info(f"Updated row {row.id} with transcription results")
            return True

        except Exception as e:
            logger.error(f"Error updating row {row.id}: {e}")
            return False

    def mark_row_as_failed(self, row, error_message):
        """
        Mark a row as failed with error message.

        Args:
            row: Coda row object
            error_message: Error description

        Returns:
            True if successful, False otherwise
        """
        try:
            cells = [
                Cell(column=self.col_status, value_storage="Failed"),
                Cell(column=self.col_summary, value_storage=f"ERROR: {error_message}"),
                Cell(column=self.col_processed_date, value_storage=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ]

            self.table.update_row(row, cells=cells)
            logger.warning(f"Marked row {row.id} as failed: {error_message}")
            return True

        except Exception as e:
            logger.error(f"Error marking row as failed: {e}")
            return False

    def _get_cell_value(self, row, column_name):
        """
        Get cell value from a row by column name.

        Args:
            row: Coda row object
            column_name: Name of the column

        Returns:
            Cell value or None
        """
        try:
            # Get column ID by name
            columns = self.table.columns()
            column_id = None

            for col in columns:
                if col.name == column_name:
                    column_id = col.id
                    break

            if not column_id:
                logger.error(f"Column '{column_name}' not found")
                return None

            # Access row values tuple (column_id, value)
            if hasattr(row, 'values') and row.values:
                for col_id, value in row.values:
                    if col_id == column_id:
                        return value

            return None
        except Exception as e:
            logger.error(f"Error getting cell value for column '{column_name}': {e}")
            return None


if __name__ == "__main__":
    # Test the Coda client
    logging.basicConfig(level=logging.INFO)

    try:
        client = CodaTranscriptionClient()
        print("✓ Coda client initialized")

        pending = client.get_pending_rows()
        print(f"✓ Found {len(pending)} pending row(s)")

        if pending:
            for row in pending:
                url = client.get_audio_url_from_row(row)
                print(f"  - Row ID: {row.id}, Audio URL: {url}")

    except Exception as e:
        print(f"✗ Error: {e}")
