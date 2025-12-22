from rest_framework import serializers
from file_manager.models import Folder, File

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = [
            'id',
            'name',
            'parent',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'
        fields = [
            'id',
            'folder',
            'file',
            'original_name',
            'size',
            'mime_type',
            'uploaded_by',
            'uploaded_at',
        ]
        read_only_fields = [
            'original_name',
            'size',
            'mime_type',
            'uploaded_by',
            'uploaded_at',
        ]
