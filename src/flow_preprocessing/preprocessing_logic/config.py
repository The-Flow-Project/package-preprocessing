"""
Configuration classes for the preprocessor.

Separates configuration from business logic following Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Optional, Union
from enum import Enum

from flow_segmenter import SegmenterConfig


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


@dataclass
class PreprocessorConfig:
    """
    Configuration for the preprocessor.

    Encapsulates all configuration parameters with validation and clear defaults.
    Uses dataclass for automatic __init__, __repr__, and type hints.
    """
    # Required parameters
    huggingface_target_repo_name: str

    # HuggingFace parameters
    huggingface_token: Optional[str] = None
    huggingface_target_repo_private: bool = False
    append: bool = False

    # Export configuration
    export_mode: str = 'line'

    # Processing options
    crop: bool = False
    allow_empty_lines: bool = False
    batch_size: int = 32

    # Line filtering
    min_width_line: Optional[int] = None
    min_height_line: Optional[int] = None

    # Dataset splitting
    split_train_ratio: Optional[float] = None
    split_seed: int = 42
    split_shuffle: bool = True

    # Segmentation
    segment: bool = False
    segmenter_config: Optional[Union[SegmenterConfig, dict]] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate all configuration parameters.

        :raises ValueError: If any parameter is invalid.
        """
        self._validate_export_mode()
        self._validate_line_dimensions()
        self._validate_split_ratio()
        self._validate_segmentation()

    def _validate_export_mode(self) -> None:
        """Validate export mode."""
        valid_modes = [mode.value for mode in ExportMode]
        if self.export_mode not in valid_modes:
            raise ValueError(
                f"Invalid export_mode: '{self.export_mode}'. "
                f"Valid options are: {', '.join(valid_modes)}"
            )

    def _validate_line_dimensions(self) -> None:
        """Validate line dimension parameters."""
        if self.min_width_line is not None and self.min_width_line <= 0:
            raise ValueError("min_width_line must be a positive integer or None.")
        if self.min_height_line is not None and self.min_height_line <= 0:
            raise ValueError("min_height_line must be a positive integer or None.")

    def _validate_split_ratio(self) -> None:
        """Validate split ratio parameter."""
        if self.split_train_ratio is not None:
            if not (0.0 < self.split_train_ratio <= 1.0):
                raise ValueError("split_train_ratio must be between 0.0 and 1.0.")

    def _validate_segmentation(self) -> None:
        """Validate segmentation configuration."""
        if self.segment and self.segmenter_config is None:
            raise ValueError(
                "segmenter_config must be provided when segment is True."
            )

    @property
    def requires_xml_parsing(self) -> bool:
        """
        Check if the export mode requires XML parsing.

        :return: True if XML parsing is needed, False otherwise.
        """
        export_mode_enum = ExportMode(self.export_mode)
        return export_mode_enum in EXPORT_MODES_REQUIRING_XML_PARSING


@dataclass
class DataSourceConfig:
    """
    Configuration for data sources.

    Encapsulates information about where the data comes from.
    """
    input_path: str
    source_type: Optional[str] = None

    def __post_init__(self):
        """Auto-detect source type if not provided."""
        if self.source_type is None:
            self.source_type = self._detect_source_type()

    def _detect_source_type(self) -> str:
        """
        Detect the source type based on input path.

        :return: Source type string ('zip', 'zip_url', or 'huggingface').
        """
        if self.input_path.startswith('http://') or self.input_path.startswith('https://'):
            return 'zip_url'
        elif self.input_path.endswith('.zip'):
            return 'zip'
        else:
            return 'huggingface'

    @property
    def is_zip(self) -> bool:
        """Check if source is a ZIP file."""
        return self.source_type in ['zip', 'zip_url']

    @property
    def is_remote(self) -> bool:
        """Check if source is remote (URL or HuggingFace)."""
        return self.source_type in ['zip_url', 'huggingface']

