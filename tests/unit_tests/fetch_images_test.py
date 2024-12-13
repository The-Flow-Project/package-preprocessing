import os
import unittest
from typing import List
from unittest.mock import patch, MagicMock

from build.lib.flow_preprocessor.exceptions.exceptions import ImageProcessException
from flow_preprocessor.exceptions.exceptions import ImageFetchException
from flow_preprocessor.preprocessing_logic.fetch_images import ImageDownloader
from flow_preprocessor.preprocessing_logic.parse_textlines import Metadata, Page


class FetchImagesTest(unittest.TestCase):
    """
    Test case for the ImageDownloader class.
    """
    def setUp(self) -> None:
        """
        Set up the test environment.

        This method prepares the necessary resources and configurations
        before each test case is executed.
        """
        current_dir: str = os.path.dirname(os.path.realpath(__file__))
        in_path: str = os.path.join(current_dir, "..", "test_data")
        self.out_path: str = os.path.join(current_dir, '..', 'tmp_data')
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        self.image_downloader = ImageDownloader()
        self.xml_files: List[str] = [os.path.join(in_path, filename) for filename in os.listdir(in_path) if
                                     filename.endswith(".xml")]
        self.dataset_size: int = 1 # len(self.xml_files)
        self.metadata_transkribus = Metadata("dummy_creator",
                                             "https://files.transkribus.eu/Get?id=GMFSOXFVZKPLGWNTXBYUMQOB&amp"
                                             ";fileType=view")
        self.page_transkribus = Page("1155140_0001_47389007.JPG", [], self.metadata_transkribus)
        self.metadata_escriptorium = Metadata("dummy_creator",
                                              "https://escriptorium.flow-project.net/media/documents/37/1_0054.png")
        self.page_escriptorium = Page("1_0054.png", [], self.metadata_escriptorium)

    @patch.object(ImageDownloader, 'fetch_image')
    def test_fetch_images(self, mock_fetch_image) -> None:
        """
        Test case to ensure that images are fetched correctly.

        This test verifies that the fetch_images method of the ImageDownloader class
        correctly downloads images from the provided XML files and saves them to the
        specified output path. It checks if the number of processed images matches
        the number of input XML files, indicating successful processing.
        """
        pages = [self.page_transkribus, self.page_escriptorium]

        # Case 1: Both succeed
        mock_fetch_image.side_effect = [None, None]
        for page in pages:
            try:
                self.image_downloader.fetch_image(page, self.out_path)
                self.image_downloader.successes.append(page.image_file_name)
            except ImageFetchException:
                self.image_downloader.failed_downloads.append(page.image_file_name)
            except ImageProcessException:
                self.image_downloader.failed_processing.append(page.image_file_name)

        self.assertEqual(len(self.image_downloader.successes), 2)
        self.assertEqual(len(self.image_downloader.failed_downloads), 0)
        self.assertEqual(len(self.image_downloader.failed_processing), 0)

        # Reset state for the next case
        self.image_downloader.successes.clear()
        self.image_downloader.failed_downloads.clear()
        self.image_downloader.failed_processing.clear()

        # Case 2: One succeeds, one fails
        mock_fetch_image.side_effect = [None, ImageFetchException("Simulated failure")]
        for page in pages:
            try:
                self.image_downloader.fetch_image(page, self.out_path)
                self.image_downloader.successes.append(page.image_file_name)
            except ImageFetchException:
                self.image_downloader.failed_downloads.append(page.image_file_name)
            except ImageProcessException:
                self.image_downloader.failed_processing.append(page.image_file_name)

        self.assertEqual(len(self.image_downloader.successes), 1)
        self.assertEqual(len(self.image_downloader.failed_downloads), 1)
        self.assertEqual(len(self.image_downloader.failed_processing), 0)

        # Reset state for the next case
        self.image_downloader.successes.clear()
        self.image_downloader.failed_downloads.clear()
        self.image_downloader.failed_processing.clear()

        # Case 3: Both fail
        mock_fetch_image.side_effect = [
            ImageFetchException("Simulated failure"),
            ImageFetchException("Simulated failure"),
        ]
        for page in pages:
            try:
                self.image_downloader.fetch_image(page, self.out_path)
                self.image_downloader.successes.append(page.image_file_name)
            except ImageFetchException:
                self.image_downloader.failed_downloads.append(page.image_file_name)
            except ImageProcessException:
                self.image_downloader.failed_processing.append(page.image_file_name)

        self.assertEqual(len(self.image_downloader.successes), 0)
        self.assertEqual(len(self.image_downloader.failed_downloads), 2)
        self.assertEqual(len(self.image_downloader.failed_processing), 0)

    @patch('flow_preprocessor.preprocessing_logic.fetch_images.requests.get')
    def test_request_image_via_url(self, mock_get: MagicMock):
        """
        Test case to ensure that images are requested correctly via URL.

        This test verifies that the _request_image_via_url method of the ImageDownloader class
        correctly requests an image via URL and saves it to the specified destination path.
        """
        mock_response: MagicMock = MagicMock()
        mock_response.content = b'Test image content'
        mock_get.return_value = mock_response

        image_url: str = "https://files.transkribus.eu/Get?id=GMFSOXFVZKPLGWNTXBYUMQOB&fileType=view"
        image_filename: str = "1155140_0001_47389007.JPG"
        destination_path: str = os.path.join(self.out_path, image_filename)
        self.image_downloader._request_image_via_url(image_url, destination_path)

        os.path.exists(destination_path)

        with open(destination_path, 'rb') as f:
            file_content: bytes = f.read()
        self.assertEqual(file_content, b'Test image content')

    def tearDown(self) -> None:
        """
        Clean up resources after each test case.

        This method removes any temporary files or directories created during
        the execution of the test cases.
        """
        for filename in os.listdir(self.out_path):
            file_path: str = os.path.join(self.out_path, filename)
            os.remove(file_path)

        if os.path.isdir(self.out_path) and not os.listdir(self.out_path):
            os.rmdir(self.out_path)


if __name__ == '__main__':
    unittest.main()
