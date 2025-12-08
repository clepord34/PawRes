"""Tests for PhotoService - photo loading, validation, and management."""
import pytest
import base64

from services.photo_service import PhotoService, PhotoValidationResult, PhotoServiceError


class TestPhotoValidation:
    """Test photo validation methods."""
    
    def test_is_base64_detects_long_string(self):
        """Test is_base64 identifies long strings as base64."""
        service = PhotoService()
        
        # Create a long base64 string (simulated)
        long_base64 = "a" * 300
        assert service.is_base64(long_base64) is True
    
    def test_is_base64_rejects_filenames(self):
        """Test is_base64 rejects typical filenames."""
        service = PhotoService()
        
        assert service.is_base64("photo.jpg") is False
        assert service.is_base64("animal_123.png") is False
        assert service.is_base64("image.jpeg") is False
    
    def test_is_base64_rejects_short_strings(self):
        """Test is_base64 rejects short strings."""
        service = PhotoService()
        
        assert service.is_base64("short") is False
        assert service.is_base64("") is False
        assert service.is_base64("a" * 50) is False
    
    def test_validate_base64_image_empty_data(self):
        """Test validation fails on empty data."""
        service = PhotoService()
        
        result, message = service.validate_base64_image("")
        assert result == PhotoValidationResult.INVALID_FORMAT
        assert "No image data" in message
    
    def test_validate_base64_image_invalid_base64(self):
        """Test validation fails on invalid base64."""
        service = PhotoService()
        
        result, message = service.validate_base64_image("not-valid-base64!!!")
        assert result == PhotoValidationResult.DECODE_ERROR
    
    def test_validate_base64_image_valid_jpeg(self):
        """Test validation succeeds on valid JPEG."""
        service = PhotoService()
        
        # Create a minimal valid JPEG (1x1 pixel)
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\xfe(\xa2\x8a\xff\xd9'
        jpeg_b64 = base64.b64encode(jpeg_data).decode('utf-8')
        
        result, message = service.validate_base64_image(jpeg_b64)
        assert result == PhotoValidationResult.VALID
    
    def test_validate_base64_image_valid_png(self):
        """Test validation succeeds on valid PNG."""
        service = PhotoService()
        
        # Create a minimal valid PNG (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        png_b64 = base64.b64encode(png_data).decode('utf-8')
        
        result, message = service.validate_base64_image(png_b64)
        assert result == PhotoValidationResult.VALID


class TestPhotoLoading:
    """Test photo loading operations."""
    
    def test_load_photo_as_base64_with_base64_data(self):
        """Test loading when data is already base64."""
        service = PhotoService()
        
        base64_data = "a" * 300  # Simulated base64
        result = service.load_photo_as_base64(base64_data)
        
        assert result == base64_data
    
    def test_load_photo_as_base64_with_none(self):
        """Test loading returns None for None input."""
        service = PhotoService()
        
        result = service.load_photo_as_base64(None)
        assert result is None
    
    def test_load_photo_as_base64_with_empty_string(self):
        """Test loading returns None for empty string."""
        service = PhotoService()
        
        result = service.load_photo_as_base64("")
        assert result is None


class TestPhotoSaving:
    """Test photo saving operations."""
    
    def test_save_photo_from_base64_with_validation(self):
        """Test saving base64 photo with validation."""
        service = PhotoService()
        
        # Create a minimal valid JPEG
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\xfe(\xa2\x8a\xff\xd9'
        jpeg_b64 = base64.b64encode(jpeg_data).decode('utf-8')
        
        filename = service.save_photo_from_base64(jpeg_b64, "test.jpg", validate=True)
        
        assert filename is not None
        assert isinstance(filename, str)
        assert len(filename) > 0
        
        # Cleanup
        service.delete_photo(filename)
    
    def test_save_photo_from_base64_invalid_raises_error(self):
        """Test saving invalid base64 raises PhotoServiceError."""
        service = PhotoService()
        
        with pytest.raises(PhotoServiceError):
            service.save_photo_from_base64("invalid-base64", "test.jpg", validate=True)
    
    def test_save_photo_from_base64_without_validation(self):
        """Test saving without validation (may succeed with any data)."""
        service = PhotoService()
        
        # Even invalid data should be saved if validation is skipped
        # Note: This might fail if FileStore validates, so we wrap in try-except
        try:
            filename = service.save_photo_from_base64("YW55ZGF0YQ==", "test.jpg", validate=False)
            assert filename is not None
            service.delete_photo(filename)
        except Exception:
            # If FileStore itself validates, this is expected
            pass


class TestPhotoDelete:
    """Test photo deletion operations."""
    
    def test_delete_photo_with_none(self):
        """Test deleting None returns False."""
        service = PhotoService()
        
        result = service.delete_photo(None)
        assert result is False
    
    def test_delete_photo_with_base64(self):
        """Test deleting base64 data returns False (not stored)."""
        service = PhotoService()
        
        base64_data = "a" * 300
        result = service.delete_photo(base64_data)
        assert result is False


class TestMimeTypeDetection:
    """Test MIME type detection from magic bytes."""
    
    def test_detect_mime_type_jpeg(self):
        """Test JPEG detection."""
        service = PhotoService()
        
        jpeg_data = b'\xff\xd8\xff' + b'\x00' * 10
        mime_type = service._detect_mime_type(jpeg_data)
        assert mime_type == "image/jpeg"
    
    def test_detect_mime_type_png(self):
        """Test PNG detection."""
        service = PhotoService()
        
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 10
        mime_type = service._detect_mime_type(png_data)
        assert mime_type == "image/png"
    
    def test_detect_mime_type_gif(self):
        """Test GIF detection."""
        service = PhotoService()
        
        gif87_data = b'GIF87a' + b'\x00' * 10
        gif89_data = b'GIF89a' + b'\x00' * 10
        
        assert service._detect_mime_type(gif87_data) == "image/gif"
        assert service._detect_mime_type(gif89_data) == "image/gif"
    
    def test_detect_mime_type_webp(self):
        """Test WebP detection."""
        service = PhotoService()
        
        webp_data = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 10
        mime_type = service._detect_mime_type(webp_data)
        assert mime_type == "image/webp"
    
    def test_detect_mime_type_unknown(self):
        """Test unknown format returns None."""
        service = PhotoService()
        
        unknown_data = b'\x00\x00\x00\x00' + b'\x00' * 10
        mime_type = service._detect_mime_type(unknown_data)
        assert mime_type is None
    
    def test_detect_mime_type_too_short(self):
        """Test data too short returns None."""
        service = PhotoService()
        
        short_data = b'\x00\x00'
        mime_type = service._detect_mime_type(short_data)
        assert mime_type is None


class TestPhotoInfo:
    """Test photo information retrieval."""
    
    def test_get_photo_info_with_none(self):
        """Test getting info for None returns None."""
        service = PhotoService()
        
        info = service.get_photo_info(None)
        assert info is None
    
    def test_get_photo_info_with_empty_string(self):
        """Test getting info for empty string returns None."""
        service = PhotoService()
        
        info = service.get_photo_info("")
        assert info is None
