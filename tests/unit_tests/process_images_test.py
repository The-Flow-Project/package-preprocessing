import os
import unittest
from unittest.mock import patch, MagicMock

from PIL.Image import Image

from flow_preprocessor.preprocessing_logic.parse_textlines import Coordinate, Line
from flow_preprocessor.preprocessing_logic.process_images import ImageProcessor


class ProcessImagesTest(unittest.TestCase):
    def setUp(self) -> None:
        current_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.in_path: str = os.path.join(current_dir, "..", "test_data")
        self.out_path: str = os.path.join(current_dir, '..', 'tmp_data')
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        self.image_transkribus: str = os.path.join(self.in_path, "1155140_0001_47389007.JPG")
        self.image_escriptorium: str = os.path.join(self.in_path, "1_0054.png")
        self.imageProcessor = ImageProcessor(uuid="test1234")
        self.line_escriptorium = Line('0',
                                      "Peter Angerfelder und Richter und auch",
                                      "1_0054.png",
                                      [Coordinate(877, 234), Coordinate(935, 254), Coordinate(1348, 255),
                                       Coordinate(1795, 267), Coordinate(1974, 275), Coordinate(2035, 283),
                                       Coordinate(2064, 355), Coordinate(2020, 364), Coordinate(1937, 356),
                                       Coordinate(1690, 350), Coordinate(1666, 371), Coordinate(1635, 344),
                                       Coordinate(1309, 337), Coordinate(1269, 362), Coordinate(1252, 326),
                                       Coordinate(1203, 365), Coordinate(1151, 364), Coordinate(1148, 317),
                                       Coordinate(959, 326), Coordinate(905, 385), Coordinate(877, 355)],
                                      [Coordinate(877, 306), Coordinate(1074, 309), Coordinate(1272, 318),
                                       Coordinate(1469, 324), Coordinate(1667, 341), Coordinate(2064, 346)],
                                      []
                                      )

        self.line_transkribus = Line('0',
                                     "Galfridus Fresel et Johanna vxor eius per attornatos suos petunt uersus "
                                     "Herbertum de Bexvilla terciam partem manerii",
                                     "1155140_0001_47389007.JPG",
                                     [Coordinate(323, 374), Coordinate(359, 373), Coordinate(395, 373),
                                      Coordinate(431, 373), Coordinate(467, 374), Coordinate(503, 375),
                                      Coordinate(539, 377), Coordinate(575, 379), Coordinate(611, 381),
                                      Coordinate(647, 384), Coordinate(684, 386), Coordinate(720, 389),
                                      Coordinate(756, 391), Coordinate(792, 394), Coordinate(828, 396),
                                      Coordinate(864, 398), Coordinate(900, 400), Coordinate(936, 402),
                                      Coordinate(972, 403), Coordinate(1008, 404), Coordinate(1045, 405),
                                      Coordinate(1045, 375), Coordinate(1008, 374), Coordinate(972, 373),
                                      Coordinate(936, 372), Coordinate(900, 370), Coordinate(864, 368),
                                      Coordinate(828, 366), Coordinate(792, 364), Coordinate(756, 361),
                                      Coordinate(720, 359), Coordinate(684, 356), Coordinate(647, 354),
                                      Coordinate(611, 351), Coordinate(575, 349), Coordinate(539, 347),
                                      Coordinate(503, 345), Coordinate(467, 344), Coordinate(431, 343),
                                      Coordinate(395, 343), Coordinate(359, 343), Coordinate(323, 344)],
                                     [Coordinate(323, 364), Coordinate(359, 363), Coordinate(395, 363),
                                      Coordinate(431, 363), Coordinate(467, 364), Coordinate(503, 365),
                                      Coordinate(539, 367), Coordinate(575, 369), Coordinate(611, 371),
                                      Coordinate(647, 374), Coordinate(684, 376), Coordinate(720, 379),
                                      Coordinate(756, 381), Coordinate(792, 384), Coordinate(828, 386),
                                      Coordinate(864, 388), Coordinate(900, 390), Coordinate(936, 392),
                                      Coordinate(972, 393), Coordinate(1008, 394), Coordinate(1045, 395)],
                                     []
                                     )

    @patch('flow_preprocessor.preprocessing_logic.process_images.Image.open')
    def test_load_image(self, mock_open):
        image_file_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        if not self.image_transkribus.lower().endswith(image_file_extensions):
            self.fail(f"Input file '{self.image_transkribus}' is not an image file")

        mock_image = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_image
        expected_image = mock_image
        result = self.imageProcessor._load_image(self.image_transkribus)
        self.assertEqual(result, expected_image)
        mock_open.assert_called_once_with(self.image_transkribus)

    def test_extract_line_from_image_transkribus(self):
        extracted_line = self.imageProcessor.extract_line_from_image(self.line_transkribus.line_baseline,
                                                                     self.line_transkribus.line_coordinates,
                                                                     self.image_transkribus,
                                                                     self.line_transkribus.line_number)

        self.assertIsInstance(extracted_line, Image)

        os.makedirs(self.out_path, exist_ok=True)
        filename = self.line_transkribus.get_output_filename()
        filepath = os.path.join(self.out_path, filename)
        extracted_line.save(filepath)

        self.assertTrue(os.path.exists(filepath), f"Output file {filepath} does not exist")

    def test_extract_line_from_image_escriptorium(self):
        extracted_line = self.imageProcessor.extract_line_from_image(self.line_escriptorium.line_baseline,
                                                                     self.line_escriptorium.line_coordinates,
                                                                     self.image_escriptorium,
                                                                     self.line_escriptorium.line_number)

        self.assertIsInstance(extracted_line, Image)

        os.makedirs(self.out_path, exist_ok=True)
        filename = self.line_escriptorium.get_output_filename()
        filepath = os.path.join(self.out_path, filename)
        extracted_line.save(filepath)

        self.assertTrue(os.path.exists(filepath), f"Output file {filepath} does not exist")

    def test_crop_line_from_image_transkribus(self):
        coordinates = [(coord.x, coord.y) for coord in self.line_transkribus.line_coordinates]
        cropped_line = self.imageProcessor.crop_line_from_image(coordinates,
                                                                self.image_transkribus,
                                                                self.line_transkribus.line_number)
        self.assertIsInstance(cropped_line, Image)

        os.makedirs(self.out_path, exist_ok=True)
        filename = self.line_transkribus.get_output_filename()
        filepath = os.path.join(self.out_path, filename)
        cropped_line.save(filepath)

        self.assertTrue(os.path.exists(filepath), f"Output file {filepath} does not exist")

    def test_crop_line_from_image_escriptorium(self):
        coordinates = [(coord.x, coord.y) for coord in self.line_escriptorium.line_coordinates]
        cropped_line = self.imageProcessor.crop_line_from_image(coordinates,
                                                                self.image_escriptorium,
                                                                self.line_escriptorium.line_number)
        self.assertIsInstance(cropped_line, Image)

        os.makedirs(self.out_path, exist_ok=True)
        filename = self.line_escriptorium.get_output_filename()
        filepath = os.path.join(self.out_path, filename)
        cropped_line.save(filepath)

        self.assertTrue(os.path.exists(filepath), f"Output file {filepath} does not exist")

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

# TODO: write tests for escriptorium
