"""Vercel loads this file. The editor itself lives in cardmaker.wsgi."""

from cardmaker.wsgi import app

__all__ = ["app"]
