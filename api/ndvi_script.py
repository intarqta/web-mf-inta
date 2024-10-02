import ee
import json
from google.oauth2 import service_account
import os
# Cargar las credenciales desde una variable de entorno
key_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']  # Establece esta variable en Render

# Inicializa Earth Engine
credentials = service_account.Credentials.from_service_account_info(key_file, scopes=oauth.SCOPES)
ee.Initialize(credentials)

def get_ndvi(polygon):
    # ee.Authenticate()
    # ee.Initialize(project="proyec2020")
    
    # Define the time range
    start_date = '2024-01-01'
    end_date = '2024-09-30'

    # Load the MODIS NDVI dataset
    dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterDate(start_date, end_date) \
        .filterBounds(ee.Geometry.Polygon(polygon['coordinates'][0])) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE","less_than",10)
    def NDVI(img):
        ndvi = img.normalizedDifference(["B8","B4"]).rename("NDVI")
        return img.addBands(ndvi).clip(ee.Geometry.Polygon(polygon['coordinates'][0]))

    # Calculate NDVI
    ndvi = dataset.map(NDVI).select('NDVI')

    # Obtener las fechas de las imágenes
    def get_image_dates(image):
        return image.set ('fecha', image.date().format())

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
            geometry= ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=30,  # Cambia la escala según la resolución deseada
            maxPixels=1e9
        )
        
        return mean_ndvi_roi.set('date', date)

    # Mapear la función sobre la lista de fechas
    daily_ndvi_collection = ee.List(dates_list.map(get_average_ndvi))

    # Obtener los resultados como una lista
    results = daily_ndvi_collection.getInfo()

    # Formatear los resultados como JSON
    json_results = [{"fecha": item['date'], "NDVI": item['mean_NDVI']} for item in results]

    # Convertir a JSON
    json_output = json.dumps(json_results, indent=4)

    # Devilver la serie temporal de ndvi
    return json_output
