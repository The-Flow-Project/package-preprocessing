# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
from datetime import datetime
from typing import List
from flow_preprocessor.preprocessing_logic.models import PreprocessState
from flow_preprocessor.exceptions.exceptions import ImageFetchException


# ===============================================================================
# CLASS
# ===============================================================================
class Status:
    def __init__(self, state: PreprocessState) -> None:
        """
        initialise class parameters.

        :param state: the state of the preprocess status.
        """
        self.state = state

    def initialize_status(self, files_fetched: List, files_download_failed: List) -> PreprocessState:
        """
        Initialize status.

        :param files_fetched: the list of files fetched.
        :param files_download_failed: the list of files that failed to download.
        :return: the status of the preprocess.
        """
        self.state.files_total = len(files_fetched)
        self.state.files_failed_download = len(files_download_failed)
        self.state.filenames_failed_download = ", ".join(files_download_failed)
        self.state.state = "in_progress"
        self.state.runtime = self.calculate_runtime()

        return PreprocessState(**self.state.dict())

    @staticmethod
    def format_timedelta_as_hms(td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def calculate_runtime(self) -> str:
        """
        Calculate runtime.

        :return: runtime as float.
        """
        delta = datetime.now() - self.state.created_at
        return self.format_timedelta_as_hms(delta)

    def update_progress(self,
                        current_item_index: int = None,
                        current_item_name: str = None,
                        success: bool = True,
                        exception: Exception = None,
                        state_str: str = None) -> PreprocessState:
        """
        update progress when job is finished.

        :param current_item_index: the index of the item currently being processed.
        :param current_item_name: the name of the item currently being processed.
        :param success: whether the item was processed successfully.
        :param exception: the exception that was raised if success is False.
        :param state_str: the state of the preprocess.
        """
        if current_item_index is not None and current_item_name is not None:
            self.state.progress = int((current_item_index / self.state.files_total) * 100)

            if success:
                self.state.files_successful += 1
                self.state.filenames_successful += f", {current_item_name}"
            else:
                self.state.files_failed_process += 1
                self.state.filenames_failed_process += f", {current_item_name}"
                if exception is ImageFetchException:
                    self.state.files_failed_download += 1
                    self.state.filenames_failed_download += f", {current_item_name}"

            if state_str is not None:
                self.state.state = state_str

        self.state.runtime = self.calculate_runtime()

        return PreprocessState(**self.state.dict())
