"""
Factory for creating XmlConverter instances.

Applies Factory Pattern and Template Method Pattern to reduce code duplication.
"""

from typing import Optional
import datasets
from pagexml_hf import XmlConverter, XmlParser

from flow_preprocessor.utils.logging.preprocessing_logger import logger
from flow_preprocessor.utils.url_validator import validate_url


class ConverterFactory:
    """
    Factory for creating XmlConverter instances.

    Centralizes converter creation logic and reduces code duplication.
    """

    def __init__(self, parser: Optional[XmlParser] = None):
        """
        Initialize the factory.

        :param parser: Optional XmlParser instance. If None, a new one is created.
        """
        self._parser = parser or XmlParser()

    def create_zip_converter(
            self,
            zip_path: str,
            parse_xml: bool,
            dataset: Optional[datasets.Dataset] = None
    ) -> XmlConverter:
        """
        Create a converter for ZIP files.

        :param zip_path: Path or URL to the ZIP file.
        :param parse_xml: Whether to parse XML.
        :param dataset: Optional dataset to use instead of ZIP file.
        :return: Configured XmlConverter instance.
        :raises ValueError: If zip_path is a URL that fails security validation.
        """
        if dataset is not None:
            return self._create_dataset_converter(
                dataset=dataset,
                parse_xml=parse_xml,
                source_path=zip_path
            )

        # Validate URL if it's a remote URL (SSRF prevention)
        if zip_path.startswith('http://') or zip_path.startswith('https://'):
            validate_url(zip_path)
            source_type = 'zip_url'
        else:
            source_type = 'zip'

        logger.info(f"Creating XmlConverter for ZIP: {zip_path} (type: {source_type})")

        return XmlConverter(
            gen_func=self._parser.parse_zip,
            gen_kwargs={'zip_path': zip_path, 'parse_xml': parse_xml},
            source_type=source_type,
            source_path=zip_path
        )

    def create_huggingface_converter(
            self,
            repo_id: str,
            token: Optional[str],
            parse_xml: bool,
            dataset: Optional[datasets.Dataset] = None
    ) -> XmlConverter:
        """
        Create a converter for HuggingFace datasets.

        :param repo_id: HuggingFace repository ID.
        :param token: Optional HuggingFace token.
        :param parse_xml: Whether to parse XML.
        :param dataset: Optional dataset object to use instead of loading from hub.
        :return: Configured XmlConverter instance.
        """
        if dataset is not None:
            gen_kwargs = {
                'dataset': dataset,
                'token': token,
                'parse_xml': parse_xml
            }
            logger.info("Using existing dataset for XML conversion.")
        else:
            gen_kwargs = {
                'dataset': repo_id,
                'token': token,
                'parse_xml': parse_xml
            }
            logger.info(f"Loading dataset from HuggingFace Hub: {repo_id}")

        return XmlConverter(
            gen_func=self._parser.parse_dataset,
            gen_kwargs=gen_kwargs,
            source_type='huggingface',
            source_path=repo_id
        )

    def _create_dataset_converter(
            self,
            dataset: datasets.Dataset,
            parse_xml: bool,
            source_path: str
    ) -> XmlConverter:
        """
        Create a converter from a dataset object.

        :param dataset: Dataset object to convert.
        :param parse_xml: Whether to parse XML.
        :param source_path: Original source path for reference.
        :return: Configured XmlConverter instance.
        """
        logger.info("Using provided dataset for XML conversion.")

        return XmlConverter(
            gen_func=self._parser.parse_dataset,
            gen_kwargs={'dataset': dataset, 'parse_xml': parse_xml},
            source_type='huggingface',
            source_path=source_path
        )
