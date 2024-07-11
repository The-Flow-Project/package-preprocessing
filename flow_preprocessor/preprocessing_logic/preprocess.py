# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import os
import time
from typing import List, Optional, Union, Dict

from PIL.Image import Image

from flow_githubmanager.github_interaction import GitHubManager
from flow_preprocessor.preprocessing_logic.fetch_images import ImageDownloader
from flow_preprocessor.preprocessing_logic.parse_textlines import PageParser, Page
from flow_preprocessor.preprocessing_logic.process_images import ImageProcessor
from flow_preprocessor.preprocessing_logic.status import Status
from flow_preprocessor.utils.logging.logger import Logger
from flow_preprocessor.exceptions.exceptions import ImageProcessException, ImageFetchException, ParseTextLinesException


# ===============================================================================
# CLASS
# ===============================================================================
# TODO: What about directly using glob.glob in the code instead of this method with os.walk?
def collect_all_file_paths(directory) -> List[Union[str, bytes]]:
    """
    Collect all file paths in a directory.

    :param directory: The directory to search for files.
    :return: A list of file paths.
    """
    file_paths: List[Union[str, bytes]] = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


class Preprocessor:
    """
    Perform preprocessing steps.

    :logger: Logger instance.
    """
    logger = Logger(log_file="logs/fetch_images.log").get_logger()

    def __init__(self, directory: str = "/tmp", github_access_token: Optional[str] = None) -> None:
        """
        initialize parameters.

        :param self.image_processor: ImageProcessor instance.
        :param self.image_downloader: ImageDownloader instance.
        :param self.status: Status instance.
        :param self.github_manager: GitHubManager instance.
        """
        self.image_processor = ImageProcessor()
        self.image_downloader = ImageDownloader()
        self.status = Status(directory)
        self.github_manager = GitHubManager(github_access_token)

    def preprocess(self,
                   repo_name: str,
                   repo_folder: str,
                   in_path: str,
                   out_path: str,
                   crop: bool = False,
                   abbrev: bool = False,
                   stop_on_fail: bool = True) -> None:
        """
        Perform preprocessing steps: fetch XML files from GitHub, preprocess and push to GitHub.

        :param repo_name: the name of the repository the results are fetched from and pushed to.
        :param repo_folder: the folder in the repository the files are fetched from.
        :param in_path: the path the XML files are saved to.
        :param out_path: the path the preprocessed data is saved to.
        :param crop: whether to crop images.
        :param abbrev: whether to expand abbreviations in text.
        :param stop_on_fail: whether to stop processing on failure.
        """

        # TODO: Is there a need the fetch_files method returns the filename/content dict?
        _ = self.github_manager.fetch_files(repo_name, repo_folder, ".xml", in_path)
        files_download = collect_all_file_paths(in_path)
        self.preprocess_xml_file_list(
            files_download,
            in_path,
            out_path,
            stop_on_fail,
            abbrev,
            crop
        )
        files_upload = collect_all_file_paths(out_path)
        self.github_manager.upload_documents(repo_name, files_upload, commit_message="Preprocessed files")

    def preprocess_xml_file_list(self,
                                 page_xml_list: List[str],
                                 in_path: str,
                                 out_path: str,
                                 stop_on_fail: bool = True,
                                 abbrev: bool = False,
                                 crop: bool = False) -> None:
        """
        Preprocess a list of XML files.

        :param page_xml_list: List of XML file paths to be processed.
        :param in_path: The input path where images are located.
        :param out_path: The output path where processed files will be saved.
        :param stop_on_fail: Whether to stop processing on failure.
        :param abbrev: Whether to expand abbreviations in text.
        :param crop: Whether to crop images.
        """
        file_counter = 1
        start_time = time.time()
        for xml_file in page_xml_list:
            try:
                self.preprocess_single_xml_file(crop, abbrev, in_path, out_path, xml_file)
                self.logger.info(f"Preprocessed {xml_file}.")
                self.status.update_progress_on_success(file_counter, xml_file, len(page_xml_list))
            except ImageFetchException as e:
                self.logger.error(f"Error while fetching images: {e}.")
                self.status.update_list_status("Failed to fetch images:", self.image_downloader.failed_downloads)
                self.status.update_list_status("Failed to process images:", self.image_downloader.failed_processing)
                if stop_on_fail:
                    raise e
            except ParseTextLinesException as e:
                self.logger.error(f"Error while parsing textlines: {e}.")
                if stop_on_fail:
                    raise e
            except ImageProcessException as e:
                self.logger.error(f"Error while processing images: {e}.")
                if stop_on_fail:
                    raise e
            file_counter += 1
        self.status.calculate_runtime(start_time)

    def preprocess_single_xml_file(self,
                                   crop: bool,
                                   abbrev: bool,
                                   in_path: str,
                                   out_path: str,
                                   xml_file: str) -> None:
        """
        Preprocess a single XML file.

        :param crop: Whether to crop images.
        :param abbrev: Whether to expand abbreviations in text.
        :param in_path: The input path where images are located.
        :param out_path: The output path where processed files will be saved.
        :param xml_file: The XML file to be processed.
        """
        page_parser = PageParser(xml_file)

        file_name = page_parser.get_image_file_name()
        metadata = page_parser.get_metadata()
        lines_per_page = page_parser.process_lines_from_xml_file()
        page = Page(file_name, lines_per_page, metadata)
        gt_dict = {}
        self.image_downloader.fetch_image(page, out_path)
        for line in page.lines:
            line_name = line.get_output_filename()
            if not abbrev:
                gt_dict[line_name] = line.line_text
            else:
                gt_dict[line_name] = line.expand_abbreviations(line.line_text)

            image_path = os.path.join(in_path, page.image_file_name)

            if not crop:
                image_per_line = self.image_processor.extract_line_from_image(line.line_baseline,
                                                                              line.line_coordinates,
                                                                              image_path,
                                                                              line.line_number)
            else:
                coordinates = [(coord.x, coord.y) for coord in line.line_coordinates]
                image_per_line = self.image_processor.crop_line_from_image(coordinates,
                                                                           image_path,
                                                                           line.line_number)

            self._save_image_per_line(image_per_line, out_path, line_name)

            self._save_gt_dict(gt_dict, out_path)

    def _save_gt_dict(self, gt_dict: Dict[str, str], out_path: str) -> None:
        """
        Save ground truth dictionary to a file.

        :param gt_dict: Dictionary containing line names and texts.
        :param out_path: The output path where the file will be saved.
        """
        file_path = os.path.join(out_path, 'gt.txt')

        with open(file_path, "w") as txt_file:
            for line_name, line_text in gt_dict.items():
                txt_file.write(f"{line_name}\t{line_text}\n")

    def _save_image_per_line(self,
                             image: Image,
                             out_path: str,
                             filename: str) -> None:
        """
        Save an image to a file.

        :param image: The image to be saved.
        :param out_path: The output path where the file will be saved.
        :param filename: The name of the file.
        """
        filepath = os.path.join(out_path, filename)
        image.save(filepath)
