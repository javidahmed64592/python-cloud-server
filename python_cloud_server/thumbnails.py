"""Thumbnail generation for images and videos."""

import logging
from pathlib import Path

import cv2
from PIL import Image

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Generate thumbnails for images and videos."""

    def __init__(self, thumbnail_size: tuple[int, int] = (200, 200)) -> None:
        """Initialize thumbnail generator.

        :param tuple[int, int] thumbnail_size: Target thumbnail size (width, height)
        """
        self.thumbnail_size = thumbnail_size
        logger.info("Initialized ThumbnailGenerator with size: %s", thumbnail_size)

    def generate_image_thumbnail(self, image_path: Path, output_path: Path) -> bool:
        """Generate thumbnail for an image file.

        :param Path image_path: Path to source image
        :param Path output_path: Path to save thumbnail
        :return bool: True if successful, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with Image.open(image_path) as img:
                new_img = img.copy()
                if img.mode == "RGBA":
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    new_img = background
                elif img.mode != "RGB":
                    new_img = img.convert("RGB")

                new_img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                new_img.save(output_path, "JPEG", quality=85, optimize=True)

            logger.info("Generated image thumbnail: %s", output_path)
        except Exception:
            logger.exception("Failed to generate image thumbnail for %s", image_path)
            return False
        else:
            return True

    def generate_video_thumbnail(self, video_path: Path, output_path: Path) -> bool:
        """Generate thumbnail for a video file by extracting a frame.

        :param Path video_path: Path to source video
        :param Path output_path: Path to save thumbnail
        :return bool: True if successful, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            video = cv2.VideoCapture(str(video_path))

            if not video.isOpened():
                logger.error("Could not open video file: %s", video_path)
                return False

            fps = video.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                target_frame = int(fps * 1.0)  # 1 second
                video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

            success, frame = video.read()
            video.release()

            if not success or frame is None:
                logger.error("Could not read frame from video: %s", video_path)
                return False

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            img.save(output_path, "JPEG", quality=85, optimize=True)
            logger.info("Generated video thumbnail: %s", output_path)
        except Exception:
            logger.exception("Failed to generate video thumbnail for %s", video_path)
            return False
        else:
            return True

    def generate_thumbnail(self, file_path: Path, mime_type: str, output_path: Path) -> None:
        """Generate thumbnail based on MIME type.

        :param Path file_path: Path to source file
        :param str mime_type: MIME type of the file
        :param Path output_path: Path to save thumbnail
        """
        if mime_type.startswith("image/"):
            self.generate_image_thumbnail(file_path, output_path)
        if mime_type.startswith("video/"):
            self.generate_video_thumbnail(file_path, output_path)

        logger.debug("No thumbnail generator for MIME type: %s", mime_type)
