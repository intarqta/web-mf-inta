from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id','title','description','done')
        # una opción para colocar todos los campos es fields = '__all__'

class PolygonSerializer(serializers.Serializer):
    coordinates = serializers.ListField(child=serializers.ListField(child=serializers.ListField(child=serializers.FloatField())))
    