"""
Preprocessor class
"""

# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
from abc import ABC, abstractmethod
from typing import List, Optional, Union
import datasets
from pydantic import ValidationError
from pagexml_hf import XmlConverter, XmlParser

from flow_segmenter import SegmenterYOLO, SegmenterConfig

from flow_preprocessor.utils.logging.preprocessing_logger import logger


# ===============================================================================
# CLASS
# ===============================================================================

# TODO: check stop_on_fail and abbrev implementation
class Preprocessor(ABC):
    """
    Perform preprocessing steps.
    """

    def __init__(
            self,
            huggingface_repo_name: str,
            huggingface_token: Optional[str] = None,
            crop: bool = False,
            abbrev: bool = False,
            segment: bool = False,
            segmenter_config: Optional[Union[SegmenterConfig, dict]] = None,
            stop_on_fail: bool = True,
            min_width_line: Optional[Union[int, float]] = None,
            min_height_line: Optional[Union[int, float]] = None,
            allow_empty_lines: bool = False,
            batch_size: int = 32,
            huggingface_new_repo_private: bool = False,
            split_train_ratio: Optional[float] = None,
            split_seed: int = 42,
            split_shuffle: bool = True,
            export_mode: str = 'line',
    ) -> None:
        """
        initialize parameters.
        :param huggingface_repo_name: Name of the Hugging Face repository to push to (new or existing to update).
        :param huggingface_token: Hugging Face access token.
        :param crop: Whether to crop the images.
        :param abbrev: Whether to expand abbreviations in the text.
        :param segment: Whether to segment the images.
        :param segmenter_config: Configuration for the segmenter.
        :param stop_on_fail: Whether to stop processing on failure.
        :param min_width_line: Minimum width of the line to be processed.
        :param min_height_line: Minimum height of the line to be processed.
        :param allow_empty_lines: Whether to allow empty lines extracted.
        :param batch_size: Batch size for dataset mapping (default 32).
        :param huggingface_new_repo_private: Whether the Hugging Face \
            repository is private (token needed).
        :param split_train_ratio: Ratio of training data to be split - if None, there is no split.
        :param split_seed: Seed for the random split.
        :param split_shuffle: Whether to shuffle the data before splitting.
        :param export_mode: Export mode ('raw_xml', 'text', 'region', 'line', 'window').
        """

        self.state = 'in_progress'

        # Hugging Face repository parameters
        self.huggingface_repo_name: str = huggingface_repo_name
        self.huggingface_token: Optional[str] = None if huggingface_token is None \
            else huggingface_token
        self.huggingface_repo_private: bool = huggingface_new_repo_private
        self.dataset: Optional[datasets.Dataset] = None

        # Data handling
        self.crop: bool = crop
        self.abbrev: bool = abbrev
        self.stop_on_fail: bool = stop_on_fail
        self.allow_empty_lines: bool = allow_empty_lines
        self.batch_size: int = batch_size
        self.export_mode: str = export_mode

        if self.export_mode in ["line", "region", "text", "window"]:
            self.parse_xml = True
        else:
            self.parse_xml = False

        self.min_width_line: Optional[int] = int(min_width_line) if min_width_line is not None \
            else None
        if self.min_width_line is not None and self.min_width_line < 0:
            logger.error(
                "Preprocessor.__init__(): min_width_line must be a positive integer or None."
            )
            self.state = 'failed'
            raise ValueError("min_width_line must be a positive integer or None.")

        self.min_height_line: Optional[int] = int(min_height_line) if min_height_line is not None \
            else None
        if self.min_height_line is not None and self.min_height_line < 0:
            logger.error(
                "Preprocessor.__init__(): min_height_line must be a positive integer or None."
            )
            self.state = 'failed'
            raise ValueError("min_height_line must be a positive integer or None.")

        # Split parameters
        if split_train_ratio is not None:
            if split_train_ratio > 1.0 or split_train_ratio <= 0.0:
                logger.error(
                    "Preprocessor.__init__(): split_train_ratio must be between 0.0 and 1.0."
                )
                self.state = 'failed'
                raise ValueError("split_train_ratio must be between 0.0 and 1.0.")
        self.split_train_ratio: Optional[float] = split_train_ratio
        self.split_seed: int = split_seed
        self.split_shuffle: bool = split_shuffle

        # Segmenter parameters
        self.segment: bool = segment

        self.stats = None
        self.converter: XmlConverter = self.create_xmlconverter()

        if isinstance(segmenter_config, dict):
            try:
                self.segmenter_config = SegmenterConfig(**segmenter_config)
            except ValidationError as e:
                logger.error("Preprocessor.__init__(): Error creating SegmenterConfig: %s", e)
                self.state = 'failed'
                raise ValidationError("Invalid segmenter_config provided.") from e
        else:
            self.segmenter_config: Optional[SegmenterConfig] = segmenter_config

        self.segmentation_models = None

    @abstractmethod
    def create_xmlconverter(self) -> XmlConverter:
        """
        Create an XmlConverter.

        :return: An instance of XmlConverter.
        """

    async def segment_images(self) -> datasets.Dataset | None:
        """
        Segment images in the dataset using the specified segmenter configuration.

        :return: A new Hugging Face dataset with segmented images.
        """
        if self.segmenter_config is None:
            logger.error("Preprocessor.segment_images(): segmenter_config is None.")
            self.state = 'failed'
            raise ValueError("segmenter_config must be provided when segment is True.")
        self.segmentation_models: Optional[Union[List[str], str]] = \
            self.segmenter_config.model_names
        segmenter = SegmenterYOLO(config=self.segmenter_config)
        segmented_dataset = self.converter.convert(
            export_mode='raw_xml',
            split_train=None,
            allow_empty=self.allow_empty_lines,
            batch_size=self.batch_size,
        )
        self.dataset = segmenter.segment_dataset(segmented_dataset, new_column_name='xml')
        self.converter = self.create_xmlconverter()

    async def preprocess(self) -> None:
        """
        Perform preprocessing steps: Create Dataset with XmlConverter and push it to the HuggingFace hub.
        """
        dataset = self.converter.convert(
            export_mode=self.export_mode,
            split_train=self.split_train_ratio,
            split_seed=self.split_seed,
            split_shuffle=self.split_shuffle,
            mask_crop=self.crop,
            min_width=self.min_width_line,
            min_height=self.min_height_line,
            allow_empty=self.allow_empty_lines,
            batch_size=self.batch_size,
        )

        # Upload to HuggingFace Hub
        repo_url = self.converter.upload_to_hub(
            dataset=dataset,
            repo_id=self.huggingface_repo_name,
            token=self.huggingface_token,
            private=self.huggingface_repo_private,
        )
        logger.info(f"Success! Dataset available at: {repo_url}")


