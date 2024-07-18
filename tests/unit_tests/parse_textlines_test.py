import os
import unittest
from flow_preprocessor.preprocessing_logic.parse_textlines import Line, PageParser, Metadata, Coordinate, Page
from lxml import etree as et


class ParseTextLinesTest(unittest.TestCase):

    @staticmethod
    def set_namespace(xml_file):
        root = et.parse(xml_file).getroot()
        namespace_uri = root.tag.split('}')[0][1:]
        xmlns = '{' + namespace_uri + '}'

        text_line = root.find(f".//{xmlns}TextLine")

        parser = PageParser(xml_file=xml_file, uuid="test_uuid")

        return parser, text_line, xmlns

    def setUp(self) -> None:
        current_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.in_path: str = os.path.join(current_dir, "..", "test_data")
        xml_file_transkribus: str = os.path.join(self.in_path, "1155140_0001_47389007.xml")
        xml_file_escriptorium: str = os.path.join(self.in_path, "1_0054.xml")
        xml_file_transkribus_with_abbreviations = os.path.join(self.in_path, "1520131_0003_58329924.xml")

        self.parser_transkribus, self.text_line_transkribus, self.xmlns_transkribus = self.set_namespace(
            xml_file_transkribus)
        self.parser_escriptorium, self.text_line_escriptorium, self.xmlns_escriptorium = self.set_namespace(
            xml_file_escriptorium)
        self.parser_transkribus_with_abbreviations, self.text_line_transkribus_with_abbreviations, self.xmlns_transkribus_with_abbreviations = self.set_namespace(
            xml_file_transkribus_with_abbreviations)

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
                                     [
                                         {'offset': 49, 'length': 2, 'expansion': 'en'}
                                     ]
                                     )
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

        self.line_transkribus_with_abbreviations = Line('0',
                                                        "Int erste quam den Steden en breff van dem hertogē van Sleswik",
                                                        "1520131_0003_58329924.jpg",
                                                        [Coordinate(572, 491), Coordinate(2174, 503),
                                                         Coordinate(2174, 473), Coordinate(572, 461)],
                                                        [Coordinate(572, 491), Coordinate(2174, 503)],
                                                        [
                                                            {'offset': 49, 'length': 2, 'expansion': 'en'}
                                                        ]
                                                        )

        self.metadata_transkribus = Metadata(
            '''prov=University of Rostock/Institute of Mathematics/CITlab|PLANET AI GmbH/Tobias 
            Gruening/tobias.gruening@planet-ai.de:name=/net_tf/LA73_249_0mod360.pb:de.uros.citlab.segmentation
            .CITlab_LA_ML:v=2.6.7 prov=University of Rostock/Institute of Mathematics/CITlab|PLANET AI GmbH/Tobias 
            Gruening/tobias.gruening@planet-ai.de:name=/net_tf/LA73_249_0mod360.pb:de.uros.citlab.segmentation
            .CITlab_LA_ML:v=2.6.7 Transkribus''',
            "https://files.transkribus.eu/Get?id=GMFSOXFVZKPLGWNTXBYUMQOB&fileType=view")

        self.metadata_escriptorium = Metadata("escriptorium",
                                              "https://escriptorium.flow-project.net/media/documents/37/1_0054.png")

        self.page_transkribus = Page("1155140_0001_47389007.JPG",
                                     [self.line_transkribus],
                                     self.metadata_transkribus)

        self.page_escriptorium = Page("1_0054.png",
                                      [self.line_escriptorium],
                                      self.metadata_escriptorium)

    def test_get_output_filename(self):
        expected_output = "1155140_0001_47389007.0.JPG"
        result = self.line_transkribus.get_output_filename()
        self.assertEqual(expected_output, result)

    def test_get_line_text_string(self):
        result = self.parser_transkribus.get_line_text_string(self.text_line_transkribus, self.xmlns_transkribus)
        expected_output = self.line_transkribus.line_text
        self.assertEqual(expected_output, result)

    def test_process_lines_from_xml_file(self):
        line_list = self.parser_transkribus_with_abbreviations.process_lines_from_xml_file()
        line = line_list[0]
        expected_output = self.line_transkribus_with_abbreviations

        # Check if all attributes match
        self.assertEqual(expected_output.line_number, line.line_number)
        self.assertEqual(expected_output.line_text, line.line_text)
        self.assertEqual(expected_output.line_document, line.line_document)

        # Check if line_coordinates match
        self.assertEqual(len(expected_output.line_coordinates), len(line.line_coordinates))
        for i in range(len(expected_output.line_coordinates)):
            self.assertEqual(expected_output.line_coordinates[i].x, line.line_coordinates[i].x)
            self.assertEqual(expected_output.line_coordinates[i].y, line.line_coordinates[i].y)

        # Check if line_baseline match
        self.assertEqual(len(expected_output.line_baseline), len(line.line_baseline))
        for i in range(len(expected_output.line_baseline)):
            self.assertEqual(expected_output.line_baseline[i].x, line.line_baseline[i].x)
            self.assertEqual(expected_output.line_baseline[i].y, line.line_baseline[i].y)

        # Check if abbreviations match
        self.assertEqual(len(expected_output.abbreviations), len(line.abbreviations))
        for i in range(len(expected_output.abbreviations)):
            self.assertEqual(expected_output.abbreviations[i], line.abbreviations[i])

    def test_get_coordinates(self):
        result = self.parser_transkribus.get_coordinates(self.text_line_transkribus, self.xmlns_transkribus)
        expected_output = self.line_transkribus.line_coordinates
        self.assertEqual(expected_output, result)

    def test_get_image_file_name(self):
        result = self.parser_transkribus.get_image_file_name()
        expected_output = self.page_transkribus.image_file_name
        self.assertEqual(expected_output, result)

    def test_get_image_url_transkribus(self):
        result = self.parser_transkribus.get_image_url()
        expected_output = self.page_transkribus.metadata.image_url
        self.assertEqual(expected_output, result)

    def test_get_image_url_escriptorium(self):
        result = self.parser_escriptorium.get_image_url()
        expected_output = self.page_escriptorium.metadata.image_url
        self.assertEqual(expected_output, result)

    def test_get_creator_escriptorium(self):
        result = self.parser_escriptorium.get_creator()
        expected_output = self.page_escriptorium.metadata.creator
        self.assertEqual(expected_output, result)

    def test_get_creator_transkribus(self):
        result = self.parser_transkribus.get_creator()
        expected_output = self.page_transkribus.metadata.creator
        self.assertEqual(expected_output, result)

    def test_min_x(self):
        coordinates = [Coordinate(1, 2), Coordinate(3, 4), Coordinate(0, 6)]
        self.assertEqual(Coordinate.min_x(coordinates), 0)

    def test_max_x(self):
        coordinates = [Coordinate(1, 2), Coordinate(3, 4), Coordinate(0, 6)]
        self.assertEqual(Coordinate.max_x(coordinates), 3)

    def test_min_y(self):
        coordinates = [Coordinate(1, 2), Coordinate(3, 4), Coordinate(0, 6)]
        self.assertEqual(Coordinate.min_y(coordinates), 2)

    def test_max_y(self):
        coordinates = [Coordinate(1, 2), Coordinate(3, 4), Coordinate(0, 6)]
        self.assertEqual(Coordinate.max_y(coordinates), 6)

    def test_get_metadata(self):
        result = self.parser_transkribus.get_metadata()
        expected_output = self.page_transkribus.metadata
        self.assertEqual(expected_output, result)

    def test_get_abbreviations(self):
        result = self.parser_transkribus_with_abbreviations.get_abbreviations(
            self.text_line_transkribus_with_abbreviations)
        expected_output = self.line_transkribus.abbreviations
        self.assertEqual(expected_output, result)

    def test_expand_abbreviations(self):
        text = "Int erste quam den Steden en breff van dem hertogē van Sleswik"
        result = self.line_transkribus.expand_abbreviations(text)
        expected_output = "Int erste quam den Steden en breff van dem hertogen van Sleswik"
        self.assertEqual(expected_output, result)

    def test_get_line_text_with_abbreviations(self):
        result = self.line_transkribus_with_abbreviations.get_line_text(abbrev=True)
        expected_output = "Int erste quam den Steden en breff van dem hertogē van Sleswik"
        self.assertEqual(expected_output, result)

    def test_get_line_text_without_abbreviations(self):
        result = self.line_transkribus_with_abbreviations.get_line_text(abbrev=False)
        expected_output = "Int erste quam den Steden en breff van dem hertogen van Sleswik"
        self.assertEqual(expected_output, result)


if __name__ == '__main__':
    unittest.main()

# TODO: add comments and typing
