import json
from rest_framework import serializers

class SearchSerializer(serializers.Serializer):
    search_text = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    class Meta:
        fields=['search_text']
    
    def validate(self, search_text):
        if not search_text:
            return []
        return search_text