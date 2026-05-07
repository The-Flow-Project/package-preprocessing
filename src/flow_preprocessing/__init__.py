"""
Flow Preprocessor - Preprocessing Logic Module

Main exports:
- ZipPreprocessor: For processing ZIP files (local or remote)
- HuggingFacePreprocessor: For processing HuggingFace datasets
- PreprocessorBuilder: Fluent API for easy preprocessor creation
"""

from flow_segmenter import SegmenterBaseConfig, SegmenterConfig

from .preprocessing_logic.config import (
    PreprocessorBaseConfig,
    PreprocessorConfig,
)
from .preprocessing_logic.preprocess import (
    HuggingFacePreprocessor,
    PreprocessorBuilder,
    ZipPreprocessor,
)
__version__ = "0.8.0"
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
