"""
Módulo de Extracción (Bronze Layer).
"""
from tasks.extract.extract_oltp_pedidos import extract_oltp_pedidos
from tasks.extract.extract_oltp_users import extract_oltp_users
from tasks.extract.extract_randomuser import extract_randomuser

__all__ = [
    "extract_oltp_pedidos",
    "extract_oltp_users",
    "extract_randomuser",
]
