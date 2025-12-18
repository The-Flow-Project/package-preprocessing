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

from .preprocessing_logic.config import PreprocessorConfig

__all__ = [
    "ZipPreprocessor",
    "HuggingFacePreprocessor",
    "PreprocessorBuilder",
    "PreprocessorConfig",
]