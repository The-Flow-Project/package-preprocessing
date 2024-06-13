import os
import unittest
from typing import List
from flow_preprocessor.preprocessing_logic.preprocess import Preprocessor


class PreprocessTest(unittest.TestCase):
    def setUp(self) -> None:
        current_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.in_path: str = os.path.join(current_dir, "..", "test_data")
        self.in_path_github: str = os.path.join(current_dir, "..", "github_download")
        self.out_path: str = os.path.join(current_dir, '..', 'tmp_data')
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        if not os.path.exists(self.in_path_github):
            os.makedirs(self.in_path_github)
        self.xml_files: List[str] = [os.path.join(self.in_path, filename) for filename in os.listdir(self.in_path) if
                                filename.endswith(".xml")]
        self.preprocessor = Preprocessor()

    def test_preprocess_with_github(self):
        repo_name = "github-actions-test-organisation/github-interaction-test"
        self.preprocessor.preprocess(repo_name, self.in_path_github, self.in_path_github)

    def test_preprocess_crop_false(self):
        self.preprocessor.preprocess_xml_file_list(self.xml_files, self.in_path, self.out_path)

    def test_preprocess_crop_true(self):
        self.preprocessor.preprocess_xml_file_list(self.xml_files, self.in_path, self.out_path, crop=True)

    def test_preprocess_abbrev_true(self):
        self.preprocessor.preprocess_xml_file_list(self.xml_files, self.in_path, self.out_path, abbrev=True)

    def tearDown(self) -> None:
        """
        Clean up resources after each test case.

    # def test_preprocess_crop_true(self):
    #     self.preprocessor.preprocess(self.in_path, self.out_path, crop=True)
    #
    # def test_preprocess_abbrev_true(self):
    #     self.preprocessor.preprocess(self.in_path, self.out_path, abbrev=True)
    #
    # def tearDown(self) -> None:
    #     """
    #     Clean up resources after each test case.
    #
    #     This method removes any temporary files or directories created during
    #     the execution of the test cases.
    #     """
    #     for filename in os.listdir(self.out_path):
    #         file_path: str = os.path.join(self.out_path, filename)
    #         os.remove(file_path)
    #
    #     if os.path.isdir(self.out_path) and not os.listdir(self.out_path):
    #         os.rmdir(self.out_path)


if __name__ == '__main__':
    unittest.main()
