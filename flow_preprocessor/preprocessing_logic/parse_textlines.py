# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import re
from typing import List, Dict, Optional, Union
from collections import defaultdict

from lxml import etree as et

from flow_preprocessor.exceptions.exceptions import ParseTextLinesException
from flow_preprocessor.utils.logging.preprocessing_logger import logger


# ===============================================================================
# CLASS
# ===============================================================================
class Coordinate:
    """
    Image coordinate.
    """

    # ===============================================================================
    # METHODS
    # ===============================================================================
    def __init__(self, x: float, y: float):
        """
        initialise x and y coordinates.

        :param x: x coordinate
        :param y: y coordinate
        """
        self.x = x
        self.y = y

    def __eq__(self, other) -> bool:
        """Override the equality operator.

        :param self.x: x coordinate which is compared to other variable.
        :param self.y: y coordinate which is compared to other variable.
        :param other: the other coordinate.
        :return: True if both coordinates are equal, False otherwise.
        """
        if not isinstance(other, Coordinate):
            return False
        return self.x == other.x and self.y == other.y

    @classmethod
    def min_x(cls, coordinates: List['Coordinate']) -> float:
        """set minimum x coordinate.

        :param coordinates: list of coordinates.
        :return: minimum x coordinate.
        """
        return min(coord.x for coord in coordinates)

    @staticmethod
    def max_x(coordinates: List['Coordinate']) -> float:
        """set maximum x coordinate.

        :param coordinates: list of coordinates.
        :return: minimum y coordinate.
        """
        return max(coord.x for coord in coordinates)

    @staticmethod
    def min_y(coordinates: List['Coordinate']) -> float:
        """set minimum y coordinate."""
        return min(coord.y for coord in coordinates)

    @staticmethod
    def max_y(coordinates: List['Coordinate']) -> float:
        """set maximum y coordinate."""
        return max(coord.y for coord in coordinates)


# ===============================================================================
# CLASS
# ===============================================================================
class Line:
    """
    Line from image.
    """

    def __init__(self,
                 line_number: str,
                 line_text: str,
                 line_document: str,
                 line_coordinates: List[Coordinate],
                 line_baseline: List[Coordinate],
                 custom_attributes: Dict[str, List[Dict[str, str]]]):
        """
        initialise class parameters.

        :param line_number: the line index.
        :param line_text: the text extracted from the line.
        :param line_document: the processed document.
        :param line_coordinates: the coordinates of the line.
        :param line_baseline: the baseline coordinates of the line.
        :param custom_attributes: custom attributes of the line, including abbreviations.
        """
        self.line_number = line_number
        self.line_text = line_text
        self.line_document = line_document
        self.line_coordinates = line_coordinates
        self.line_baseline = line_baseline
        self.custom_attributes = custom_attributes

    def __eq__(self, other):
        """Override the equality operator."""
        if isinstance(other, Line):
            return (self.line_number == other.line_number and
                    self.line_text == other.line_text and
                    self.line_document == other.line_document and
                    self.line_coordinates == other.line_coordinates and
                    self.line_baseline == other.line_baseline and
                    self.custom_attributes == other.custom_attributes)
        return False

    def get_output_filename(self) -> str:
        """construct image file name."""
        out_image_name = re.sub(
            r"(\.[a-zA-Z]+)$",
            f".{self.line_number}\\1",
            self.line_document
        )

        return out_image_name

    def get_line_text(self, expand_abbrev=False) -> str:
        """
        extract text from line

        :param expand_abbrev: set whether to keep the abbreviations (False) or expand them (True).

        """
        if expand_abbrev is False:
            return self.line_text
        else:
            expanded_line = self.expand_abbreviations()
            return expanded_line

    def expand_abbreviations(self) -> str:
        """
        Expand the abbreviations.
        """
        add_offset = 0
        text = self.line_text
        if 'abbrev' in self.custom_attributes.keys():
            abbreviations = self.custom_attributes['abbrev']
            for abbreviation in abbreviations:
                if ('offset' not in abbreviation.keys() or
                        'length' not in abbreviation.keys() or
                        'expansion' not in abbreviation.keys()
                ):
                    continue
                offset = int(abbreviation['offset'])
                length = int(abbreviation['length'])
                expansion = abbreviation['expansion']
                text = text[:offset + add_offset] + expansion + text[offset + add_offset + length:]
                add_offset += len(expansion) - length
        return text


