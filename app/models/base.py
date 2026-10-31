"""Utilitarios base para modelos de datos en MDG Cibersegura."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Devuelve la fecha y hora actual en zona horaria UTC con información de zona."""
    return datetime.now(timezone.utc)