class ZipPreprocessor(Preprocessor):
    """
    Preprocess zip-files from a local directory or URL.
    """

    def __init__(
            self,
            input_path: str,
            huggingface_repo_name: str,
            **kwargs
    ) -> None:
        """
        Initialize parameters for file preprocessing.

        :param input_path: URL to fetch the ZIP-File or local path to the ZIP-File.
        :param huggingface_repo_name: Name of the Hugging Face repository, \
            where the result is pushed to.
        :param kwargs: Additional keyword arguments for the \
            base Preprocessor class arguments with default values.
        """
        self.input_path: str = input_path

        super().__init__(huggingface_repo_name, **kwargs)

    def create_xmlconverter(self) -> XmlConverter:
        """
        Create an XmlConverter.

        :return: An instance of XmlConverter.
        """
        parser = XmlParser()

        logger.info("Creating XmlConverter for input path: %s", self.input_path)
        if parser:
            logger.info("XmlParser created successfully.")
        else:
            logger.error("Failed to create XmlParser.")
            self.state = 'failed'
            raise ValueError("Failed to create XmlParser.")
        if self.dataset is not None:
            logger.info("Using dataset for XML conversion.")
            source_type = 'huggingface'
            gen_func = parser.parse_dataset
            gen_kwargs = {'dataset': self.dataset, 'parse_xml': self.parse_xml}
        else:
            logger.info("Using dataset from ZIP file for XML conversion.")
            if self.input_path.startswith('http://') or self.input_path.startswith('https://'):
                source_type = 'zip_url'
            else:
                source_type = 'zip'
            gen_func = parser.parse_zip
            gen_kwargs = {'zip_path': self.input_path, 'parse_xml': self.parse_xml}
        converter = XmlConverter(
            gen_func=gen_func,
            gen_kwargs=gen_kwargs,
            source_type=source_type,
            source_path=self.input_path
        )
        if converter is not None:
            logger.info("XmlConverter created successfully.")
            return converter
        else:
            logger.error("Failed to create XmlConverter.")
            self.state = 'failed'
            raise ValueError("Failed to create XmlConverter.")

    async def preprocess(self) -> None:
        """
        Perform preprocessing steps on files in the input directory 
        and save to the output directory.
        """
        logger.info("Preprocessing/converting %s", self.input_path)
        await super().preprocess()
        logger.info("Preprocessing/converting %s completed.", self.input_path)


class HuggingFacePreprocessor(Preprocessor):
    """
    Preprocess files from a Hugging Face dataset.
    """

    def __init__(
            self,
            input_path: str,
            huggingface_repo_name: str,
            **kwargs
    ) -> None:
        """
        Initialize parameters for file preprocessing.

        :param input_path: Hugging Face dataset ID to fetch the XML files from.
        :param huggingface_repo_name: Name of the Hugging Face repository, \
            where the result is pushed to.
        :param kwargs: Additional keyword arguments for the base Preprocessor class \
            arguments with default values.
        """
        self.input_path: str = input_path

        super().__init__(huggingface_repo_name, **kwargs)

    def create_xmlconverter(self) -> XmlConverter:
        """
        Create an XmlConverter with LineExporter.

        :return: An instance of XmlConverter configured with LineExporter.
        """
        parser = XmlParser()
        logger.info(f"Creating XmlConverter for input path: {self.input_path}")
        if parser:
            logger.info("XmlParser created successfully.")
        else:
            logger.error("Failed to create XmlParser.")
            self.state = 'failed'
            raise ValueError("Failed to create XmlParser.")
        source_type = 'huggingface'
        gen_func = parser.parse_dataset

        if self.dataset is not None:
            logger.info("Using existing dataset for XML conversion.")
            gen_kwargs = {'dataset': self.dataset, 'token': self.huggingface_token, 'parse_xml': self.parse_xml}
        else:
            logger.info("Using dataset from Huggingface Hub for XML conversion.")
            gen_kwargs = {'dataset': self.input_path, 'token': self.huggingface_token, 'parse_xml': self.parse_xml}

        converter = XmlConverter(
            gen_func=gen_func,
            gen_kwargs=gen_kwargs,
            source_type=source_type,
            source_path=self.input_path
        )
        if converter is not None:
            logger.info("XmlConverter created successfully.")
            return converter
        else:
            logger.error("Failed to create XmlConverter.")
            self.state = 'failed'
            raise ValueError("Failed to create XmlConverter.")

    async def preprocess(self) -> None:
        """
        Perform preprocessing steps on files in the input directory and save to the output directory.
        """
        logger.info(f"Preprocessing/converting {self.input_path}")
        await super().preprocess()
        logger.info(f"Preprocessing/converting {self.input_path} completed.")
