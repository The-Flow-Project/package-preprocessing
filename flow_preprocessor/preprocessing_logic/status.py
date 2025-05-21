"""
Status class
"""

# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
from datetime import datetime
from typing import List, Union
from motor.motor_asyncio import AsyncIOMotorDatabase
from flow_preprocessor.preprocessing_logic.models import PreprocessState, StateEnum
from flow_preprocessor.exceptions.exceptions import ImageFetchException
from flow_preprocessor.utils.logging.preprocessing_logger import logger


# ===============================================================================
# CLASS
# ===============================================================================
class Status:
    """
    Status class to keep overview over the preprocessing status.

    :param state: the preprocessing state in this moment.
    """

    def __init__(self, state: PreprocessState, db: AsyncIOMotorDatabase) -> None:
        """
        initialise class parameters.

        :param state: the state of the preprocess status.
        """
        self.state = state
        self.db: AsyncIOMotorDatabase = db

    def initialize_status(self, files_fetched: List, files_download_failed: List) -> PreprocessState:
        """
        Initialize status.

        :param files_fetched: the list of files fetched.
        :param files_download_failed: the list of files that failed to download.
        :return: the status of the preprocessing.
        """
        self.state.files_total = len(files_fetched)
        self.state.files_failed_download = len(files_download_failed)
        self.state.filenames_failed_download = files_download_failed
        self.state.state = StateEnum.IN_PROGRESS
        self.state.runtime_seconds = 0
        self.state.line_images = []
        return PreprocessState(**self.state.model_dump(by_alias=True))

    def calculate_runtime(self) -> int:
        """
        Calculate runtime_seconds.

        :return: runtime_seconds in seconds as int.
        """
        delta = datetime.now() - self.state.created_at
        return int(delta.total_seconds())

    async def update_progress(
            self,
            current_item_index: int = None,
            current_item_name: str = None,
            success: bool = True,
            exception: Exception = None,
            state_enum: StateEnum = None,
    ) -> PreprocessState:
        """
        update progress when job is finished.

        :param current_item_index: the index of the item currently being processed.
        :param current_item_name: the name of the item currently being processed.
        :param success: whether the item was processed successfully.
        :param exception: the exception that was raised if success is False.
        :param state_enum: the state of the preprocessing.
        """
        if current_item_index is not None and current_item_name is not None:
            if self.state.files_total > 0:
                self.state.progress = int((current_item_index / self.state.files_total) * 100)
            else:
                self.state.progress = 0

            if success:
                self.state.files_successful += 1
                self.state.filenames_successful.append(current_item_name)
            else:
                self.state.files_failed_process += 1
                self.state.filenames_failed_process.append(current_item_name)
                if isinstance(exception, ImageFetchException):
                    self.state.files_failed_download += 1
                    self.state.filenames_failed_download.append(current_item_name)

            if state_enum is not None:
                self.state.state = state_enum

        self.state.runtime_seconds = self.calculate_runtime()

        new_status_dict = self.state.model_dump(
            by_alias=True,
            exclude={'line_images'},
            exclude_defaults=True,
            exclude_unset=True,
        )

        logger.info(
            f"Updating DB status: {new_status_dict['_id']}"
        )
        del new_status_dict['_id']
        result = await self.db.preprocess_status.update_one(
            {"_id": self.state.id},
            {"$set": new_status_dict},
        )
        if result:
            logger.info('Result: %s', result)
            logger.info(
                f"Status updated: {new_status_dict['progress']}%",
            )
        else:
            logger.info("Status not updated in DB")
        return PreprocessState(**self.state.model_dump(by_alias=True))

    def update_image_list(self, new_line_images: Union[str, List]) -> PreprocessState:
        """
        Update the image list.

        :param new_line_images: the new line image list.
        """
        if new_line_images is not None:
            self.state.line_images.append(new_line_images)

        return PreprocessState(**self.state.model_dump(by_alias=True))
