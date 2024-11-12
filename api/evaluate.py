import ee
import json
from google.oauth2 import service_account
import os
from pathlib import Path

def initialize_earth_engine():
    service_account = 'api-monitoreo-forrajero@proyec2020.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account, '/etc/secrets/GOOGLE_APPLICATION_CREDENTIALS')
    ee.Initialize(credentials)

# Función para calcular el centroide del polígono
def get_ndvi_and_regions(polygon):
    # Inicializar GEE
    initialize_earth_engine()
  
    # Define el rango de fechas
    start_date = '2024-01-01'
    end_date = '2024-09-30'

    # Cargar el dataset MODIS NDVI
    dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterDate(start_date, end_date) \
        .filterBounds(ee.Geometry.Polygon(polygon['coordinates'][0])) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 10)

    def NDVI(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi).clip(ee.Geometry.Polygon(polygon['coordinates'][0]))

    # Calcular NDVI
    ndvi = dataset.map(NDVI).select('NDVI')

    # Obtener las fechas de las imágenes
    def get_image_dates(image):
        return image.set('fecha', image.date().format())

    # Mapear la función sobre la colección de imágenes
    dates_list = ndvi.map(get_image_dates).aggregate_array('fecha')

    # Agrupar por fecha y calcular el promedio del NDVI
    def get_average_ndvi(date):
        daily_ndvi = ndvi.filterDate(date, ee.Date(date).advance(1, 'day')).select('NDVI')
        mean_ndvi = daily_ndvi.mean().rename('mean_NDVI')

        # Calcular el NDVI promedio para la región de interés (ROI)
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
    ndvi_results = [{"fecha": item['date'], "NDVI": item.get('mean_NDVI', None)} for item in results]

    # Ahora evaluamos si el polígono pertenece a alguna región en un ráster
    # Por ejemplo, podríamos usar un ráster de cobertura terrestre
    regions = []
    try:
        unidad_vegetacion = ee.Image("projects/proyec2020/assets/Raster_UV")  # Este es un ejemplo de un ráster
        region_mask = unidad_vegetacion.reduceRegion(
            reducer=ee.Reducer.mode(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=50,
            maxPixels=1e9
        )

        # Reducir la imagen para obtener la fracción de cada clase de cobertura terrestre en el polígono
        region_reduction = unidad_vegetacion.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=30,
            maxPixels=1e9
        )
        

        # Obtener el resultado como un diccionario
        landcover_histogram = region_reduction.getInfo()
        print('revisar',landcover_histogram.get('b1').values())
        print(sum(landcover_histogram.get('b1').values()))



        # Verificar si la clave del histograma es correcta
        if isinstance(landcover_histogram.get('b1'), dict):

                    # Mapeo de clases de cobertura terrestre
            region_names = {
                    '25.0' : 'Monte Austral o Tipico',
                    '5.0' : 'Delta del Parana',
                    '32.0' : 'Pampa Interior Occidental',
                    '27.0' : 'Campos y Urundayzales',
                    '37.0' : 'Distrito de la Payunia',
                    '38.0' : 'Distrito Subandino-Estepa de coiron blanco',
                    '46.0' : 'Distrito Subandino-Estepa magallanica seca',
                    '49.0' : 'Ecotono de la Peninsula de Valdes',
                    '26.0' : 'Monte Oriental o de Transicion',
                    '4.0' : 'Valle del Parana',
                    '13.0' : 'Chaco Subhumedo',
                    '29.0' : 'Pampa Mesopotamica',
                    '22.0' : 'Caldenal',
                    '30.0' : 'Pampa Ondulada',
                    '1.0' : 'Selva Montana y Bosque de Aliso y Pino del cerro',
                    '24.0' : 'Bolsones Endorreicos',
                    '41.0' : 'Distrito Central-Estepa arbustiva serrana',
                    '6.0' : 'Prepuna',
                    '14.0' : 'Chaco Humedo con Bosques, Pajonales y Palmares de Caranday',
                    '15.0' : 'Chaco Humedo con Bosques y Canadas',
                    '40.0' : 'Distrito Central-Estepa arbustiva de quilenbai',
                    '33.0' : 'Pampa Deprimida',
                    '7.0' : 'Chaco Serrano',
                    '12.0' : 'Chaco Semiarido',
                    '21.0' : 'Algarrobal',
                    '34.0' : 'Pampa Austral',
                    '10.0' : 'Salinas Grandes',
                    '42.0' : 'Distrito Central-Erial',
                    '45.0' : 'Estepa arbustiva de mata negra',
                    '31.0' : 'Pampa Interior Plana',
                    '9.0' : 'Chaco Arido',
                    '17.0' : 'Pajonales y Palmares de Yatay',
                    '23.0' : 'Monte de Sierras y Bolsones',
                    '50.0' : 'Bosques Andino-Patagonicos',
                    '43.0' : 'Distrito del Golfo San Jorge',
                    '3.0' : 'Selva Misionera-Selva Paranaense',
                    '20.0' : 'Espinillar',
                    '11.0' : 'Banados de Mar Chiquita-Espartillares y zampales',
                    '16.0' : 'Bajos Submeridionales-Espartillares',
                    '44.0' : 'Distrito Central',
                    '19.0' : 'Nandubayzal y Selva de Montiel',
                    '48.0' : 'Ecotono Rionegrino',
                    '47.0' : 'Distrito Fueguino-Estepa magallanica humeda',
                    '8.0' : 'Pastizales de Altura',
                    '28.0' : 'Malezales',
                    '39.0' : 'Distrito Occidental',
                    '18.0' : 'Esteros del Ibera',
                    '2.0' : 'Selva de Transicion',
                    '35.0' : 'Puna',
                    '36.0' : 'Provincia Altoandina'
                        }
            # Calcular el porcentaje de cada región en el polígono
            total_area = sum(landcover_histogram.get('b1').values())
            if total_area > 0:
                for key, value in landcover_histogram.get('b1').items():
                    region_name = region_names.get(key, "Unknown") 
                    regions.append({
                        "name": region_name,
                        "percentage": (value / total_area) * 100
                    })                    

                # Determinar la clase con mayor porcentaje
                dominant_region = max(regions, key=lambda x: x['percentage'])
                dominant_region_name = dominant_region['name']
                dominant_region_percentage = dominant_region['percentage'] 
                
            else:
                dominant_region_name = "No coverage detected"
                dominant_region_percentage = 0
        else:
            dominant_region_name = "No coverage detected"
            dominant_region_percentage = 0

    except Exception as e:
        print("Error al evaluar la región:", e)
        dominant_region_name = "Error"
        dominant_region_percentage = 0
    print(regions)
    # Devolver NDVI y la región dominante
    return {
        "ndvi_data": ndvi_results,
        "dominant_region": {
            "name": dominant_region_name,
            "percentage": dominant_region_percentage,
        },
        "regions": regions  # Devolver todas las regiones con sus porcentajes para referencia
    }

        
