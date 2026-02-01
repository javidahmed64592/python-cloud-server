"""Unit tests for the thumbnail generator."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image

from python_cloud_server.thumbnails import ThumbnailGenerator


class TestImageThumbnailGeneration:
    """Unit tests for image thumbnail generation."""

    def test_generate_image_thumbnail(
        self, mock_thumbnail_generator: ThumbnailGenerator, mock_image_file: Path, tmp_path: Path
    ) -> None:
        """Test generating a thumbnail from an image."""
        output_path = tmp_path / "thumbnail.jpg"

        mock_thumbnail_generator.generate_image_thumbnail(mock_image_file, output_path)

        assert output_path.exists()
        # Verify thumbnail is a valid JPEG
        img = Image.open(output_path)
        assert img.format == "JPEG"
        assert img.size[0] <= mock_thumbnail_generator.thumbnail_size[0]
        assert img.size[1] <= mock_thumbnail_generator.thumbnail_size[1]

    def test_generate_image_thumbnail_rgba(self, mock_thumbnail_generator: ThumbnailGenerator, tmp_path: Path) -> None:
        """Test generating a thumbnail from an RGBA image (PNG with transparency)."""
        # Create RGBA image
        img = Image.new("RGBA", (400, 300), color=(255, 0, 0, 128))
        image_path = tmp_path / "test_rgba.png"
        img.save(image_path, "PNG")

        output_path = tmp_path / "thumbnail.jpg"
        mock_thumbnail_generator.generate_image_thumbnail(image_path, output_path)

        assert output_path.exists()
        # Verify RGBA was converted to RGB
        thumbnail = Image.open(output_path)
        assert thumbnail.format == "JPEG"
        assert thumbnail.mode == "RGB"

    def test_generate_image_thumbnail_nonexistent_file(
        self, mock_thumbnail_generator: ThumbnailGenerator, tmp_path: Path
    ) -> None:
        """Test that generating thumbnail from nonexistent file returns False."""
        nonexistent_file = tmp_path / "nonexistent.jpg"
        output_path = tmp_path / "thumbnail.jpg"

        result = mock_thumbnail_generator.generate_image_thumbnail(nonexistent_file, output_path)
        assert result is False
        assert not output_path.exists()


class TestThumbnailGeneration:
    """Unit tests for the main generate_thumbnail method."""

    def test_generate_thumbnail_image(
        self, mock_thumbnail_generator: ThumbnailGenerator, mock_image_file: Path, tmp_path: Path
    ) -> None:
        """Test generating thumbnail dispatches to image generator for image MIME types."""
        output_path = tmp_path / "thumbnail.jpg"

        mock_thumbnail_generator.generate_thumbnail(mock_image_file, "image/jpeg", output_path)

        assert output_path.exists()
        img = Image.open(output_path)
        assert img.format == "JPEG"

    def test_generate_thumbnail_video(
        self, mock_thumbnail_generator: ThumbnailGenerator, mock_video_file: Path, tmp_path: Path
    ) -> None:
        """Test generating thumbnail dispatches to video generator for video MIME types."""
        output_path = tmp_path / "thumbnail.jpg"

        # Mock cv2 to simulate successful video processing
        with patch("python_cloud_server.thumbnails.cv2") as mock_cv2:
            mock_video = MagicMock()
            mock_video.isOpened.return_value = True
            mock_video.get.return_value = 30.0  # 30 FPS
            # Create a fake frame (numpy array)
            fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            fake_frame[:, :] = [255, 0, 0]  # Red frame
            mock_video.read.return_value = (True, fake_frame)
            mock_cv2.VideoCapture.return_value = mock_video
            mock_cv2.cvtColor.return_value = fake_frame
            mock_cv2.CAP_PROP_FPS = 5
            mock_cv2.CAP_PROP_POS_FRAMES = 1
            mock_cv2.COLOR_BGR2RGB = 4

            mock_thumbnail_generator.generate_thumbnail(mock_video_file, "video/mp4", output_path)

            assert output_path.exists()
            img = Image.open(output_path)
            assert img.format == "JPEG"

    def test_generate_thumbnail_unsupported_type(
        self, mock_thumbnail_generator: ThumbnailGenerator, tmp_path: Path
    ) -> None:
        """Test that unsupported MIME type raises error."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("test content")
        output_path = tmp_path / "thumbnail.jpg"

        # No exception should be raised, but thumbnail won't be created
        mock_thumbnail_generator.generate_thumbnail(text_file, "text/plain", output_path)
        assert not output_path.exists()

    def test_generate_thumbnail_creates_parent_directory(
        self, mock_thumbnail_generator: ThumbnailGenerator, mock_image_file: Path, tmp_path: Path
    ) -> None:
        """Test that generate_thumbnail creates parent directories if they don't exist."""
        output_path = tmp_path / "nested" / "folder" / "thumbnail.jpg"

        mock_thumbnail_generator.generate_thumbnail(mock_image_file, "image/jpeg", output_path)

        assert output_path.exists()
        assert output_path.parent.exists()