# ===============================================================================
# CLASS
# ===============================================================================
class Metadata:
    """
    The metadata section in the xml files.
    """

    def __init__(self, creator, image_url):
        """
        initialise class parameters.
        :param creator: the creator name.
        :param image_url: the image url.

        """
        self.creator = creator
        self.image_url = image_url

    def __eq__(self, other):
        """Override the equality operator."""
        if not isinstance(other, Metadata):
            return False
        return self.creator == other.creator and self.image_url == other.image_url


# ===============================================================================
# CLASS
# ===============================================================================
class Page:
    """
    An XML Page.
    """

    def __init__(self, image_file_name, lines, metadata):
        """
        initialise class parameters.

        :param image_file_name: the name of the image which is downloaded.
        :param lines: lines in one page.
        :param metadata: the metadata of a given XML file.
        """
        self.image_file_name = image_file_name
        self.lines = lines
        self.metadata = metadata


# ===============================================================================
# CLASS
# ===============================================================================
class PageParser:
    """
    Download images from Transkribus and eScriptorium via image URL
    """

    def __init__(self, xml_file) -> None:
        """
        initialise class parameters.

        :param self.logger: logger instance.
        :param self.tree: parse XML parse tree.
        :param self.root: root of XML parse tree.
        :param self.namespace_uri: namespace URI from the XML root element's tag.
        :param self.namespace: namespace dictionary with prefix key.
        :param self.xmlns: namespace declaration.
        :param self.failed_processing: list of images that could not be processed.
        """
        self.tree = et.parse(xml_file)
        self.root = self.tree.getroot()
        self.namespace_uri = self.root.tag.split('}')[0][1:]
        self.namespace = {'prefix': self.namespace_uri}
        self.xmlns = {'ns': self.namespace_uri}
        self.failed_processing = []

    def process_lines_from_xml_file(self) -> List[Line]:
        """
        Transfer line information into Line object.

        :return: list of Line objects.
        """
        line_document = None
        try:
            line_document = self.get_image_file_name()
            line_list: List[Line] = []
            for text_line in self.root.findall(".//ns:TextLine", namespaces=self.xmlns):
                line_number = self.get_line_id(text_line)
                line_text = self.get_line_text_string(text_line)
                line_coordinates = self.get_coordinates(text_line)
                line_baseline_points = self.get_baseline(text_line)
                custom_attributes = self.get_custom_attribute(text_line)
                if line_text == '' or line_coordinates == [] or line_baseline_points == []:
                    logger.warning(
                        f'{self.__class__.__name__} - Skipping line {line_number} in file {line_document} as it is '
                        f'empty or has no coordinates or baseline points.'
                    )
                    continue
                line = Line(line_number,
                            line_text,
                            line_document,
                            line_coordinates,
                            line_baseline_points,
                            custom_attributes)
                line_list.append(line)
        except FileNotFoundError as e:
            logger.error(
                f'{self.__class__.__name__} - XML file not found: {line_document}',
                exc_info=True,
            )
            self.failed_processing.append(line_document)
            raise ParseTextLinesException('XML file not found:  %s', line_document, e)
        except (et.XMLSyntaxError, et.ParseError, IndexError, TypeError, ValueError) as e:
            logger.error(
                f'{self.__class__.__name__} - Error parsing file {line_document}',
                exc_info=True,
            )
            self.failed_processing.append(line_document)
            raise ParseTextLinesException(f'Error parsing file {line_document}: {e}')
        except Exception as e:
            logger.error(
                f'{self.__class__.__name__} - An unexpected error occurred for file {line_document}',
                exc_info=True,
            )
            self.failed_processing.append(line_document)
            raise ParseTextLinesException('An unexpected error occurred for file %s: %s', line_document, e)

        logger.info(f'{self.__class__.__name__} - Successfully processed lines in file {line_document}')
        return line_list

    def get_metadata(self) -> Metadata:
        """
        Construct metadata object.

        :return: Metadata object.
        """
        creator: str = self.get_creator()
        image_url: str = self.get_image_url()
        metadata = Metadata(creator, image_url)
        return metadata

    def get_image_file_name(self) -> str:
        """
        Get filename of the image.

        :return: filename of the image as string.
        """
        return self.root.find(".//ns:Page", namespaces=self.xmlns).attrib.get('imageFilename')

    def get_creator(self) -> str:
        """
        Get creator tag from XML.

        :return: creator tag as string.
        """
        creator = self.root.find(".//ns:Metadata/ns:Creator", namespaces=self.xmlns)
        creator_text: Optional[str] = creator.text
        logger.info(f'{self.__class__.__name__} - Got creator: {creator_text}')
        return creator_text

    def get_image_url(self) -> str:
        """
        Get URL tag from XML.

        return: URL tag as string.
        """
        creator = self.get_creator()
        # self.logger.info(f'{self.__class__.__name__} - Got xmlns: {self.xmlns}')
        if (
                creator is not None
                and creator == "escriptorium"
                and self.namespace_uri == "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
        ):
            image_url: str = self.root.find("ns:Page", namespaces=self.xmlns).get('imageURL')
        else:
            transkribus_metadata = self.root.xpath(
                "ns:Metadata/ns:TranskribusMetadata",
                namespaces=self.xmlns
            )
            if type(transkribus_metadata) is list:
                transkribus_metadata = transkribus_metadata[0]
            image_url = transkribus_metadata.get('imgUrl')
        logger.info(f'{self.__class__.__name__} - Got image URL: {image_url}')
        return image_url

    def get_line_text_string(self, text_line: et.Element) -> str:
        """
        Get line text from XML file.

        :param text_line: A text line from the XML file.
        :return: The text in Unicode.
        """
        if text_line is None:
            raise ValueError("text_line is None")

        unicode_text = text_line.find('.//ns:Unicode', namespaces=self.xmlns)
        if unicode_text is not None and unicode_text.text is not None:
            logger.info(f'{self.__class__.__name__} - Got Unicode text: {unicode_text.text}')
            text: str = unicode_text.text.strip()
        else:
            logger.info(f'{self.__class__.__name__} - No Unicode text found')
            text: str = ''
        return text

    def get_coordinates(self, text_line: et.Element) -> List[Coordinate]:
        """
        Get coordinates from the XML file.

        :param text_line: A text line from the XML file.
        :return: List of coordinates.
        """
        coord = text_line.find(".//ns:Coords", namespaces=self.xmlns)
        points: str = coord.attrib.get("points")

        # self.logger.info(f'{self.__class__.__name__} - Got coordinates: {points}')
        points_list: List[str] = points.split()
        coordinates: List[Coordinate] = [Coordinate(int(p.split(",")[0]), int(p.split(",")[1])) for p in points_list]
        return coordinates

    def get_baseline(self, text_line: et.Element) -> List[Coordinate]:
        """
        Get a list of baseline coordinates.

        :param text_line: a text line from an XML file.
        :return: a list of baseline coordinates.
        """
        baseline_points: List[Coordinate] = []
        baseline = text_line.find(".//ns:Baseline", namespaces=self.xmlns)
        if baseline is not None:
            points: str = baseline.attrib.get("points")
            points_list: List[str] = points.split()
            baseline_points = [Coordinate(int(p.split(",")[0]), int(p.split(",")[1])) for p in points_list]
        return baseline_points

    @staticmethod
    def get_custom_attribute(text_line: et.Element) -> Dict[str, List[Dict[str, str]]]:
        """
        get the custom attribute for a given line.

        :param text_line: a text line from an XML file.
        :return: custom attributes as nested dictionary.
        """
        attributes = defaultdict(list)
        pattern = r"(\w+)\s*\{([^}]+)\}"
        matches = re.findall(pattern, text_line.get('custom'))

        for m in matches:
            key = m[0]
            value_dict = {}

            values = m[1]
            values = [v.strip() for v in values.split(';')]
            for v in values:
                if ':' not in v:
                    continue
                k, v = v.split(':')
                value_dict[k] = v

            attributes[key].append(value_dict)

        return dict(attributes)

    @staticmethod
    def get_line_id(text_line: et.Element) -> Union[str, None]:
        """
        Get the line ID from the XML file.

        :param text_line: A text line from the XML file.
        :return: The line ID as a string.
        """
        return str(text_line.get('id'))

    def get_failed_processing(self) -> List[str]:
        """
        Retrieve the names of the XML files which failed during download.

        :return: List of XML files which failed during processing.
        """
        return self.failed_processing

    def get_page(self):
        return Page(
            self.get_image_file_name(),
            self.process_lines_from_xml_file(),
            self.get_metadata()
        )
