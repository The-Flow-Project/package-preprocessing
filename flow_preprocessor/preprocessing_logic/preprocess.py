# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import os
import json
from typing import List, Optional, Dict, Any

from PIL.Image import Image
from dependency_injector.providers import Coroutine

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

    def __init__(self) -> None:
        """
        initialize parameters.

        :param self.image_processor: ImageProcessor instance.
        :param self.image_downloader: ImageDownloader instance.
        :param self.github_manager: GitHubManager instance.
        :param self.process_id: the ID of the preprocessors process.
        """

        self.image_processor = None
        self.image_downloader = None
        self.github_manager = None
        self.progressStatus = None
        self.statusManager = None
        self.process_id = None
        self.callback = None

    async def preprocess(self,
                         process_id: str,
                         repo_name: str,
                         repo_folder: str,
                         github_access_token: Optional[str] = None,
                         crop: bool = False,
                         abbrev: bool = False,
                         stop_on_fail: bool = True,
                         directory: str = "tmp",
                         in_path: str = "",
                         out_path: str = "preprocessed",
                         callback_preprocess: Coroutine[Any, Any, None] = None,
                         **kwargs,
                         ) -> None:
        """
        Perform preprocessing steps: fetch XML files from GitHub, preprocess and push to GitHub.

        :param process_id: the uniqueid of the preprocessors process.
        :param repo_name: the name of the repository the results are fetched from and pushed to.
        :param repo_folder: the folder in the repository the files are fetched from.
        :param github_access_token: the GitHub access token.
        :param directory: the directory where the files are saved locally.
        :param in_path: the path the XML files are saved to - UUID will be a subfolder.
        :param out_path: the path the preprocessed data is saved to - UUID will be a subfolder.
        :param crop: whether to crop images.
        :param abbrev: whether to expand abbreviations in text.
        :param stop_on_fail: whether to stop processing on failure.
        :param callback_preprocess: a callback function to be called after each step.
        """

        state = PreprocessState(
            process_id=process_id,
            repo_name=repo_name,
            repo_folder=repo_folder,
            directory=directory,
            in_path=in_path,
            out_path=out_path,
            crop=crop,
            abbreviation=abbrev,
            stop_on_fail=stop_on_fail,
            **kwargs
        )
        self.progressStatus = PreprocessState(**state.model_dump(by_alias=True))
        self.statusManager = Status(self.progressStatus)
        self.image_processor = ImageProcessor()
        self.image_downloader = ImageDownloader()
        self.github_manager = GitHubManager(github_access_token)
        self.process_id = process_id
        self.callback = callback_preprocess

        if not os.path.exists(directory):
            os.makedirs(directory)

        in_path = os.path.join(directory, in_path, process_id)
        out_path = os.path.join(directory, out_path, process_id)

        if not os.path.exists(in_path):
            os.makedirs(in_path)
        if not os.path.exists(out_path):
            os.makedirs(out_path)

        print(f"Fetching files from {repo_name} in folder {repo_folder}...")
        print(f"Paths: {in_path} -> {out_path}")
        files_fetched, files_download_failed = self.github_manager.fetch_files(repo_name,
                                                                               repo_folder,
                                                                               ".xml",
                                                                               in_path)
        self.progressStatus = self.statusManager.initialize_status(files_fetched, files_download_failed)
        logger.info(
            f"Preprocessor.preprocess(): Fetched {len(files_fetched)} files from {repo_name} in folder {repo_folder}.")
        logger.info(f"Preprocessor.preprocess(): Starting preprocessing...")
        await self.preprocess_xml_file_list(
            files_fetched,
            in_path,
            out_path,
            stop_on_fail,
            abbrev,
            crop
        )

    async def preprocess_xml_file_list(self,
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

        for i, xml_file in enumerate(page_xml_list):
            logger.info(f"Preprocessor.preprocess_xml_file_list(): Preprocessing {xml_file}...")
            logger.info(f"Preprocessor.preprocess_xml_file_list(): Progress: {i + 1}/{len(page_xml_list)}")
            try:
                self.preprocess_single_xml_file(crop, abbrev, in_path, out_path, xml_file)
                logger.info(f"Preprocessor.preprocess_xml_file_list(): Preprocessed {xml_file}.")
                self.progressStatus = await self.statusManager.update_progress(
                    current_item_index=i + 1,
                    current_item_name=xml_file,
                    success=True
                )

                if self.callback:
                    await self.callback(self.progressStatus.model_dump(by_alias=True))
            except (ParseTextLinesException, ImageProcessException, ImageFetchException) as e:
                logger.error(f"Preprocessor.preprocess_xml_file_list(): Failed to preprocess {xml_file}.",
                             exc_info=True)
                if stop_on_fail:
                    self.statusManager.state.state = StateEnum.FAILED
                    self.progressStatus = await self.statusManager.update_progress(
                        i + 1,
                        xml_file,
                        success=False,
                        exception=e,
                        state_enum=StateEnum.FAILED
                    )
                    logger.error(f"Preprocessor.preprocess_xml_file_list(): Stopping processing due to failure.")
                    raise e
                else:
                    self.progressStatus = await self.statusManager.update_progress(
                        i + 1,
                        xml_file,
                        success=False,
                        exception=e)
                    logger.error(f"Preprocessor.preprocess_xml_file_list(): Continuing processing after failure.")
            finally:
                self.statusManager.calculate_runtime()
                self._save_failed_files(out_path)
                logger.info(
                    f"Preprocessor.preprocess_xml_file_list(): Preprocessing {xml_file} done. "
                    f"Runtime (sec): {self.progressStatus.runtime}")

        self.progressStatus = await self.statusManager.update_progress(state_enum=StateEnum.DONE)
        logger.info(
            f"Preprocessor.preprocess_xml_file_list(): Preprocessing done. ProgressStatus: {self.progressStatus}"
        )
        self.progressStatus.state = StateEnum.DONE
        if self.callback:
            await self.callback(self.progressStatus.model_dump(by_alias=True))

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
        self.image_downloader.fetch_image(page, in_path)
        for line in page.lines:
            line_name = line.get_output_filename()
            if not abbrev:
                gt_dict[line_name] = line.line_text
            else:
                gt_dict[line_name] = line.expand_abbreviations()

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
            image_per_line.close()

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
        filepath = os.path.join(out_path, filename)
        image.save(filepath)

    @staticmethod
    def _save_gt_dict(gt_dict: Dict[str, str], out_path: str) -> None:
        """
        Save ground truth dictionary to a file.

        :param gt_dict: Dictionary containing line names and texts.
        :param out_path: The output path where the file will be saved.
        """
        file_path = os.path.join(out_path, 'gt.txt')

        with open(file_path, "a") as txt_file:
            for line_name, line_text in gt_dict.items():
                escaped_text = json.dumps(line_text)
                txt_file.write(f"{line_name}\t{escaped_text}\n")

    def _save_failed_files(self, out_path: str, to_save: str = 'both') -> None:
        """
        Save failed files list to a file.

        :param out_path: The output path where the file will be saved.
        :param to_save: Which failed files list to save. Options: 'image_process', 'image_download', 'both'.
        """

        if to_save == 'image_process' or to_save == 'both':
            file_path = os.path.join(out_path, f'{self.process_id}_image_process_failed_files.txt')
            with open(file_path, "w") as txt_file:
                for file in self.image_processor.failed_processing:
                    txt_file.write(f"{file}\n")
        if to_save == 'image_download' or to_save == 'both':
            file_path = os.path.join(out_path, f'{self.process_id}_image_download_failed_files.txt')
            with open(file_path, "w") as txt_file:
                for file in self.image_downloader.failed_downloads:
                    txt_file.write(f"{file}\n")
