from rest_framework import serializers

class EmptySerializer(serializers.Serializer):
    pass

class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()