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
from flow_segmenter import SegmenterConfig, SegmenterBaseConfig

__version__ = "0.7.0"

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
