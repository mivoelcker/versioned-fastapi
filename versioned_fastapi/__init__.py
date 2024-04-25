"""Versioned FastAPI simplifies the versioning of FastAPI web applications."""

__version__ = "1.0.2"


from .version_fastapi import FastApiVersioner, version

__all__ = ("FastApiVersioner", "version")
