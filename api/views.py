from rest_framework import viewsets
from rest_framework.views import APIView
from .serializer import TaskSerializer, PolygonSerializer
from .models import Task
from rest_framework.response import Response
from rest_framework import status
import geojson
from .evaluate import get_ndvi_and_regions
from .ndvi_script import get_ndvi, calculate_centroid, get_nasa_power_data
import json


class NDVIAPIView(APIView):
    def post(self, request):
        # Asegúrate de que los datos se pasan correctamente
        serializer = PolygonSerializer(data=request.data)
        if serializer.is_valid():
            coordinates = serializer.validated_data['coordinates']
            polygon = geojson.Polygon([coordinates])
            start_date = request.data.get('start_date', '2024-01-01')
            end_date = request.data.get('end_date', '2024-09-30')
            
            # Llamar a la función get_ndvi para obtener los datos de NDVI
            ndvi_data = get_ndvi_and_regions(polygon)
            print(ndvi_data)

            # Calcular el centroide del polígono
            centroid = calculate_centroid(polygon)

            # Obtener datos de NASA POWER (temperatura y radiación)
            nasa_power_data = get_nasa_power_data(centroid, start_date, end_date)

            # Combinar los resultados de NDVI y NASA POWER
            combined_results = {
                "ndvi_data": ndvi_data,
                "nasa_power_data": nasa_power_data
            }

            return Response(combined_results, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
