# utils/db_utils.py

from django.db import connections

def get_db_vendor(alias='kqms_db'):
    """
    Fungsi untuk mendapatkan nama vendor dari koneksi database berdasarkan alias yang diberikan.
    """
    try:
        # Mendapatkan koneksi ke database berdasarkan alias
        connection = connections[alias]
        
        # Mendapatkan vendor dari koneksi tersebut
        db_vendor = connection.vendor
        
        # Debugging: Pastikan vendor yang terdeteksi benar
        print(f"Database vendor: {db_vendor}")
        
        return db_vendor
    except KeyError:
        raise ValueError(f"Connection alias '{alias}' doesn't exist.")
