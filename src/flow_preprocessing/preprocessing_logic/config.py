"""
Configuration classes for the preprocessor.

Separates configuration from business logic following Single Responsibility Principle.
"""

from typing import Union, Literal, Annotated
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, SecretStr, field_validator, model_validator

from flow_segmenter import SegmenterConfig, SegmenterBaseConfig


class ExportMode(Enum):
    """
    Available export modes for the preprocessor.
    """
    RAW_XML = "raw_xml"
    TEXT = "text"
    REGION = "region"
    LINE = "line"
    WINDOW = "window"


class ProcessorState(Enum):
    """
    Enum for processor states.
    """
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Export modes that require XML parsing
EXPORT_MODES_REQUIRING_XML_PARSING = {
    ExportMode.LINE,
    ExportMode.REGION,
    ExportMode.TEXT,
    ExportMode.WINDOW
}


class PreprocessorBaseConfig(BaseModel):
    """
    Configuration for the preprocessor.

    Encapsulates all configuration parameters with validation and clear defaults.
    Uses Pydantic for validation and schema metadata.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Required parameters
    huggingface_target_repo_name: Annotated[
        str,
        Field(
            default=None,
            alias="huggingface_target_repo_name",
            description="HuggingFace target repository name.",
            title="HuggingFace-Target-Repo-Name",
            examples=["my-org/my-repo"],
        ),
    ]

    # HuggingFace parameters
    huggingface_target_repo_private: Annotated[
        bool | None,
        Field(
            default=False,
            alias="huggingface_target_repo_private",
            description="Whether the target repository is private.",
            title="HuggingFace-Target-Repo-Private",
            examples=["false"],
        ),
    ]
    append: Annotated[
        bool | None,
        Field(
            default=False,
            alias="append",
            description="Append to an existing dataset if it exists, else overwrite it.",
            title="Append",
            examples=["false"],
        ),
    ]

    # Export configuration
    export_mode: Annotated[
        str | None,
        Field(
            default="line",
            alias="export_mode",
            description="Export mode for preprocessing output.",
            title="Export-Mode",
            examples=["line"],
        ),
    ]

    # Processing options
    crop: Annotated[
        bool | None,
        Field(
            default=False,
            alias="crop",
            description="Whether to crop lines during preprocessing.",
            title="Crop",
            examples=["false"],
        ),
    ]
    allow_empty_lines: Annotated[
        bool | None,
        Field(
            default=False,
            alias="allow_empty_lines",
            description="Allow empty lines in output.",
            title="Allow-Empty-Lines",
            examples=["false"],
        ),
    ]
    batch_size: Annotated[
        int | None,
        Field(
            default=32,
            alias="batch_size",
            description="Batch size for processing.",
            title="Batch-Size",
            examples=["32"],
        ),
    ]

    # Line filtering
    min_width_line: Annotated[
        int | None,
        Field(
            default=None,
            alias="min_width_line",
            description="Minimum width of a line; None disables filtering.",
            title="Min-Width-Line",
            examples=["40"],
        ),
    ]
    min_height_line: Annotated[
        int | None,
        Field(
            default=None,
            alias="min_height_line",
            description="Minimum height of a line; None disables filtering.",
            title="Min-Height-Line",
            examples=["10"],
        ),
    ]

    # Dataset splitting
    split_train_ratio: Annotated[
        float | None,
        Field(
            default=None,
            alias="split_train_ratio",
            description="Train split ratio; None disables splitting.",
            title="Split-Train-Ratio",
            examples=["0.8"],
        ),
    ]
    split_seed: Annotated[
        int,
        Field(
            default=42,
            alias="split_seed",
            description="Random seed for dataset splitting.",
            title="Split-Seed",
            examples=["42"],
        ),
    ]
    split_shuffle: Annotated[
        bool | None,
        Field(
            default=True,
            alias="split_shuffle",
            description="Shuffle before splitting the dataset.",
            title="Split-Shuffle",
            examples=["true"],
        ),
    ]

    # Segmentation
    segment: Annotated[
        Literal["yolo", "kraken"] | None,
        Field(
            default=None,
            alias="segment",
            description="Segmentation backend to use.",
            title="Segment",
            examples=["yolo"],
        ),
    ]
    segmenter_config: Annotated[
        Union[SegmenterConfig, SegmenterBaseConfig, dict] | None,
        Field(
            default=None,
            alias="segmenter_config",
            description="Configuration for the segmentation backend.",
            title="Segmenter-Config",
            examples=["{'model_names': 'Riksarkivet/yolov9-lines-within-regions-1',"
                      "'batch_sizes': 16,"
                      "'order_lines': false,"
                      "'baselines': true,"
                      "'kraken_linemasks': true,"
                      "'creator': 'yourname',"
                      "'load_existing_segmentation': true"
                      "}"],
        ),
    ]

    @field_validator("export_mode")
    @classmethod
    def _validate_export_mode(cls, value: str) -> str:
        """Validate export mode."""
        valid_modes = [mode.value for mode in ExportMode]
        if value not in valid_modes:
            raise ValueError(
                f"Invalid export_mode: '{value}'. "
                f"Valid options are: {', '.join(valid_modes)}"
            )
        return value

    @field_validator("min_width_line", "min_height_line")
    @classmethod
    def _validate_line_dimensions(cls, value: int | None, info) -> int | None:
        """Validate line dimension parameters."""
        if value is not None and value <= 0:
            raise ValueError(f"{info.field_name} must be a positive integer or None.")
        return value

    @field_validator("split_train_ratio")
    @classmethod
    def _validate_split_ratio(cls, value: float | None) -> float | None:
        """Validate split ratio parameter."""
        if value is not None:
            if not (0.0 < value <= 1.0):
                raise ValueError("split_train_ratio must be between 0.0 and 1.0.")
        return value

    @model_validator(mode="after")
    def _validate_segmentation(self) -> "PreprocessorBaseConfig":
        """Validate segmentation configuration."""
        if self.segment and self.segmenter_config is None:
            raise ValueError(
                "segmenter_config must be provided when segment is True."
            )
        return self

    @property
    def requires_xml_parsing(self) -> bool:
        """
        Check if the export mode requires XML parsing.

        :return: True if XML parsing is needed, False otherwise.
        """
        export_mode_enum = ExportMode(self.export_mode)
        return export_mode_enum in EXPORT_MODES_REQUIRING_XML_PARSING


class PreprocessorConfig(PreprocessorBaseConfig):
    """
    Extended configuration for the preprocessor.
    """
    huggingface_token: Annotated[
        SecretStr | None,
        Field(
            default=None,
            alias="huggingface_token",
            description="Optional HuggingFace access token.",
            title="HuggingFace-Token",
            examples=["hf_xxx"],
        ),
    ]
