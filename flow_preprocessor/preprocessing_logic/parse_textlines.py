# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
import re
from typing import List, Dict, Optional
from lxml import etree as et

from flow_preprocessor.exceptions.exceptions import ParseTextLinesException
from flow_preprocessor.utils.logging.logger import Logger


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

    @classmethod
    def max_x(cls, coordinates:  List['Coordinate']) -> float:
        """set maximum x coordinate.

        :param coordinates: list of coordinates.
        :return: minimum y coordinate.
        """
        return max(coord.x for coord in coordinates)

    @classmethod
    def min_y(cls, coordinates: List['Coordinate']) -> float:
        """set minimum y coordinate."""
        return min(coord.y for coord in coordinates)

    @classmethod
    def max_y(cls, coordinates: List['Coordinate']) -> float:
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
                 abbreviations: List[Dict]):
        """
        initialise class parameters.

        :param line_number: the line index.
        :param line_text: the text extracted from the line.
        :param line_document: the processed document.
        :param line_coordinates: the coordinates of the line.
        :param line_baseline: the baseline coordinates of the line.
        :param abbreviations: the abbreviations found in the line.
        """
        self.line_number = line_number
        self.line_text = line_text
        self.line_document = line_document
        self.line_coordinates = line_coordinates
        self.line_baseline = line_baseline
        self.abbreviations = abbreviations

    def __eq__(self, other):
        """Override the equality operator."""
        if isinstance(other, Line):
            return (self.line_number == other.line_number and
                    self.line_text == other.line_text and
                    self.line_document == other.line_document and
                    self.line_coordinates == other.line_coordinates and
                    self.line_baseline == other.line_baseline and
                    self.abbreviations == other.abbreviations)
        return False

    def get_output_filename(self) -> str:
        """construct image file name."""
        out_image_name = re.sub(r"\.([^\.]*?)$", r".{0}.\1".format(self.line_number), self.line_document)
        return out_image_name

    def get_line_text(self, abbrev=False):
        """
        extract text from line

        :param abbrev: set whether to extract abbreviations or not.

        """
        if abbrev is True:
            return self.line_text
        else:
            expanded_line = self.expand_abbreviations(self.line_text)
            return expanded_line

    def expand_abbreviations(self, text):
        """
        Expand the abbreviations.

        :param text: the text to be expanded.

        """
        add_offset = 0
        for abbreviation in self.abbreviations:
            offset = abbreviation['offset']
            length = abbreviation['length']
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

    :logger: Logger instance
    """
    logger = Logger(log_file="logs/parse_textlines.log").get_logger()

    def __init__(self, xml_file) -> None:
        """
        initialise class parameters.

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
        self.xmlns = '{' + self.namespace_uri + '}'
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
            line_number = 0
            for text_line in self.root.iterfind(f".//{self.xmlns}TextLine"):
                line_text = self.get_line_text_string(text_line, self.xmlns)
                line_coordinates = self.get_coordinates(text_line, self.xmlns)
                line_baseline_points = self.get_baseline(text_line, self.xmlns)
                abbreviations = self.get_abbreviations(text_line)
                line = Line(str(line_number), line_text, line_document, line_coordinates, line_baseline_points, abbreviations)
                line_list.append(line)
                line_number += 1
            self.logger.info("Successfully processed lines in file %s", line_document)
            return line_list
        except FileNotFoundError as e:
            self.logger.error('XML file not found: %s', line_document, str(e))
            self.failed_processing.append(line_document)
            raise ParseTextLinesException('XML file not found:  %s', line_document, e)
        except (et.XMLSyntaxError, et.ParseError, IndexError, TypeError, ValueError) as e:
            self.logger.error('Error parsing file %s: %s', line_document, str(e))
            self.failed_processing.append(line_document)
            raise ParseTextLinesException('Error parsing file %s: %s', line_document, e)
        except Exception as e:
            self.logger.error('An unexpected error occurred for file %s: %s', line_document, str(e))
            self.failed_processing.append(line_document)
            raise ParseTextLinesException('An unexpected error occurred for file %s: %s', line_document, e)

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
        return self.root.find(f".//{self.xmlns}Page").get('imageFilename')

    def get_creator(self) -> str:
        """
        Get creator tag from XML.

        :return: creator tag as string.
        """
        creator = self.root.find(".//prefix:Metadata/prefix:Creator", namespaces=self.namespace)
        creator_text: Optional[str] = creator.text
        return creator_text

    def get_image_url(self) -> str:
        """
        Get URL tag from XML.

        return: URL tag as string.
        """
        creator = self.get_creator()
        if creator is not None and creator == "escriptorium" and self.xmlns == ("{http://schema.primaresearch.org/PAGE"
                                                                                "/gts/pagecontent/2019-07-15}"):
            image_url: str = self.root.find(f".//{self.xmlns}Page").get('imageURL')
        else:
            transkribus_metadata = self.root.xpath("//prefix:Metadata/prefix:TranskribusMetadata", namespaces=self.namespace)[0]
            image_url = transkribus_metadata.get('imgUrl')
        return image_url

    def get_line_text_string(self, text_line: et.Element, xmlns: str) -> str:
        """
        Get line text from XML file.

        :param text_line: A text line from the XML file.
        :param xmlns: The XML namespace.
        :return: The text in unicode.
        """
        unicode_text: str = text_line.find(f"./{xmlns}TextEquiv/{xmlns}Unicode").text.strip()
        return unicode_text

    def get_coordinates(self, text_line: et.Element, xmlns: str) -> List[Coordinate]:
        """
        Get coordinates from the XML file.

        :param text_line: A text line from the XML file.
        :param xmlns: The XML namespace.
        :return: List of coordinates.
        """
        coord = text_line.find(f"./{xmlns}Coords")
        points: str = coord.get("points")
        points_list: List[str] = points.split()
        coordinates: List[Coordinate] = [Coordinate(int(p.split(",")[0]), int(p.split(",")[1])) for p in points_list]
        return coordinates

    def get_baseline(self, text_line: et.Element, xmlns: str) -> List[Coordinate]:
        """
        Get a list of baseline coordinates.

        :param text_line: a text line from an XML file.
        :param xmlns: the XML namespace.
        :return: a list of baseline coordinates.
        """
        baseline_points: List[Coordinate] = []
        baseline = text_line.find(f"./{xmlns}Baseline")
        if baseline is not None:
            points: str = baseline.get("points")
            points_list: List[str] = points.split()
            baseline_points = [Coordinate(int(p.split(",")[0]), int(p.split(",")[1])) for p in points_list]
        return baseline_points

    def get_abbreviations(self, text_line: et.Element) -> List[Dict[str, str]]:
        """
        get the abbreviations for a given line.

        :param: a text line from an XML file.
        :return: list of dictionaries containing offset, length and expansion.
        """
        abbreviations: List[Dict[str, str]] = []
        custom_attr: str = text_line.get('custom')
        if custom_attr is not None:
            split_string: List[str] = custom_attr.split('}')
            for abbreviation_str in split_string:
                if re.search('(abbrev).*(expansion)', abbreviation_str):
                    abbreviation: Dict[str, str] = {}
                    parts: List[str] = abbreviation_str.strip().strip('abbrev {').rstrip(';').replace(' ', '').split(';')
                    for part in parts:
                        p: List[str] = part.split(':')
                        if p[0] == 'expansion':
                            abbreviation[p[0]] = p[1]
                        else:
                            abbreviation[p[0]] = str(int(p[1]))  # converting to string to maintain consistency
                    if 'expansion' in abbreviation.keys():
                        abbreviations.append(abbreviation)
        return abbreviations

    def get_failed_processing(self) -> List[str]:
        """
        Retrieve the names of the XML files which failed during download.

        :return: List of XML files which failed during processing.
        """
        return self.failed_processing
