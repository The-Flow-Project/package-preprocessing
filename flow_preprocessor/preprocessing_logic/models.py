from datetime import datetime

from pydantic import BaseModel, Field, UUID4, Optional
import enum


class StateEnum(enum.Enum):
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    DONE = "done"


class PreprocessStateBase(BaseModel):
    progress: Optional[int] = Field(alias="progress",
                                    description="The progress of the preprocess status.",
                                    title="Progress",
                                    default=0,
                                    exclude=True)
    state: Optional[StateEnum] = Field(alias="state",
                                       description="The state of the preprocess status.",
                                       title="State",
                                       default="in_progress",
                                       exclude=True)
    files_successful: Optional[int] = Field(alias="files_successful",
                                            description="The amount of successfully processed files.",
                                            title="Files-Successful",
                                            default=0,
                                            exclude=True)
    files_failed_process: Optional[int] = Field(alias="files_failed_process",
                                                description="The amount of files that failed processing.",
                                                title="Files-Failed-Process",
                                                default=0,
                                                exclude=True)
    files_failed_download: Optional[int] = Field(alias="files_failed_download",
                                                 description="The amount of files that failed downloading.",
                                                 title="Files-Failed-Download",
                                                 default=0,
                                                 exclude=True)
    files_total = Optional[int] = Field(alias="files_total",
                                        description="The total amount of files.",
                                        title="Files-Total",
                                        default=0,
                                        exclude=True)
    filenames_successful: Optional[str] = Field(alias="filenames_successful",
                                                description="The names of the successfully processed files.",
                                                title="Filenames-Successful",
                                                default=None,
                                                exclude=True)
    filenames_failed_process: Optional[str] = Field(alias="filenames_failed_process",
                                                    description="The names of the files that failed processing.",
                                                    title="Filenames-Failed-Process",
                                                    default=None,
                                                    exclude=True)
    filenames_failed_download: Optional[str] = Field(alias="filenames_failed_download",
                                                     description="The names of the files that failed downloading.",
                                                     title="Filenames-Failed-Download",
                                                     default=None,
                                                     exclude=True)
    github_amount_pushed: Optional[int] = Field(alias="github_amount_pushed",
                                                description="The amount of files pushed to GitHub.",
                                                title="GitHub-Amount-Pushed",
                                                default=0,
                                                exclude=True)
    github_pushed: Optional[str] = Field(alias="github_pushed",
                                         description="The names of the files pushed to GitHub.",
                                         title="GitHub-Pushed",
                                         default=None,
                                         exclude=True)
    runtime: Optional[int] = Field(alias="runtime",
                                   description="The runtime of the preprocess status.",
                                   title="Runtime",
                                   default=0,
                                   exclude=True)


class PreprocessState(PreprocessStateBase):
    id: UUID4 = Field(alias="id",
                      description="The UUID of the preprocess status.",
                      title="ID",
                      example="123e4567-e89b-12d3-a456-426614174000")
    github_access_token: str = Field(alias="github_token",
                                     description="GitHub access token.",
                                     title="GitHub-Token",
                                     example="ghp_1234567890")
    log_file: Optional[str] = Field(alias="log_file",
                                    description="Name of the log file.",
                                    title="Log-File",
                                    example="log.txt",
                                    default="log.txt",
                                    )
    created_at: datetime = Field(alias="created_at",
                                 description="The timestamp of the preprocess status creation.",
                                 title="Created-At",
                                 example="2022-01-01T12:00:00")
    repo_name: str = Field(alias="repo_name",
                           description="Name of the GitHub-repository.",
                           title="Repository-Name",
                           example="your_github_name/your_repo_name")
    repo_folder: str = Field(alias="repo_folder",
                             description="Folder in the repository the files are fetched from.",
                             title="Repository-Folder",
                             examples=["xml", "page"])
    abbreviation: Optional[bool] = Field(default=False,
                                         alias="abbreviation",
                                         description="Whether to expand abbreviations in text.",
                                         title="Abbreviation")
    crop: Optional[bool] = Field(default=False,
                                 alias="crop",
                                 description="Whether to crop images to their linemask.",
                                 title="Crop")
    stop_on_fail: Optional[bool] = Field(default=True,
                                         alias="stop_on_fail",
                                         description="Whether to stop processing on failure.",
                                         title="Stop-On-Fail")
    directory: Optional[str] = Field(default="tmp",
                                     alias="directory",
                                     description="Directory to save the files temporarily to.",
                                     title="Directory",
                                     example="tmp")
    in_path: Optional[str] = Field(default="",
                                   alias="in_path",
                                   description="Path to save the fetched files.",
                                   title="In-Path",
                                   example="fetched")
    out_path: Optional[str] = Field(default="preprocessed",
                                    alias="out_path",
                                    description="Path to save the preprocessed files.",
                                    title="Out-Path",
                                    example="preprocessed")
    github_commit_message: Optional[str] = Field(alias="github_commit_message",
                                                 description="The commit message for the GitHub push.",
                                                 title="GitHub-Commit-Message",
                                                 example="Preprocessed files.",
                                                 default="Preprocessed files.")
