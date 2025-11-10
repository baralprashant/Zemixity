"""
File upload security module
Validates file uploads to prevent malicious files
"""

import os
import re
import hashlib
from typing import Tuple, Optional

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️  python-magic not installed. File content validation will be limited.")


class FileValidator:
    """Validates uploaded files for security"""

    # Allowed MIME types
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp']
    }

    ALLOWED_DOCUMENT_TYPES = {
        'application/pdf': ['.pdf']
    }

    ALL_ALLOWED_TYPES = {**ALLOWED_IMAGE_TYPES, **ALLOWED_DOCUMENT_TYPES}

    # Maximum file sizes (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DOCUMENT_SIZE = 25 * 1024 * 1024  # 25MB

    def __init__(self):
        self.mime = magic.Magic(mime=True) if MAGIC_AVAILABLE else None

    def validate_file(
        self,
        file_content: bytes,
        filename: str,
        declared_mime_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file upload

        Args:
            file_content: File content bytes
            filename: Original filename
            declared_mime_type: MIME type declared by client

        Returns:
            Tuple of (is_valid, error_message)
        """
        # 1. Check if MIME type is allowed
        if declared_mime_type not in self.ALL_ALLOWED_TYPES:
            return False, f"File type '{declared_mime_type}' is not allowed"

        # 2. Validate file size
        file_size = len(file_content)

        if declared_mime_type in self.ALLOWED_IMAGE_TYPES:
            if file_size > self.MAX_IMAGE_SIZE:
                return False, f"Image too large. Maximum size is {self.MAX_IMAGE_SIZE // (1024*1024)}MB"
        elif declared_mime_type in self.ALLOWED_DOCUMENT_TYPES:
            if file_size > self.MAX_DOCUMENT_SIZE:
                return False, f"Document too large. Maximum size is {self.MAX_DOCUMENT_SIZE // (1024*1024)}MB"

        # 3. Validate file extension matches MIME type
        file_ext = os.path.splitext(filename.lower())[1]
        allowed_extensions = self.ALL_ALLOWED_TYPES.get(declared_mime_type, [])

        if file_ext not in allowed_extensions:
            return False, f"File extension '{file_ext}' does not match declared type '{declared_mime_type}'"

        # 4. Verify actual file content matches declared MIME type (using magic numbers)
        if MAGIC_AVAILABLE and self.mime:
            try:
                actual_mime_type = self.mime.from_buffer(file_content)

                # Some MIME types have variants (e.g., image/jpeg can be detected as image/jpg)
                if not self._mime_types_match(actual_mime_type, declared_mime_type):
                    return False, f"File content type '{actual_mime_type}' does not match declared type '{declared_mime_type}'. Possible malicious file."
            except Exception as e:
                print(f"⚠️  Could not verify file content: {e}")
                # If magic check fails, we can still allow the file if other checks passed
                # But log this for monitoring

        # 5. Check for suspicious content in PDFs (basic check)
        if declared_mime_type == 'application/pdf':
            if not self._validate_pdf_content(file_content):
                return False, "PDF file contains suspicious content"

        return True, None

    def _mime_types_match(self, actual: str, declared: str) -> bool:
        """Check if MIME types match (accounting for variants)"""
        # Exact match
        if actual == declared:
            return True

        # Handle common variants
        variants = {
            'image/jpeg': ['image/jpg', 'image/pjpeg'],
            'image/png': ['image/x-png'],
            'application/pdf': ['application/x-pdf']
        }

        declared_variants = variants.get(declared, [])
        return actual in declared_variants or actual == declared

    def _validate_pdf_content(self, content: bytes) -> bool:
        """Basic PDF validation - check for PDF header and no executable code"""
        # Check PDF header
        if not content.startswith(b'%PDF-'):
            return False

        # Check for suspicious patterns that might indicate embedded malware
        # This is a basic check - for production, use a proper PDF parser
        suspicious_patterns = [
            b'/JavaScript',  # Embedded JavaScript
            b'/JS',          # JavaScript short form
            b'/Launch',      # Launch action
            b'/EmbeddedFile' # Embedded files
        ]

        # Allow embedded files but log a warning
        for pattern in suspicious_patterns[:3]:  # Check first 3 (JS and Launch)
            if pattern in content:
                print(f"⚠️  PDF contains potentially unsafe content: {pattern.decode('latin-1')}")
                # For now, we block these. In production, you might want to:
                # - Use a PDF sanitizer
                # - Scan with antivirus
                # - Extract and analyze in sandbox
                return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Get just the filename (no path)
        filename = os.path.basename(filename)

        # Remove any non-alphanumeric characters except . - _
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Remove leading dots (hidden files)
        filename = filename.lstrip('.')

        # Ensure filename is not empty
        if not filename or filename == '_':
            filename = 'upload'

        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext

        return filename

    @staticmethod
    def generate_safe_filename(original_filename: str, file_content: bytes) -> str:
        """
        Generate a safe, unique filename based on content hash

        Args:
            original_filename: Original filename
            file_content: File content

        Returns:
            Safe unique filename
        """
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        # Generate content hash
        content_hash = hashlib.sha256(file_content).hexdigest()[:16]

        # Create safe filename
        return f"{content_hash}{ext}"


def validate_uploaded_file(
    file_content: bytes,
    filename: str,
    mime_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate an uploaded file

    Args:
        file_content: File content bytes
        filename: Original filename
        mime_type: Declared MIME type

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = FileValidator()
    return validator.validate_file(file_content, filename, mime_type)
