"""
Preprocessor class
"""

# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import os
import json
import shutil
import csv
from typing import List, Dict, Any, Coroutine, Callable, Optional

from PIL.Image import Image

from flow_githubmanager.github_interaction import GitHubManager

from flow_preprocessor.preprocessing_logic.fetch_images import ImageDownloader
from flow_preprocessor.preprocessing_logic.parse_textlines import PageParser, Page
from flow_preprocessor.preprocessing_logic.process_images import ImageProcessor
from flow_preprocessor.preprocessing_logic.status import Status
from flow_preprocessor.preprocessing_logic.models import PreprocessState, StateEnum
from flow_preprocessor.exceptions.exceptions import ImageProcessException, ImageFetchException, ParseTextLinesException
from flow_preprocessor.utils.logging.preprocessing_logger import logger


# ===============================================================================
# CLASS
# ===============================================================================

class Preprocessor:
    """
    Perform preprocessing steps.
    """

    def __init__(
            self,
            process_id: str,
            repo_name: str,
            repo_folder: str,
            github_access_token: Optional[str],
            callback_preprocess: Callable[[dict], Coroutine[Any, Any, None]] = None,
            crop: bool = False,
            abbrev: bool = False,
            stop_on_fail: bool = True,
            # segment: bool = False,
            **kwargs,
    ) -> None:
        """
        initialize parameters.

        :param process_id: id of preprocessing process.
        :param repo_name: name of repo.
        :param repo_folder: folder where repo is located.
        :param github_access_token: github access token.
        :param callback_preprocess: callback function for preprocessing.
        :param crop: whether to crop.
        :param abbrev: whether to abbrev.
        :param stop_on_fail: whether to stop preprocessing.
        :param segment: wether to segment the image.
        :param self.image_processor: ImageProcessor instance.
        :param self.image_downloader: ImageDownloader instance.
        :param self.github_manager: GitHubManager instance.
        :param self.process_id: the ID of the preprocessors process.
        :param kwargs: keyword arguments for status.
        """

        self.process_id = process_id
        self.repo_name = repo_name
        self.repo_folder = repo_folder
        self.github_access_token = github_access_token
        self.callback = callback_preprocess
        self.crop = crop
        self.abbrev = abbrev
        self.stop_on_fail = stop_on_fail
        self.directory = os.path.join('data', repo_name.replace('/', '___'))
        self.in_path = os.path.join(self.directory, 'fetched')
        self.out_path = os.path.join(self.directory, 'preprocessed')
        self.kwargs = kwargs
        # TODO: Change as soon as Segmenter is implemented
        # self.segment = segment
        self.segment = False

        self.image_processor = ImageProcessor()
        self.image_downloader = ImageDownloader()
        self.github_manager = GitHubManager(github_access_token)

        state = PreprocessState(
            process_id=self.process_id,
            repo_name=self.repo_name,
            repo_folder=self.repo_folder,
            crop=self.crop,
            abbreviation=self.abbrev,
            stop_on_fail=self.stop_on_fail,
            segment=self.segment,
            **self.kwargs
        )
        self.progress_status = PreprocessState(**state.model_dump(by_alias=True))
        self.status_manager = Status(self.progress_status)

    async def preprocess(self) -> None:
        """
        Perform preprocessing steps: fetch XML files from GitHub, preprocess and push to GitHub.
        """

        # Removing the existing directory to reset any former preprocessing of this repository
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
            os.makedirs(self.directory)

        if not os.path.exists(self.in_path):
            os.makedirs(self.in_path)
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)

        print(f"Fetching files from {self.repo_name} in folder {self.repo_folder}...")
        print(f"Paths: {self.in_path} -> {self.out_path}")

        files_fetched, files_download_failed = self.github_manager.fetch_files(
            self.repo_name,
            self.repo_folder,
            ".xml",
            self.in_path,
        )
        self.progress_status = self.status_manager.initialize_status(files_fetched, files_download_failed)
        logger.info(
            "Preprocessor.preprocess(): Fetched %d files from %s in folder %s.",
            len(files_fetched),
            self.repo_name,
            self.repo_folder,
        )
        logger.info("Preprocessor.preprocess(): Starting preprocessing...")
        await self.preprocess_xml_file_list(files_fetched)

    async def preprocess_xml_file_list(self, page_xml_list: List[str]) -> None:
        """
        Preprocess a list of XML files.

        :param page_xml_list: List of XML file paths to be processed.
        """

        for i, xml_file in enumerate(page_xml_list):
            logger.info("Preprocessor.preprocess_xml_file_list(): Preprocessing %s...", xml_file)
            logger.info("Preprocessor.preprocess_xml_file_list(): Progress: %d/%d",
                        i + 1,
                        len(page_xml_list)
                        )
            try:
                self.preprocess_single_xml_file(xml_file)
                logger.info("Preprocessor.preprocess_xml_file_list(): Preprocessed %s.", xml_file)
                self.progress_status = await self.status_manager.update_progress(
                    current_item_index=i + 1,
                    current_item_name=xml_file
                )

                if self.callback:
                    await self.callback(
                        self.progress_status.model_dump(
                            by_alias=True,
                            exclude={'line_images'}
                        )
                    )
            except (ParseTextLinesException, ImageProcessException, ImageFetchException) as e:
                logger.error("Preprocessor.preprocess_xml_file_list(): Failed to preprocess %s.", xml_file,
                             exc_info=True)
                if self.stop_on_fail:
                    self.status_manager.state.state = StateEnum.FAILED
                    self.progress_status = await self.status_manager.update_progress(
                        i + 1,
                        xml_file,
                        success=False,
                        exception=e,
                        state_enum=StateEnum.FAILED,
                    )
                    logger.error("Preprocessor.preprocess_xml_file_list(): Stopping processing due to failure.")
                    raise e
                self.progress_status = await self.status_manager.update_progress(
                    i + 1,
                    xml_file,
                    success=False,
                    exception=e,
                )
                logger.error("Preprocessor.preprocess_xml_file_list(): Continuing processing after failure.")
            finally:
                self.status_manager.calculate_runtime()
                self._save_failed_files(self.out_path)
                logger.info(
                    "Preprocessor.preprocess_xml_file_list(): Preprocessing %s done. Runtime (sec): %s",
                    xml_file,
                    self.progress_status.runtime,
                )

        self.progress_status = await self.status_manager.update_progress(state_enum=StateEnum.DONE)
        logger.info(
            "Preprocessor.preprocess_xml_file_list(): Preprocessing done. ProgressStatus: %s",
            self.progress_status,
        )

        self.progress_status.state = StateEnum.DONE
        if self.callback:
            await self.callback(
                self.progress_status.model_dump(
                    by_alias=True,
                    exclude={'line_images'}
                )
            )

    def preprocess_single_xml_file(self, xml_file: str) -> None:
        """
        Preprocess a single XML file.

        :param xml_file: The XML file to be processed.
        """
        page_parser = PageParser(xml_file, self.segment)

        file_name = page_parser.get_image_file_name()
        metadata = page_parser.get_metadata()
        lines_per_page = page_parser.process_lines_from_xml_file()
        page = Page(file_name, lines_per_page, metadata)
        gt_dict = {}
        try:
            self.image_downloader.fetch_image(page, self.in_path)
        except ImageFetchException as e:
            logger.error("Error fetching image for file %s from %s.", file_name, e)
            if self.stop_on_fail:
                raise
            return

        for line in page.lines:
            line_name = line.get_output_filename()
            if not self.abbrev:
                gt_dict[line_name] = line.line_text
            else:
                gt_dict[line_name] = line.expand_abbreviations()

            logger.info("Added to gt_dict: key = %s, value = %s", line_name, gt_dict[line_name])
            image_path = os.path.join(self.in_path, page.image_file_name)

            if not self.crop:
                image_per_line = self.image_processor.extract_line_from_image(line.line_baseline,
                                                                              line.line_coordinates,
                                                                              image_path,
                                                                              line.line_number)
            else:
                coordinates = [(coord.x, coord.y) for coord in line.line_coordinates]
                image_per_line = self.image_processor.crop_line_from_image(coordinates,
                                                                           image_path,
                                                                           line.line_number)

            self._save_image_per_line(image_per_line, self.out_path, line_name)
            image_per_line.close()
            self.status_manager.update_image_list(line_name)

        self._save_gt_dict(gt_dict, self.out_path)

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
        filepath = os.path.join(out_path, filename)
        image.save(filepath)

    @staticmethod
    def _save_gt_dict(gt_dict: Dict[str, str], out_path: str) -> None:
        """
        Save ground truth dictionary to a file.

        :param gt_dict: Dictionary containing line names and texts.
        :param out_path: The output path where the file will be saved.
        """
        file_path = os.path.join(out_path, "gt.txt")

        with open(file_path, "a", encoding="utf-8") as txt_file:
            for line_name, line_text in gt_dict.items():
                txt_file.write(f"{line_name}\t{line_text}\n")

    @staticmethod
    def _get_gt_dict(out_path: str) -> Dict[str, str]:
        """
        Get ground truth dictionary from a file.
        :param out_path: The output path where the file is saved.
        """
        file_path = os.path.join(out_path, 'gt.txt')
        gt_dict = {}
        with open(file_path, newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            for row in reader:
                gt_dict[row[0]] = row[1]

        return gt_dict

    def _save_failed_files(self, to_save: str = 'both') -> None:
        """
        Save failed files list to a file.

        :param to_save: Which failed files list to save. Options: 'image_process', 'image_download', 'both'.
        """
        repo_str = self.repo_name.replace('/', '___')
        if to_save in ['image_process', 'both']:
            file_path = os.path.join(self.out_path, f'{repo_str}_image_process_failed_files.txt')
            with open(file_path, "w", encoding='utf-8') as txt_file:
                for file in self.image_processor.failed_processing:
                    txt_file.write(f"{file}\n")
        if to_save in ('image_download', 'both'):
            file_path = os.path.join(self.out_path, f'{repo_str}_image_download_failed_files.txt')
            with open(file_path, "w", encoding='utf-8') as txt_file:
                for file in self.image_downloader.failed_downloads:
                    txt_file.write(f"{file}\n")
