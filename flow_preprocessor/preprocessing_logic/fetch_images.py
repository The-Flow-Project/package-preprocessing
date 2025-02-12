"""
Defining the ImageDownloader class to manage the image fetching.
"""

# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import os
from typing import List, Optional
from lxml import etree as et
import requests

from flow_preprocessor.exceptions.exceptions import ImageFetchException, ImageProcessException
from flow_preprocessor.preprocessing_logic.parse_textlines import Page
from flow_preprocessor.utils.logging.preprocessing_logger import logger


# ===============================================================================
# CLASS
# ===============================================================================
class ImageDownloader:
    """
    Download images from Transkribus and eScriptorium via image URL.
    """

    # ===============================================================================
    # METHODS
    # ===============================================================================
    def __init__(self) -> None:
        """
        Initialise the lists of failed downloads, failed image processings and successful image processings.

        :param self.failed_downloads: List of failed downloads.
        :param self.successful_downloads: List of successful downloads.
        :param self.failed_image_processings: List of failed image processings.
        :param self.logger: Logger instance.
        """
        self.failed_downloads: List[str] = []
        self.failed_processing: List[str] = []
        self.successes: List[str] = []

    def _request_image_via_url(self, url: str, filename: str) -> None:
        """
        Request single image from Transkribus and eScriptorium.

        :param url: the image url
        :param filename: the image filename
        """
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            with open(filename, 'wb') as file:
                file.write(response.content)
            logger.info('%s - File downloaded: %s', self.__class__.__name__, filename)
        except requests.exceptions.Timeout:
            logger.info('%s - Image download timed out', self.__class__.__name__)
        except requests.exceptions.RequestException as e:
            logger.info('%s - Image download failed: %s', self.__class__.__name__, e)

    def fetch_image(self, page: Page, img_output: str) -> None:
        """
        Fetch images from Transkribus and eScriptorium.

        :param page: input page object.
        :param img_output: the output destination for the images.
        """
        image_filename: Optional[str] = None
        try:
            image_filename = page.image_file_name
            image_url = page.metadata.image_url

            if image_filename is not None:
                destination_path = os.path.join(img_output, image_filename)
                self._request_image_via_url(image_url, destination_path)
                self.successes.append(destination_path)

        except requests.exceptions.RequestException as e:
            self.failed_downloads.append(image_filename)
            logger.error(
                '%s - Failed to download file %s',
                self.__class__.__name__,
                image_filename,
                exc_info=True
            )
            raise ImageFetchException(f'Failed to download file {e}.') from e
        except (et.XMLSyntaxError, et.ParseError, IndexError, TypeError, ValueError) as e:
            if image_filename is not None:
                self.failed_processing.append(image_filename)
            logger.error(
                '%s - Error parsing file %s',
                self.__class__.__name__,
                page,
                exc_info=True
            )
            raise ImageProcessException(f'Error parsing file {e}') from e
        except Exception as e:
            if image_filename is not None:
                self.failed_processing.append(image_filename)
            logger.error(
                '%s - An unexpected error occurred for file %s',
                self.__class__.__name__,
                page,
                exc_info=True
            )
            raise RuntimeError(f'An unexpected error occurred for file {image_filename}: {e}') from e

    def get_failed_downloads(self) -> List[str]:
        """
        Retrieve the names of the XML files which failed during download.

        :return: List of failed downloads.
        """
        return self.failed_downloads

    def get_failed_processing(self) -> List[str]:
        """
        Retrieve the names of the XML files which failed during processing (i.e. due to parsing errors).

        :return: List of names of the XML files which could not be processed.
        """
        return self.failed_processing

    def get_successes(self) -> List[str]:
        """
        Retrieve the names of the XML files which were successfully downloaded and processed.
        """
        return self.successes
