# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import json
import os
import time
from typing import Dict, Any, List


# ===============================================================================
# CLASS
# ===============================================================================
class Status:
    def __init__(self, output_dir: str) -> None:
        """
        initialise class parameters.

        :param output_dir: the directory the status file is saved to.
        """
        timestamp = self.get_current_timestamp()
        file_name = "preprocessor_status_" + timestamp + ".json"
        self.file_path = os.path.join(output_dir, file_name)

    def write_status(self, data: Dict[str, Any]) -> None:
        """
        Write status to status file in dict.

        :param data: the data to be written to the status file in a dict.
        """
        with open(self.file_path, 'a') as status_file:
            json.dump(data, status_file)
            status_file.write('\n')

    @staticmethod
    def get_current_timestamp(timestamp_format: str = "%Y-%m-%dT%H:%M:%S") -> str:
        """
        Get current timestamp.

        :param timestamp_format: formatted string.
        :return: current timestamp.
        """
        return time.strftime(timestamp_format)

    def calculate_runtime(self, start_time: float) -> float:
        """
        Calculate runtime.

        :param: start time as float.
        :return: runtime as float.
        """
        current_time: float = time.time()
        runtime: float = round(current_time - start_time, 2)
        self._update_status({"runtime": runtime})
        return runtime

    def _update_status(self, data: Dict[str, Any]) -> None:
        """
        Update status in status file.

        :param data: the data to be written to the status file in a dict.
        """
        timestamp: str = self.get_current_timestamp()
        data["timestamp"] = timestamp
        self.write_status(data)

    def update_progress_on_success(self,
                                   current_item_index: int,
                                   current_item_name: str,
                                   total_item_number: int) -> None:
        """
        update progress when job is finished.

        :param current_item_index: the index of the item currently being processed.
        :param current_item_name: the name of the item currently being processed.
        :param total_item_number: the total number of items being processed.
        """
        formatted_data = {
            "progress": f"{current_item_index}/{total_item_number}",
            "last_item": current_item_name
        }
        self._update_status(formatted_data)

    def update_list_status(self, list_name: str, list_data: List[Any]) -> None:
        """
        Update the status of lists of processed files.

        :param list_name: the name of the list to be processed.
        :param list_data: the data to be processed.
        """
        formatted_data: Dict[str, Any] = {
            "list_name": list_name,
            "list_data": list_data
        }
        self._update_status(formatted_data)
