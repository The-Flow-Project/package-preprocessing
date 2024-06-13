import json
import os
import unittest
import time
from unittest.mock import patch

from flow_preprocessor.preprocessing_logic.status import Status


class StatusTest(unittest.TestCase):

    def setUp(self):
        current_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.in_path: str = os.path.join(current_dir, "..", "test_data")
        self.out_path: str = os.path.join(current_dir, '..', 'tmp_data')
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        self.status = Status(self.out_path)

    def test_write_status(self):
        test_data = {
            "test_key": "Test data"
        }
        expected_file_content = json.dumps(test_data) + '\n'

        # Write status data
        self.status.write_status(test_data)

        # Read file content to check if data was written
        with open(self.status.file_path, 'r') as status_file:
            actual_file_content = status_file.read()

        self.assertEqual(expected_file_content, actual_file_content)

    def test_get_current_timestamp(self):
        fixed_timestamp = "2022-01-01T00:00:00"
        with patch('time.strftime', return_value=fixed_timestamp):
            current_timestamp = self.status.get_current_timestamp()
            self.assertEqual(current_timestamp, fixed_timestamp)

    def test_calculate_runtime(self):
        start_time = 1620683210.123
        end_time = 1620683220.456
        expected_runtime = end_time - start_time

        with patch('time.time') as mock_time:
            mock_time.return_value = start_time
            start = time.time()

            mock_time.return_value = end_time
            end = time.time()

            result = end - start

        self.assertEqual(result, expected_runtime)

    def test_update_progress_on_success(self):
        current_item_index = 1
        total_item_number = 3
        cwd = os.getcwd()
        file_path = "tests/unit_tests/../test_data/1155140_0001_47389007.xml"
        current_item_name = os.path.join(cwd, file_path)

        fixed_timestamp = "2024-05-10T11:21:00"
        self.status.get_current_timestamp = lambda: fixed_timestamp

        self.status.update_progress_on_success(current_item_index, current_item_name, total_item_number)

        with open(self.status.file_path, 'r') as status_file:
            lines = status_file.readlines()

        status_data = json.loads(lines[0])

        expected_output = {
            "progress": f"{current_item_index}/{total_item_number}",
            "last_item": current_item_name,
            "timestamp": fixed_timestamp
        }

        self.assertEqual(status_data, expected_output)

    def test_update_list_status(self):
        list_name = "List Name"
        list_data = ["Item 1", "Item 2", "Item 3"]

        fixed_timestamp = "2024-05-10T11:21:00"
        self.status.get_current_timestamp = lambda: fixed_timestamp

        self.status.update_list_status(list_name, list_data)

        with open(self.status.file_path, 'r') as file:
            lines = file.readlines()

        status_data = json.loads(lines[0])

        self.assertEqual(status_data["list_name"], list_name)
        self.assertEqual(status_data["list_data"], list_data)
        self.assertEqual(status_data["timestamp"], fixed_timestamp)

    def tearDown(self) -> None:
        """
        Clean up resources after each test case.

        This method removes any temporary files or directories created during
        the execution of the test cases.
        """
        for filename in os.listdir(self.out_path):
            file_path: str = os.path.join(self.out_path, filename)
            os.remove(file_path)

        if os.path.isdir(self.out_path) and not os.listdir(self.out_path):
            os.rmdir(self.out_path)


if __name__ == '__main__':
    unittest.main()
