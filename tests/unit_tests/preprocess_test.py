import asyncio
import os
import unittest
from typing import List
from flow_preprocessor.preprocessing_logic.preprocess import Preprocessor


class PreprocessTest(unittest.TestCase):
    def setUp(self) -> None:
        current_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.in_path: str = os.path.join(current_dir, "..", "test_data")
        self.out_path: str = os.path.join(current_dir, '..', 'tmp_data')
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        self.xml_files: List[str] = [os.path.join(self.in_path, filename) for filename in os.listdir(self.in_path) if
                                     filename.endswith(".xml")]
        process_id = 'test_process'
        repo_name = "github-actions-test-organisation/github-interaction-test"
        repo_folder = "xml"
        github_access_token = os.environ.get('GITHUB_ACCESS_TOKEN')
        self.preprocessor = Preprocessor(github_access_token=github_access_token,
                                         process_id=process_id,
                                         repo_name=repo_name,
                                         repo_folder=repo_folder)

    def test_preprocess_with_github(self):
        asyncio.run(self.preprocessor.preprocess())

    def test_preprocess_crop_false(self):
        asyncio.run(self.preprocessor.preprocess_xml_file_list(self.xml_files, self.in_path, self.out_path))

    def test_preprocess_crop_true(self):
        asyncio.run(self.preprocessor.preprocess_xml_file_list(self.xml_files, self.in_path, self.out_path, crop=True))

    def test_preprocess_abbrev_true(self):
        asyncio.run(
            self.preprocessor.preprocess_xml_file_list(self.xml_files, self.in_path, self.out_path, abbrev=True))

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
