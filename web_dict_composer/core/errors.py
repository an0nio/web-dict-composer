class ComposerError(Exception):
    """Base error with a message suitable for CLI users."""


class ProfileError(ComposerError):
    """Raised when a profile is missing or invalid."""


class SafetyLimitError(ComposerError):
    """Raised before a build that exceeds its declared safety limit."""


class SourceError(ComposerError):
    """Raised for invalid dictionary source operations."""
