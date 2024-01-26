"""Versioned FastAPI simplifies the versioning of FastAPI web applications."""

__version__ = "0.0.1"


from .version_fastapi import FastApiVersioner, version

__all__ = ("FastApiVersioner", "version")
