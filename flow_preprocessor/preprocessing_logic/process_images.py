# ===============================================================================
# IMPORT STATEMENTS
# ===============================================================================
from typing import List, Tuple, Union

import PIL
from PIL import Image, ImageDraw

from flow_preprocessor.exceptions.exceptions import ImageProcessException
from flow_preprocessor.preprocessing_logic.parse_textlines import Coordinate
from flow_preprocessor.utils.logging.logger import Logger


# ===============================================================================
# CLASS
# ===============================================================================
class ImageProcessor:
    """
    Process images from Transkribus and eScriptorium to extract text lines.
    """

    def __init__(self, process_id: str) -> None:
        """
        Initialize class parameters.

        :param: self.failed_processing: images which could not be processed.
        :arg: self.process_id: the unique identifier of the process.
        :param: self.logger: the logger instance.
        """
        self.failed_processing: List[str] = []
        self.logger = Logger(log_file=f'logs/{process_id}_process_images.log').get_logger()

    @staticmethod
    def _load_image(image_path: str) -> Image:
        """
        Load image.

        :param: the path of the image to be loaded.
        :return: the loaded image as a PILImage.
        """
        with Image.open(image_path) as image:
            image.load()
            return image

    def extract_line_from_image(self,
                                baseline_points: List[Coordinate],
                                coordinates: List[Coordinate],
                                in_path: Union[str, bytes],
                                line_number: str) -> Image:
        """
        Extract line from image in bounding box.

        :param baseline_points: the baseline coordinates.
        :param coordinates: the coordinates of the line.
        :param in_path: the input path of the images to be processed.
        :param line_number: the line number of the line to be processed.
        :return: Line as PILImage object.
        """
        try:
            y_max_base = Coordinate.max_y(baseline_points)
            x_min_coord = Coordinate.min_x(coordinates)
            x_max_coord = Coordinate.max_x(coordinates)
            y_min_coord = Coordinate.min_y(coordinates)
            y_max_coord = Coordinate.max_y(coordinates)

            # only use baseline y_max if it is lower than the y_min of the region
            if y_max_base > y_min_coord:
                y_max_coord = (y_max_base + y_max_coord) / 2

            img = self._load_image(in_path)
            image_line = img.crop((x_min_coord, y_min_coord, x_max_coord, y_max_coord))
            self.logger.info(f'{self.__class__.__name__} - Successfully extracted line {line_number} for image {in_path}')
            return image_line
        except FileNotFoundError as e:
            self.logger.error(f'{self.__class__.__name__} - File not found: {in_path}, {str(e)}')
            self.failed_processing.append(in_path)
            raise ImageProcessException('File not found: %s %s:', in_path, e)
        except PIL.UnidentifiedImageError as e:
            self.logger.error(f'{self.__class__.__name__} - The image cannot be opened and identified for file {in_path}, {str(e)}')
            self.failed_processing.append(in_path)
            raise ImageProcessException('The image cannot be opened and identified for file %s %s', in_path, e)
        except ValueError as e:
            self.logger.error(f'{self.__class__.__name__} - Wrong value provided for file {in_path} on line {line_number}, {str(e)}')
            self.failed_processing.append(in_path)
            raise ImageProcessException('Wrong value provided for file %s %s', in_path, str(e))
        except TypeError as e:
            self.logger.error(f'{self.__class__.__name__} - Wrong type provided for file {in_path}, {str(e)}')
            self.failed_processing.append(in_path)
            raise ImageProcessException('Wrong type provided for file %s %s', in_path, str(e))

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
            mask = Image.new('L', img.size, 0)
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
            self.logger.info(
                f'{self.__class__.__name__} - Successfully extracted line {line_number} for image {image_path}'
            )
            return cropped_image
        except FileNotFoundError as e:
            self.logger.error(f'{self.__class__.__name__} - File not found: {image_path}',  exc_info=True)
            self.failed_processing.append(image_path)
            raise ImageProcessException('File not found: %s %s:', image_path, e)
        except PIL.UnidentifiedImageError as e:
            self.logger.error(
                f'{self.__class__.__name__} - The image cannot be opened and identified for file {image_path}',
                exc_info=True,
            )
            self.failed_processing.append(image_path)
            raise ImageProcessException('The image cannot be opened and identified for file %s %s', image_path, e)
        except ValueError as e:
            self.logger.error(
                f'{self.__class__.__name__} - Wrong value provided for file {image_path}',
                exc_info=True,
            )
            self.failed_processing.append(image_path)
            raise ImageProcessException('Wrong value provided for file %s %s', image_path, str(e))
        except TypeError as e:
            self.logger.error(
                f'{self.__class__.__name__} - Wrong type provided for file {image_path}',
                exc_info=True,
            )
            self.failed_processing.append(image_path)
            raise ImageProcessException('Wrong type provided for file %s %s', image_path, str(e))

    def get_failed_processing(self) -> List[str]:
        """
        Retrieve the names of the XML files which failed during download.

        return: List of names of the XML files which could not be processed.
        """
        return self.failed_processing
