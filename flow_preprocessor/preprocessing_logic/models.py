"""
Models to use for the preprocessing package - mainly the status model
"""
from datetime import datetime
from typing import Optional, List
import enum

from pydantic import BaseModel, Field


class StateEnum(enum.Enum):
    """
    List of states of the process
    """
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    DONE = "done"


class PreprocessState(BaseModel):
    """
    The state of a preprocessing job
    """
    process_id: str = Field(alias="process_id",
                            description="The uniqueid of the preprocess status.",
                            title="ID")
    created_at: datetime = Field(alias="created_at",
                                 description="The timestamp of the preprocess status creation.",
                                 title="Created-At",
                                 default_factory=datetime.now)
    repo_name: str = Field(alias="repo_name",
                           description="Name of the GitHub-repository.",
                           title="Repository-Name")
    repo_folder: str = Field(alias="repo_folder",
                             description="Folder in the repository the files are fetched from.",
                             title="Repository-Folder",
                             examples=["xml", "page"])
    abbreviation: bool = Field(default=False,
                               alias="abbreviation",
                               description="Whether to expand abbreviations in text.",
                               title="Abbreviation")
    crop: bool = Field(default=False,
                       alias="crop",
                       description="Whether to crop images to their linemask.",
                       title="Crop")
    stop_on_fail: bool = Field(default=True,
                               alias="stop_on_fail",
                               description="Whether to stop processing on failure.",
                               title="Stop-On-Fail")
    progress: int = Field(alias="progress",
                          description="The progress of the preprocess status.",
                          title="Progress",
                          default=0)
    state: StateEnum = Field(alias="state",
                             description="The state of the preprocess status.",
                             title="State",
                             default=StateEnum.IN_PROGRESS)
    files_successful: Optional[int] = Field(alias="files_successful",
                                            description="The amount of successfully processed files.",
                                            title="Files-Successful",
                                            default=0)
    files_failed_process: Optional[int] = Field(alias="files_failed_process",
                                                description="The amount of files that failed processing.",
                                                title="Files-Failed-Process",
                                                default=0)
    files_failed_download: Optional[int] = Field(alias="files_failed_download",
                                                 description="The amount of files that failed downloading.",
                                                 title="Files-Failed-Download",
                                                 default=0)
    files_total: Optional[int] = Field(alias="files_total",
                                       description="The total amount of files.",
                                       title="Files-Total",
                                       default=0)
    filenames_successful: Optional[List] = Field(alias="filenames_successful",
                                                 description="The names of the successfully processed files.",
                                                 title="Filenames-Successful",
                                                 default=[])
    filenames_failed_process: Optional[List] = Field(alias="filenames_failed_process",
                                                     description="The names of the files that failed processing.",
                                                     title="Filenames-Failed-Process",
                                                     default=[])
    filenames_failed_download: Optional[List] = Field(alias="filenames_failed_download",
                                                      description="The names of the files that failed downloading.",
                                                      title="Filenames-Failed-Download",
                                                      default=[])
    line_images: Optional[List] = Field(alias="line_images",
                                        description="The names of the lines images processed.",
                                        title="Filenames-Line-Images-Processed",
                                        default=[])
    runtime: Optional[int] = Field(alias="runtime",
                                   description="The runtime of the preprocess status.",
                                   title="Runtime",
                                   default=0)
    segment: Optional[bool] = Field(alias="segment",
                                    description="Whether the images have to be segmented before processing.",
                                    title="Segment",
                                    default=False
                                    )
