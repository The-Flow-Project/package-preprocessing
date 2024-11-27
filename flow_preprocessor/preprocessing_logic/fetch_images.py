# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import os
from typing import List, Optional
from lxml import etree as et
import requests

from flow_preprocessor.exceptions.exceptions import ImageFetchException
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
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            file.write(response.content)
        logger.info(f'{self.__class__.__name__} - File downloaded: {filename}')

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
                f'{self.__class__.__name__} - Failed to download file {image_filename}',
                exc_info=True
            )
            raise ImageFetchException('Failed to download file %s.', e)
        except FileNotFoundError as e:
            logger.error(
                f'{self.__class__.__name__} - XML file not found: {page}',
                exc_info=True
            )
            raise ImageFetchException('XML file not found: %s', e)
        except (et.XMLSyntaxError, et.ParseError, IndexError, TypeError, ValueError) as e:
            logger.error(
                f'{self.__class__.__name__} - Error parsing file {page}',
                exc_info=True
            )
            if image_filename is not None:
                self.failed_processing.append(image_filename)
            raise ImageFetchException('Error parsing file %s: %s', e)
        except Exception as e:
            logger.error(
                f'{self.__class__.__name__} - An unexpected error occurred for file {page}',
                exc_info=True
            )
            if image_filename is not None:
                self.failed_processing.append(image_filename)
            raise ImageFetchException('An unexpected error occurred for file %s: %s', e)

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
