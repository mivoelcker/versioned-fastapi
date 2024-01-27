"""Versioned FastAPI simplifies the versioning of FastAPI web applications."""

__version__ = "1.0.0"


from .version_fastapi import FastApiVersioner, version

__all__ = ("FastApiVersioner", "version")
