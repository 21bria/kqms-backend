import os
from django.shortcuts import render
from django.conf import settings

def format_downloads(request):
    # Path ke folder format-upload
    folder_path = os.path.join(settings.BASE_DIR, 'static/format-upload')

    # List semua file dalam folder
    files = []
    for idx, filename in enumerate(os.listdir(folder_path), start=1):
        if filename.endswith('.xlsx'):  # Filter file dengan ekstensi .xlsx
            files.append({
                "no"   : idx,
                "name" : filename,
                "path" : f"format-upload/{filename}",
            })
    
     # Ambil permissions dinamis dari database
    context = {
        'files': files,
    }      

    return render(request, "task/template-excel.html", context)
