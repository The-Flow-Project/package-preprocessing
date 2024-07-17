# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import os
import time
from glob import glob
from typing import List, Optional, Dict

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


# TODO: Why is everything logged multiple times?
class Preprocessor:
    """
    Perform preprocessing steps.
    """

    def __init__(self, uuid: str, directory: str = "tmp", github_access_token: Optional[str] = None) -> None:
        """
        initialize parameters.

        :param self.image_processor: ImageProcessor instance.
        :param self.image_downloader: ImageDownloader instance.
        :param self.status: Status instance.
        :param self.github_manager: GitHubManager instance.
        :param self.uuid: the UUID of the preprocessors process.
        :param self.logger: Logger instance.
        """
        self.image_processor = ImageProcessor()
        self.image_downloader = ImageDownloader()
        self.status = Status(os.path.join(directory, uuid))
        self.github_manager = GitHubManager(github_access_token)
        self.uuid = uuid
        self.logger = Logger(log_file=f"logs/{uuid}_preprocess.log").get_logger()

        if not os.path.exists(directory):
            os.makedirs(directory)

        self.directory = directory

    def preprocess(self,
                   repo_name: str,
                   repo_folder: str,
                   in_path: str = "",
                   out_path: str = "preprocessed",
                   crop: bool = False,
                   abbrev: bool = False,
                   stop_on_fail: bool = True) -> None:
        """
        Perform preprocessing steps: fetch XML files from GitHub, preprocess and push to GitHub.

        :param repo_name: the name of the repository the results are fetched from and pushed to.
        :param repo_folder: the folder in the repository the files are fetched from.
        :param in_path: the path the XML files are saved to - UUID will be a subfolder.
        :param out_path: the path the preprocessed data is saved to - UUID will be a subfolder.
        :param crop: whether to crop images.
        :param abbrev: whether to expand abbreviations in text.
        :param stop_on_fail: whether to stop processing on failure.
        """

        # TODO: Is there a need the fetch_files method returns the filename/content dict?
        in_path = os.path.join(self.directory, in_path, self.uuid)
        out_path = os.path.join(self.directory, out_path, self.uuid)

        if not os.path.exists(in_path):
            os.makedirs(in_path)
        if not os.path.exists(out_path):
            os.makedirs(out_path)

        print(f"Fetching files from {repo_name} in folder {repo_folder}...")
        print(f"Paths: {in_path} -> {out_path}")
        _ = self.github_manager.fetch_files(repo_name, repo_folder, ".xml", in_path)
        files_download = glob(f'{in_path}/**/*', recursive=True)
        self.preprocess_xml_file_list(
            files_download,
            in_path,
            out_path,
            stop_on_fail,
            abbrev,
            crop
        )
        files_upload = glob(f'{out_path}/**/*', recursive=True)
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
        # in_path = os.path.join(self.directory, in_path, self.uuid)
        # out_path = os.path.join(self.directory, out_path, self.uuid)

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
        # in_path = os.path.join(self.directory, in_path, self.uuid)
        # out_path = os.path.join(self.directory, out_path, self.uuid)

        file_name = page_parser.get_image_file_name()
        metadata = page_parser.get_metadata()
        lines_per_page = page_parser.process_lines_from_xml_file()
        page = Page(file_name, lines_per_page, metadata)
        gt_dict = {}
        self.image_downloader.fetch_image(page, in_path)
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

    @staticmethod
    def _save_image_per_line(image: Image,
                             out_path: str,
                             filename: str) -> None:
        """
        Save an image to a file.

        :param image: The image to be saved.
        :param out_path: The output path where the file will be saved.
        :param filename: The name of the file.
        """
        # out_path = os.path.join(out_path, self.uuid)
        filepath = os.path.join(out_path, filename)
        image.save(filepath)

    @staticmethod
    def _save_gt_dict(gt_dict: Dict[str, str], out_path: str) -> None:
        """
        Save ground truth dictionary to a file.

        :param gt_dict: Dictionary containing line names and texts.
        :param out_path: The output path where the file will be saved.
        """
        # out_path = os.path.join(out_path, self.uuid)
        file_path = os.path.join(out_path, 'gt.txt')

        with open(file_path, "w") as txt_file:
            for line_name, line_text in gt_dict.items():
                txt_file.write(f"{line_name}\t{line_text}\n")
