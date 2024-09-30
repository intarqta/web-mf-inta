from rest_framework import viewsets
from rest_framework.views import APIView
from .serializer import TaskSerializer, PolygonSerializer
from .models import Task
from rest_framework.response import Response
from rest_framework import status
from .ndvi_script import get_ndvi
import geojson

# Con una sola clase podemos generar el CRUD de forma automatica 
class TaskView(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

class NDVIAPIView(APIView):
    def post(self, request):
        # Asegúrate de que los datos se pasan correctamente
        serializer = PolygonSerializer(data=request.data)
        if serializer.is_valid():
            coordinates = serializer.validated_data['coordinates']
            polygon = geojson.Polygon([coordinates])
            ndvi_data = get_ndvi(polygon)
            return Response(ndvi_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)