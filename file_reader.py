import os
from typing import Iterable


class FileReader:
    """Class for validating file paths and reading files in binary chunks"""
    CHUNK_SIZE = 4096

    @staticmethod
    def validate(file_path: str):
        """Validate that the path exists and points to a regular file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist")
        if not os.path.isfile(file_path):
            raise ValueError(f"{file_path} is not a file")

    @staticmethod
    def chunks(file_path: str, chunk_size: int = None, full_file: bool = False) -> Iterable[bytes]:
        """
        Yield file content in binary chunks.

        Validates the file before reading. Uses CHUNK_SIZE unless an
        explicit chunk size is provided.If full_file is True, reads
        entire file as single chunk.

        Args:
            file_path (str):
                Path to the file that should be read.
            chunk_size (int, optional):
                Size of each chunk in bytes. If not provided, the default
                `FileReader.CHUNK_SIZE` is used.
            full_file (bool, optional):
                If True, read entire file as single chunk (default: False)
        """

        FileReader.validate(file_path)

        with open(file_path, "rb") as f:
            if full_file:
                # Read entire file as single chunk
                data = f.read()
                if data:
                    yield data
            else:
                # Read file in chunks
                if chunk_size is None:
                    chunk_size = FileReader.CHUNK_SIZE

                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
