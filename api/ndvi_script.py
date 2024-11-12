import ee
import json
from google.oauth2 import service_account
import os
import requests
from datetime import datetime

def initialize_earth_engine():
    service_account = 'api-monitoreo-forrajero@proyec2020.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account, '/etc/secrets/GOOGLE_APPLICATION_CREDENTIALS')
    ee.Initialize(credentials)

# Función para calcular el centroide del polígono
def calculate_centroid(polygon):
    # Inicializar GEE
    initialize_earth_engine()
    
    ee_polygon = ee.Geometry.Polygon(polygon['coordinates'][0])
    centroid = ee_polygon.centroid().coordinates().getInfo()
    return centroid  # [longitude, latitude]

# Función para obtener datos de NASA POWER
def get_nasa_power_data(centroid, start_date, end_date):
    longitud, latitud = centroid
    print('lobgitud', longitud)
    print('latitud', latitud)
    
    # Configuración de la URL de la API de NASA POWER
    # url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    # params = {
    #     "start": start_date.replace('-', ''),
    #     "end": end_date.replace('-', ''),
    #     "latitude": lat,
    #     "longitude": lon,
    #     "community": "AG",
    #     "parameters": "T2M,RADAVG",  # Temperatura a 2m y Radiación media
    #     "format": "JSON",
    #     "header": "false",
    #     "timeStandard": "UTC"
    # }
    
    # longitud = -58.364378424319945
    # latitud = -32.50141643265047
    iniAAAAMMDD = start_date.replace('-', '')
    finAAAAMMDD = end_date.replace('-', '')

    base_url = r"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_PAR_TOT,T2M&community=RE&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON"

    api_request_url = base_url.format(longitude=longitud, latitude=latitud, start=iniAAAAMMDD, end=finAAAAMMDD)
    response = requests.get(url=api_request_url, verify=True, timeout=30.00)
    # content = json.loads(response.content.decode('utf-8'))
    # Convertir a una lista de diccionarios para facilitar el manejo
    
    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.json()
        daily_data = data.get("properties", {}).get("parameter", {})
        temperature_data = daily_data.get("T2M", {})
        radiation_data = daily_data.get("ALLSKY_SFC_PAR_TOT", {})

       
        results_rad = []
        for date in temperature_data.keys():
            results_rad.append({
                "fecha": datetime.strptime(date, "%Y%m%d").date(),
                "temperatura": temperature_data[date],
                "radiacion": radiation_data.get(date, None)  # Algunos días podrían no tener valores
            })
            if 'radiacion' in results_rad and results_rad['radiacion'] < 0:
                    results_rad['radiacion'] = None
        return results_rad
    else:
        # Si la solicitud falla, se imprime el error
        print(f"Error en la solicitud de NASA POWER: {response.status_code}")
        return []

# Función principal para obtener NDVI y datos de NASA POWER
def get_ndvi(polygon, start_date='2024-01-01', end_date='2024-09-30', recurso_forrajero=None, presencia_leñosas=False, porcentaje_leñosas=0):
    ee.Authenticate()
    ee.Initialize(project="proyec2020")
    
    # Definir rango de fechas a partir de los parámetros
    # Load the MODIS NDVI dataset
    dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterDate(start_date, end_date) \
        .filterBounds(ee.Geometry.Polygon(polygon['coordinates'][0])) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 10)

    def NDVI(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi).clip(ee.Geometry.Polygon(polygon['coordinates'][0]))

    # Calculate NDVI
    ndvi = dataset.map(NDVI).select('NDVI')

    # Obtener las fechas de las imágenes
    def get_image_dates(image):
        return image.set('fecha', image.date().format())

    # Mapear la función sobre la colección de imágenes
    dates_list = ndvi.map(get_image_dates).aggregate_array('fecha')

    # Agrupar por fecha y calcular el promedio del NDVI
    def get_average_ndvi(date):
        daily_ndvi = ndvi.filterDate(date, ee.Date(date).advance(1, 'day')) \
                                    .select('NDVI')
        mean_ndvi = daily_ndvi.mean().rename('mean_NDVI')
        
        # Calcular el NDVI promedio para la ROI
        mean_ndvi_roi = mean_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=30,  # Cambia la escala según la resolución deseada
            maxPixels=1e9
        )
        
        return mean_ndvi_roi.set('date', date)

    # Mapear la función sobre la lista de fechas
    daily_ndvi_collection = ee.List(dates_list.map(get_average_ndvi))

    # Obtener los resultados como una lista
    results = daily_ndvi_collection.getInfo()

    # Formatear los resultados como JSON
    json_results = []
    for item in results:
        result_item = {
            "fecha": item['date'],
            "NDVI": item.get('mean_NDVI', None)  # Asegurarse de que el valor esté presente
        }

        # Añadir información adicional basada en los parámetros del recurso
        result_item.update({
            "recurso_forrajero": recurso_forrajero,
            "presencia_leñosas": presencia_leñosas,
            "porcentaje_leñosas": porcentaje_leñosas if presencia_leñosas else 0
        })

        json_results.append(result_item)

    # Calcular el centroide del polígono
    centroid = calculate_centroid(polygon)

    # Obtener datos de NASA POWER
    nasa_power_results = get_nasa_power_data(centroid, start_date, end_date)


    # Combinar los resultados de NDVI y NASA POWER
    combined_results = {
        "ndvi_data": json_results,
        "nasa_power_data": nasa_power_results
    }

    # Convertir a JSON
    json_output = json.dumps(combined_results, indent=4)

    # Devolver la serie temporal de ndvi y los datos de NASA POWER
    return json_output
