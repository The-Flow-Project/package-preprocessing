"""
Implementation of image processing
"""

# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
from typing import List, Tuple, Union
import PIL
from PIL import Image, ImageDraw
from flow_preprocessor.exceptions.exceptions import ImageProcessException
from flow_preprocessor.preprocessing_logic.parse_textlines import Coordinate
from flow_preprocessor.utils.logging.preprocessing_logger import logger


# ===============================================================================
# CLASS
# ===============================================================================
class ImageProcessor:
    """
    Process images from Transkribus and eScriptorium to extract text lines.
    """

    def __init__(self) -> None:
        """
        Initialize class parameters.

        :param: self.failed_processing: images which could not be processed.
        :param: self.too_short: images which are too short to be processed.
        :param: self.logger: the logger instance.
        """
        self.failed_processing: List[str] = []
        self.too_short: List[str] = []

    @staticmethod
    def _correct_orientation(image):
        try:
            exif = image.getexif()

            if exif:
                # key 274 = orientation, returns 1 if not existing
                orientation = exif.get(274, 1)

                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
            return image
        except (AttributeError, KeyError, IndexError):
            return image

    def _load_image(self, image_path: str) -> Image:
        """
        Load image.

        :param: the path of the image to be loaded.
        :return: the loaded image as a PILImage.
        """
        image = Image.open(image_path)
        image = self._correct_orientation(image)

        return image

    def extract_line_from_image(self,
                                baseline_points: List[Coordinate],
                                coordinates: List[Coordinate],
                                in_path: Union[str, bytes],
                                line_number: str,
                                min_width: float = None) -> Image:
        """
        Extract line from image in bounding box.

        :param baseline_points: the baseline coordinates.
        :param coordinates: the coordinates of the line.
        :param in_path: the input path of the images to be processed.
        :param line_number: the line number of the line to be processed.
        :param min_width: the minimum width of the lines to be processed.
        :return: Line as PILImage object.
        """
        try:
            logger.debug(
                '%s - baseline_points: %s',
                self.__class__.__name__,
                baseline_points,
            )

            if min_width and Coordinate.get_width(baseline_points) < min_width:
                logger.warning(
                    '%s - The line %s in %s is too short (width: %s)',
                    self.__class__.__name__,
                    line_number,
                    in_path,
                    Coordinate.get_width(baseline_points),
                )
                self.too_short.append(in_path)
                self.failed_processing.append(in_path)
                raise ImageProcessException(f'Line to short: {line_number} in {in_path}')

            img = self._load_image(in_path)
            image_line = img.crop(Coordinate.get_bbox(baseline_points + coordinates))
            img.close()
            logger.info(
                '%s - Successfully extracted line %s for image %s',
                self.__class__.__name__,
                line_number,
                in_path,
            )
            return image_line
        except FileNotFoundError as e:
            logger.error(
                '%s - File not found: %s, %s',
                self.__class__.__name__,
                in_path,
                e,
            )
            self.failed_processing.append(in_path)
            raise ImageProcessException(f'File not found: {in_path} {e}') from e
        except PIL.UnidentifiedImageError as e:
            logger.error(
                '%s - The image cannot be opened and identified for file %s, %s',
                self.__class__.__name__,
                in_path,
                e,
            )
            self.failed_processing.append(in_path)
            raise ImageProcessException(f'The image cannot be opened and identified for file {in_path}, {e}') from e
        except ValueError as e:
            logger.error(
                '%s - Wrong value provided for file %s on line %s, %s',
                self.__class__.__name__,
                in_path,
                line_number,
                e,
            )
            self.failed_processing.append(in_path)
            raise ImageProcessException(f'Wrong value provided for file {in_path}, {e}') from e
        except TypeError as e:
            logger.error(
                '%s - Wrong type provided for file %s, %s',
                self.__class__.__name__,
                in_path,
                e,
            )
            self.failed_processing.append(in_path)
            raise ImageProcessException(f'Wrong type provided for file {in_path}, {e}') from e
        except Exception as e:
            logger.error(
                '%s - Unknown error occurred for file %s, %s',
                self.__class__.__name__,
                in_path,
                e,
            )
            self.failed_processing.append(in_path)
            raise ImageProcessException(f'Unknown error occurred for file {in_path}, {e}') from e

    def crop_line_from_image(self,
                             coordinates: List[Tuple[float, float]],
                             image_path: Union[str, bytes],
                             line_number: str) -> Image:
        """
        Crop the line from the image by drawing polygon mask.

        :param coordinates: the coordinates of the line.
        :param image_path: the input path of the images to be processed.
        :param line_number: the line number of the line to be processed.
        :return: Line as PILImage object.
        """
        try:
            img = self._load_image(image_path)
            new_image = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(new_image)
            draw.polygon(coordinates, fill=(0, 0, 0, 255))

            # Create a mask image with the polygon filled in white
            mask = Image.new('L', img.size)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.polygon(coordinates, fill=255)

            # Apply the mask to the original image to cut out the polygon
            new_image.paste(img, (0, 0), mask=mask)

            # Crop the cutout image to the bounding box of the polygon
            bbox = new_image.getbbox()
            cutout = new_image.crop(bbox)

            cropped_image = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
            cropped_image.paste(cutout, (0, 0), mask=cutout)
            cropped_image = cropped_image.convert('RGB')
            logger.info(
                '%s - Successfully extracted line %s for image %s',
                self.__class__.__name__,
                line_number,
                image_path,
            )
            new_image.close()
            img.close()
            return cropped_image
        except FileNotFoundError as e:
            logger.error('%s - File not found: %s', self.__class__.__name__, image_path, exc_info=True)
            self.failed_processing.append(image_path)
            raise ImageProcessException(f'File not found:{image_path}, {e}') from e
        except PIL.UnidentifiedImageError as e:
            logger.error(
                '%s - The image cannot be opened and identified for file %s',
                self.__class__.__name__,
                image_path,
                exc_info=True,
            )
            self.failed_processing.append(image_path)
            raise ImageProcessException(f'The image cannot be opened and identified for file {image_path}, {e}') from e
        except ValueError as e:
            logger.error(
                '%s - Wrong value provided for file %s',
                self.__class__.__name__,
                image_path,
                exc_info=True,
            )
            self.failed_processing.append(image_path)
            raise ImageProcessException(f'Wrong value provided for file {image_path}, {e}') from e
        except TypeError as e:
            logger.error(
                '%s - Wrong type provided for file %s',
                self.__class__.__name__,
                image_path,
                exc_info=True,
            )
            self.failed_processing.append(image_path)
            raise ImageProcessException(f'Wrong type provided for file {image_path}, {e}') from e
