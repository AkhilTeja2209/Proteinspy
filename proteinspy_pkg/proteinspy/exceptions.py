"""
Custom exceptions for Proteinspy.

All library-specific errors inherit from ProteinsyError so callers
can catch the whole family with a single except clause.
"""


class ProteinsyError(Exception):
    """Base exception for all Proteinspy errors."""


class FileNotFoundError(ProteinsyError):
    """Raised when the requested structure file does not exist."""


class InvalidFileFormatError(ProteinsyError):
    """Raised when a file cannot be parsed as a supported structure format."""


class AnalysisError(ProteinsyError):
    """Raised when an analysis step fails unexpectedly."""


class ExportError(ProteinsyError):
    """Raised when writing output to disk or serialising results fails."""
