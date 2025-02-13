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
def get_ndvi_and_regions(polygon, start_date, end_date):
    # Iniciar Google Earth Engine
    initialize_earth_engine()
    
    # Función para crear la máscara de nubes a partir de la banda de calidad.
    # Se asume que en la banda "MSK_CLDPRB" 0 indica píxel sin nubes y 1 con nubes.
    # Así, con .lt(1) se generan 1 (sin nubes) y 0 (con nubes)
    def maskcloud(img):
       q = img.select(["MSK_CLDPRB"]).lt(1)
       return img.updateMask(q).addBands(q.rename('q'))

    # Cargar la colección Sentinel‑2 SR harmonized, filtrando por fecha, ubicación y porcentaje de nubes
    dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterDate(start_date, end_date) \
        .filterBounds(ee.Geometry.Polygon(polygon['coordinates'][0])) \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 80) \
        .select("B4", "B8", "MSK_CLDPRB") \
        .map(maskcloud)

    # Función para calcular NDVI y recortar a la región de interés
    def NDVI(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi).clip(ee.Geometry.Polygon(polygon['coordinates'][0]))
    
    # Aplicar la función NDVI a la colección; la imagen resultante incluye la banda 'NDVI' y la banda 'q'
    ndvi = dataset.map(NDVI).select('NDVI', 'q')

    # Función para asignar la propiedad 'fecha' a cada imagen
    def get_image_dates(image):
        return image.set('fecha', image.date().format())
    
    dates_list = ndvi.map(get_image_dates).aggregate_array('fecha')

    # Función que, para cada fecha, evalúa la calidad (píxeles sin nubes) y, si es aceptable,
    # calcula el promedio de NDVI usando solo los píxeles sin nubes.
    def get_average_ndvi(date):
        # Seleccionar imágenes dentro del día
        daily_images = ndvi.filterDate(date, ee.Date(date).advance(1, 'day'))
        # Seleccionar las bandas 'NDVI' y 'q'
        daily_image = daily_images.select(['NDVI','q']).mean()
        
        # Calcular el promedio de la banda 'q' en la región para obtener el porcentaje de píxeles claros.
        quality_dict = daily_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=30,
            maxPixels=1e9
        )
        clearFraction = ee.Number(quality_dict.get('q')).gte(0.8)
        
        # Condición: si el % de píxeles sin nubes es mayor o igual al 20%, se calcula el promedio de NDVI;
        # de lo contrario se descarta la fecha (se retorna None)
        def compute_ndvi():
            mean_ndvi = daily_image.select("NDVI").rename('mean_NDVI')
            ndvi_roi = mean_ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
                scale=30,
                maxPixels=1e9
            )
            return ee.Dictionary(ndvi_roi).set('date', date)
        
        # Si clearFraction >= 0.8 se computa el NDVI promedio; de lo contrario se retorna None
        result = ee.Algorithms.If(ee.String(clearFraction), compute_ndvi(), None)
        return result

    # Mapear la función sobre la lista de fechas y obtener la colección diaria
    daily_ndvi_collection = ee.List(dates_list.map(get_average_ndvi))
    # Obtener los resultados como una lista de diccionarios
    results = daily_ndvi_collection.getInfo()
    # Filtrar fechas eliminadas (None) y formatear resultados
    ndvi_results = [{"fecha": item['date'], "NDVI": item.get('mean_NDVI', None)}
                    for item in results if item is not None]

    # Ahora evaluamos a qué unidad de vegetación pertenece el polígono usando un ráster de cobertura terrestre.
    regions = []
    try:
        unidad_vegetacion = ee.Image("projects/proyec2020/assets/Raster_UV")
        region_mask = unidad_vegetacion.reduceRegion(
            reducer=ee.Reducer.mode(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=50,
            maxPixels=1e9
        )
        region_reduction = unidad_vegetacion.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=30,
            maxPixels=1e9
        )
        landcover_histogram = region_reduction.getInfo()
        # Ejemplo de impresión para depuración
        print('Histogram:', landcover_histogram.get('b1').values())
        print('Total area count:', sum(landcover_histogram.get('b1').values()))
        if isinstance(landcover_histogram.get('b1'), dict):
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
            total_area = sum(landcover_histogram.get('b1').values())
            if total_area > 0:
                for key, value in landcover_histogram.get('b1').items():
                    region_name = region_names.get(key, "Unknown")
                    regions.append({
                        "name": region_name,
                        "percentage": (value / total_area) * 100
                    })
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
    # Devolver NDVI y la región dominante junto con la lista de regiones
    return {
        "ndvi_data": ndvi_results,
        "dominant_region": {
            "name": dominant_region_name,
            "percentage": dominant_region_percentage,
        },
        "regions": regions
    }


        
