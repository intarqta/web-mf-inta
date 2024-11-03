from rest_framework import viewsets
from rest_framework.views import APIView
from .serializer import TaskSerializer, PolygonSerializer
from .models import Task
from rest_framework.response import Response
from rest_framework import status
from .ndvi_script import get_ndvi
import geojson

# Con una sola clase podemos generar el CRUD de forma automática
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

            # Obtener parámetros adicionales desde el request
            start_date = request.data.get('start_date', '2024-01-01')
            end_date = request.data.get('end_date', '2024-09-30')
            recurso_forrajero = request.data.get('recurso_forrajero', None)
            presencia_leñosas = request.data.get('presencia_leñosas', False)
            porcentaje_leñosas = request.data.get('porcentaje_leñosas', 0)

            # Asegúrate de convertir 'presencia_leñosas' a booleano si viene como string
            if isinstance(presencia_leñosas, str):
                presencia_leñosas = presencia_leñosas.lower() == 'true'

            # Llamar a la función get_ndvi con los nuevos parámetros
            ndvi_data = get_ndvi(
                polygon=polygon,
                start_date=start_date,
                end_date=end_date,
                recurso_forrajero=recurso_forrajero,
                presencia_leñosas=presencia_leñosas,
                porcentaje_leñosas=porcentaje_leñosas
            )

            # Responder con los datos NDVI generados
            return Response(ndvi_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
