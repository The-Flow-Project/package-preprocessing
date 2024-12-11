import asyncio
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from flow_preprocessor.preprocessing_logic.status import Status
from flow_preprocessor.preprocessing_logic.models import PreprocessState, StateEnum
from flow_preprocessor.exceptions.exceptions import ImageFetchException


class StatusTest(unittest.TestCase):
    def setUp(self):
        # Mock initial state
        self.mock_state = PreprocessState(
            process_id="1234",
            repo_name="TestRepo",
            repo_folder="test_folder",
            files_total=5
        )
        self.status = Status(self.mock_state)

    @patch('flow_preprocessor.preprocessing_logic.status.datetime')
    def test_update_progress_success(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2024, 5, 10, 12, 0, 0)
        self.mock_state.created_at = datetime(2024, 5, 10, 11, 0, 0)

        async def run_test():
            current_item_index = 2
            current_item_name = "file1.xml"

            updated_state = await self.status.update_progress(
                current_item_index=current_item_index,
                current_item_name=current_item_name,
                success=True
            )

            self.assertEqual(updated_state.files_successful, 1)
            self.assertIn(current_item_name, updated_state.filenames_successful)
            self.assertEqual(updated_state.progress, 40)  # 2 out of 5 files processed
            self.assertEqual(updated_state.runtime, 3600)  # 1 hour runtime

        asyncio.run(run_test())

    @patch('flow_preprocessor.preprocessing_logic.status.datetime')
    def test_update_progress_failure(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2024, 5, 10, 12, 0, 0)
        self.mock_state.created_at = datetime(2024, 5, 10, 11, 0, 0)

        async def run_test():
            current_item_index = 3
            current_item_name = "file2.xml"

            updated_state = await self.status.update_progress(
                current_item_index=current_item_index,
                current_item_name=current_item_name,
                success=False,
                exception=ImageFetchException("Mock Exception")
            )

            self.assertEqual(updated_state.files_failed_process, 1)
            self.assertIn(current_item_name, updated_state.filenames_failed_process)
            self.assertEqual(updated_state.files_failed_download, 1)  # ImageFetchException triggers download failure
            self.assertEqual(updated_state.progress, 60)  # 3 out of 5 files processed
            self.assertEqual(updated_state.runtime, 3600)  # 1 hour runtime

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
