"""
Flow Preprocessor - Preprocessing Logic Module

Main exports:
- ZipPreprocessor: For processing ZIP files (local or remote)
- HuggingFacePreprocessor: For processing HuggingFace datasets
- PreprocessorBuilder: Fluent API for easy preprocessor creation
"""
from .preprocessing_logic.preprocess import (
    ZipPreprocessor,
    HuggingFacePreprocessor,
    PreprocessorBuilder,
)

from .preprocessing_logic.config import (
    PreprocessorBaseConfig,
    PreprocessorConfig,
)

from .utils.logging.preprocessing_logger import setup_logger

from flow_segmenter import SegmenterConfig, SegmenterBaseConfig

LOGGING_LEVEL = "INFO"
setup_logger(LOGGING_LEVEL)

__version__ = "0.7.2"
__license__ = "MIT"

__all__ = [
    "ZipPreprocessor",
    "HuggingFacePreprocessor",
    "PreprocessorBuilder",
    "PreprocessorBaseConfig",
    "PreprocessorConfig",
    "SegmenterConfig",
    "SegmenterBaseConfig",
    "__version__",
]
