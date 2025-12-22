from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from file_manager.models import File
from .serializers import FileSerializer

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

import mimetypes

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.select_related('folder')
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        folder_id = self.request.query_params.get('folder')
        qs = super().get_queryset()
        if folder_id:
            qs = qs.filter(folder_id=folder_id)
        return qs

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        folder_id = request.data.get('folder')

        if not uploaded_file:
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_file.size > MAX_UPLOAD_SIZE:
            return Response(
                {"error": "Max file size 50MB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = File.objects.create(
            folder_id=folder_id,
            file=uploaded_file,
            original_name=uploaded_file.name,
            size=uploaded_file.size,
            mime_type=mimetypes.guess_type(uploaded_file.name)[0],
            uploaded_by=request.user
        )

        serializer = self.get_serializer(file_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
