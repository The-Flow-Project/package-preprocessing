"""
Flow Preprocessor - Main Preprocessing Module

This module provides preprocessing functionality for PageXML datasets with:
- Async/await support for FastAPI (using asyncio.to_thread for non-blocking)
- Dependency Injection pattern
- Factory Pattern for converter creation
- Configuration object pattern
- Support for ZIP files and HuggingFace datasets
- Optional GPU-accelerated image segmentation
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, List
import asyncio
import datasets
from pydantic import ValidationError

from pagexml_hf import XmlConverter
from flow_segmenter import SegmenterYOLO, SegmenterConfig

from flow_preprocessor.utils.logging.preprocessing_logger import logger
from flow_preprocessor.preprocessing_logic.config import (
    PreprocessorConfig,
    ProcessorState,
    ExportMode,
)
from flow_preprocessor.preprocessing_logic.converter_factory import ConverterFactory


# ===============================================================================
# BASE PREPROCESSOR
# ===============================================================================

class Preprocessor(ABC):
    """
    Base preprocessor class with improved OOP design and async support.

    Features:
    - Dependency Injection for better testability
    - Configuration object pattern for cleaner initialization
    - Async/await with asyncio.to_thread() for FastAPI compatibility
    - Factory pattern for converter creation
    - Properties for encapsulation
    """

    def __init__(
            self,
            config: PreprocessorConfig,
            converter_factory: Optional[ConverterFactory] = None
    ) -> None:
        """
        Initialize the preprocessor.

        :param config: Configuration object containing all settings.
        :param converter_factory: Optional factory for creating converters (for testing/DI).
        """
        self._config = config
        self._converter_factory = converter_factory or ConverterFactory()
        self._state = ProcessorState.INITIALIZED
        self._dataset: Optional[datasets.Dataset] = None
        self._converter: Optional[XmlConverter] = None
        self._segmentation_models: Optional[Union[List[str], str]] = None

        # Initialize segmenter config
        self._segmenter_config = self._initialize_segmenter_config(
            config.segmenter_config
        )

    # ==================== Properties ====================

    @property
    def state(self) -> ProcessorState:
        """Get current processor state."""
        return self._state

    @property
    def config(self) -> PreprocessorConfig:
        """Get configuration."""
        return self._config

    @property
    def dataset(self) -> Optional[datasets.Dataset]:
        """Get the current dataset."""
        return self._dataset

    @property
    def converter(self) -> XmlConverter:
        """
        Get or create the XmlConverter (lazy initialization).

        :return: XmlConverter instance.
        """
        if self._converter is None:
            self._converter = self.create_xmlconverter()
        return self._converter

    # ==================== Abstract Methods ====================

    @abstractmethod
    def create_xmlconverter(self) -> XmlConverter:
        """
        Create an XmlConverter for the specific data source.

        Subclasses must implement this to define their data source.

        :return: An instance of XmlConverter.
        """

    # ==================== Public Async Methods ====================

    async def preprocess(self) -> str:
        """
        Perform preprocessing steps: segmentation (optional) and dataset conversion/upload.

        This method is async and uses asyncio.to_thread() to run CPU-intensive operations
        in a thread pool, ensuring the async event loop is not blocked. This is essential
        for FastAPI and other async frameworks.

        :return: URL of the uploaded dataset repository.
        :raises Exception: If preprocessing fails.
        """
        try:
            self._set_state(ProcessorState.IN_PROGRESS)

            # Step 1: Segmentation (if enabled) - non-blocking
            if self._config.segment:
                logger.info("Segmentation enabled - running segment_images()...")
                await self.segment_images()
                logger.info("Segmentation completed.")

            # Step 2: Convert and upload - non-blocking
            repo_url = await self._convert_and_upload()

            self._set_state(ProcessorState.COMPLETED)
            logger.info(f"Success! Dataset available at: {repo_url}")
            return repo_url

        except Exception as e:
            self._set_state(ProcessorState.FAILED)
            logger.error(f"Preprocessing failed: {e}")
            raise

    async def segment_images(self) -> None:
        """
        Segment images in the dataset using YOLO.

        Runs the CPU/GPU-intensive segmentation in a thread pool to avoid blocking
        the async event loop (important for FastAPI and other async frameworks).

        :raises ValueError: If segmenter_config is not provided.
        """
        try:
            # Run segmentation in thread pool (non-blocking)
            await asyncio.to_thread(self._segment_images_sync)
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            self._set_state(ProcessorState.FAILED)
            raise

    # ==================== Private Sync Methods ====================

    def _initialize_segmenter_config(
            self,
            config: Optional[Union[SegmenterConfig, dict]]
    ) -> Optional[SegmenterConfig]:
        """
        Initialize segmenter configuration.

        :param config: Segmenter config as object or dict.
        :return: SegmenterConfig instance or None.
        :raises ValidationError: If config dict is invalid.
        """
        if config is None:
            return None

        if isinstance(config, dict):
            try:
                return SegmenterConfig(**config)
            except ValidationError as e:
                logger.error(f"Invalid segmenter_config: {e}")
                self._set_state(ProcessorState.FAILED)
                raise ValidationError("Invalid segmenter_config provided.") from e

        return config

    def _segment_images_sync(self) -> None:
        """
        Synchronous implementation of image segmentation.

        This method performs CPU/GPU-intensive segmentation operations.
        Called via asyncio.to_thread() to avoid blocking the event loop.

        :raises ValueError: If segmenter_config is not provided.
        """
        if self._segmenter_config is None:
            error_msg = "segmenter_config must be provided when segment is True."
            logger.error(f"Preprocessor._segment_images_sync(): {error_msg}")
            self._set_state(ProcessorState.FAILED)
            raise ValueError(error_msg)

        logger.info("Running segmentation...")

        # Store model names
        self._segmentation_models = self._segmenter_config.model_names

        # Create segmenter (GPU-accelerated if available)
        segmenter = SegmenterYOLO(config=self._segmenter_config)

        # Convert to raw XML for segmentation
        segmented_dataset = self.converter.convert(
            export_mode=ExportMode.RAW_XML.value,
            split_train=None,
            allow_empty=self._config.allow_empty_lines,
            batch_size=self._config.batch_size,
        )

        # Segment the dataset
        self._dataset = segmenter.segment_dataset(
            segmented_dataset,
            new_column_name='xml'
        )

        # Reset converter to use new dataset
        self._converter = None

        logger.info("Segmentation completed.")

    async def _convert_and_upload(self) -> str:
        """
        Convert dataset and upload to HuggingFace.

        Runs in thread pool to avoid blocking the event loop.

        :return: URL of the uploaded dataset.
        """
        logger.info(f"Converting and uploading with export_mode={self._config.export_mode}")

        # Run conversion/upload in thread pool (non-blocking)
        repo_url = await asyncio.to_thread(self._convert_and_upload_sync)

        return repo_url

    def _convert_and_upload_sync(self) -> str:
        """
        Synchronous implementation of convert and upload.

        This method performs CPU/I/O-intensive operations.
        Called via asyncio.to_thread() to avoid blocking the event loop.

        :return: URL of the uploaded dataset repository.
        """
        return self.converter.convert_and_upload(
            repo_id=self._config.huggingface_repo_name,
            export_mode=self._config.export_mode,
            token=self._config.huggingface_token,
            private=self._config.huggingface_repo_private,
            split_train=self._config.split_train_ratio,
            split_seed=self._config.split_seed,
            split_shuffle=self._config.split_shuffle,
            mask_crop=self._config.crop,
            min_width=self._config.min_width_line,
            min_height=self._config.min_height_line,
            allow_empty=self._config.allow_empty_lines,
            batch_size=self._config.batch_size,
            append=self._config.append
        )

    def _set_state(self, state: ProcessorState) -> None:
        """
        Set the processor state.

        :param state: New state to set.
        """
        self._state = state
        logger.debug(f"Preprocessor state changed to: {state.value}")


# ===============================================================================
# CONCRETE IMPLEMENTATIONS
# ===============================================================================

class ZipPreprocessor(Preprocessor):
    """
    Preprocessor for ZIP files (local or remote).

    Supports:
    - Local ZIP files
    - Remote ZIP files (HTTP/HTTPS URLs)
    - Automatic source type detection
    """

    def __init__(
            self,
            input_path: str,
            config: PreprocessorConfig,
            converter_factory: Optional[ConverterFactory] = None
    ) -> None:
        """
        Initialize ZIP preprocessor.

        :param input_path: Path or URL to ZIP file.
        :param config: Preprocessor configuration.
        :param converter_factory: Optional converter factory (for DI/testing).
        """
        self._input_path = input_path
        super().__init__(config, converter_factory)

    def create_xmlconverter(self) -> XmlConverter:
        """
        Create XmlConverter for ZIP source using factory.

        :return: Configured XmlConverter instance.
        """
        logger.info(f"Creating XmlConverter for ZIP: {self._input_path}")

        try:
            converter = self._converter_factory.create_zip_converter(
                zip_path=self._input_path,
                parse_xml=self._config.requires_xml_parsing,
                dataset=self._dataset
            )
            logger.info("XmlConverter created successfully.")
            return converter
        except Exception as e:
            logger.error(f"Failed to create XmlConverter: {e}")
            self._set_state(ProcessorState.FAILED)
            raise ValueError(f"Failed to create XmlConverter: {e}") from e

    async def preprocess(self) -> str:
        """
        Preprocess ZIP file.

        This method is async to support non-blocking execution in FastAPI and
        other async frameworks.

        :return: URL of uploaded dataset.
        """
        logger.info(f"Preprocessing ZIP: {self._input_path}")
        repo_url = await super().preprocess()
        logger.info(f"Preprocessing of {self._input_path} completed.")
        return repo_url


class HuggingFacePreprocessor(Preprocessor):
    """
    Preprocessor for HuggingFace datasets.

    Supports processing existing HuggingFace datasets and uploading
    the processed version to a new or existing repository.
    """

    def __init__(
            self,
            input_path: str,
            config: PreprocessorConfig,
            converter_factory: Optional[ConverterFactory] = None
    ) -> None:
        """
        Initialize HuggingFace preprocessor.

        :param input_path: HuggingFace repository ID (e.g., 'username/dataset').
        :param config: Preprocessor configuration.
        :param converter_factory: Optional converter factory (for DI/testing).
        """
        self._input_path = input_path
        super().__init__(config, converter_factory)

    def create_xmlconverter(self) -> XmlConverter:
        """
        Create XmlConverter for HuggingFace source using factory.

        :return: Configured XmlConverter instance.
        """
        logger.info(f"Creating XmlConverter for HuggingFace: {self._input_path}")

        try:
            converter = self._converter_factory.create_huggingface_converter(
                repo_id=self._input_path,
                token=self._config.huggingface_token,
                parse_xml=self._config.requires_xml_parsing,
                dataset=self._dataset
            )
            logger.info("XmlConverter created successfully.")
            return converter
        except Exception as e:
            logger.error(f"Failed to create XmlConverter: {e}")
            self._set_state(ProcessorState.FAILED)
            raise ValueError(f"Failed to create XmlConverter: {e}") from e

    async def preprocess(self) -> str:
        """
        Preprocess HuggingFace dataset.

        This method is async to support non-blocking execution in FastAPI and
        other async frameworks.

        :return: URL of uploaded dataset.
        """
        logger.info(f"Preprocessing HuggingFace dataset: {self._input_path}")
        repo_url = await super().preprocess()
        logger.info(f"Preprocessing of {self._input_path} completed.")
        return repo_url


# ===============================================================================
# BUILDER PATTERN (Optional - for easier usage)
# ===============================================================================

class PreprocessorBuilder:
    """
    Builder for creating Preprocessor instances with fluent API.

    Makes it easier to create preprocessors with complex configurations
    without needing to manually create PreprocessorConfig objects.

    Example:
        preprocessor = (PreprocessorBuilder("username/output-dataset")
            .with_token("hf_token")
            .with_export_mode("line")
            .with_segmentation(segmenter_config)
            .with_split(0.8)
            .build_for_zip("data.zip"))
    """

    def __init__(self, huggingface_repo_name: str):
        """
        Initialize builder.

        :param huggingface_repo_name: Target HuggingFace repository.
        """
        self._config_dict: Dict[str, Any] = {
            'huggingface_repo_name': huggingface_repo_name
        }

    def with_token(self, token: str) -> 'PreprocessorBuilder':
        """
        Set HuggingFace token.

        :param token: HuggingFace access token.
        :return: Builder instance for chaining.
        """
        self._config_dict['huggingface_token'] = token
        return self

    def with_export_mode(self, mode: str) -> 'PreprocessorBuilder':
        """
        Set export mode.

        :param mode: Export mode ('line', 'region', 'text', 'window', 'raw_xml').
        :return: Builder instance for chaining.
        """
        self._config_dict['export_mode'] = mode
        return self

    def with_crop(self, crop: bool = True) -> 'PreprocessorBuilder':
        """
        Enable image cropping.

        :param crop: Whether to crop images.
        :return: Builder instance for chaining.
        """
        self._config_dict['crop'] = crop
        return self

    def with_segmentation(
            self,
            segmenter_config: Union[SegmenterConfig, dict]
    ) -> 'PreprocessorBuilder':
        """
        Enable image segmentation.

        :param segmenter_config: Segmenter configuration object or dict.
        :return: Builder instance for chaining.
        """
        self._config_dict['segment'] = True
        self._config_dict['segmenter_config'] = segmenter_config
        return self

    def with_split(
            self,
            ratio: float,
            seed: int = 42,
            shuffle: bool = True
    ) -> 'PreprocessorBuilder':
        """
        Configure dataset splitting.

        :param ratio: Training data ratio (0.0-1.0).
        :param seed: Random seed for reproducibility.
        :param shuffle: Whether to shuffle before splitting.
        :return: Builder instance for chaining.
        """
        self._config_dict['split_train_ratio'] = ratio
        self._config_dict['split_seed'] = seed
        self._config_dict['split_shuffle'] = shuffle
        return self

    def with_line_filtering(
            self,
            min_width: Optional[int] = None,
            min_height: Optional[int] = None
    ) -> 'PreprocessorBuilder':
        """
        Configure line filtering.

        :param min_width: Minimum line width in pixels.
        :param min_height: Minimum line height in pixels.
        :return: Builder instance for chaining.
        """
        if min_width is not None:
            self._config_dict['min_width_line'] = min_width
        if min_height is not None:
            self._config_dict['min_height_line'] = min_height
        return self

    def with_batch_size(self, batch_size: int) -> 'PreprocessorBuilder':
        """
        Set batch size for processing.

        :param batch_size: Batch size for dataset operations.
        :return: Builder instance for chaining.
        """
        self._config_dict['batch_size'] = batch_size
        return self

    def private(self, is_private: bool = True) -> 'PreprocessorBuilder':
        """
        Set repository privacy.

        :param is_private: Whether the output repository should be private.
        :return: Builder instance for chaining.
        """
        self._config_dict['huggingface_repo_private'] = is_private
        return self

    def append(self, should_append: bool = True) -> 'PreprocessorBuilder':
        """
        Set append mode.

        :param should_append: Whether to append to existing dataset.
        :return: Builder instance for chaining.
        """
        self._config_dict['append'] = should_append
        return self

    def build_for_zip(self, zip_path: str) -> ZipPreprocessor:
        """
        Build a ZipPreprocessor.

        :param zip_path: Path or URL to ZIP file.
        :return: Configured ZipPreprocessor instance.
        """
        config = PreprocessorConfig(**self._config_dict)
        return ZipPreprocessor(zip_path, config)

    def build_for_huggingface(self, repo_id: str) -> HuggingFacePreprocessor:
        """
        Build a HuggingFacePreprocessor.

        :param repo_id: HuggingFace repository ID.
        :return: Configured HuggingFacePreprocessor instance.
        """
        config = PreprocessorConfig(**self._config_dict)
        return HuggingFacePreprocessor(repo_id, config)
