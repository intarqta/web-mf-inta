import ee
import json
from google.oauth2 import service_account
import os
import requests
from datetime import datetime, timedelta
import numpy as np

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

def get_nasa_power_data(centroid, start_date, end_date):
    """
    Obtiene los datos de NASA POWER con el siguiente enfoque:
      1. Se consulta la temperatura (T2M) en el rango de fecha solicitado.
      2. Para cada uno de los últimos 10 años se consulta la radiación (ALLSKY_SFC_PAR_TOT)
         en el rango solicitado. Si el rango abarca varios años se segmenta por cada año
         (o parte de año) de la consulta del usuario y se realizan las consultas históricas
         usando los límites de mes y día de cada segmento.
      3. Se calcula el percentil 95 para cada fecha (usando el mes y día como clave) en cada segmento.
      4. Se filtran los resultados según los días correspondientes del rango solicitado.
    
    Retorna una lista de diccionarios con:
       - "fecha": fecha (YYYY-MM-DD)
       - "temperatura": valor de T2M para ese día (según consulta actual)
       - "radiacion": percentil 95 de la radiación para ese día calculado con datos históricos
    """
    longitud, latitud = centroid

    # --- Consulta de temperatura para el rango solicitado ---
    iniAAAAMMDD = start_date.replace('-', '')
    finAAAAMMDD = end_date.replace('-', '')
    base_url_temp = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        "?parameters=T2M&community=RE"
        "&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON"
    )
    api_temp_url = base_url_temp.format(
        longitude=longitud, latitude=latitud,
        start=iniAAAAMMDD, end=finAAAAMMDD
    )
    response_temp = requests.get(url=api_temp_url, verify=True, timeout=30.00)
    temperature_data = {}
    if response_temp.status_code == 200:
        data_temp = response_temp.json()
        daily_data_temp = data_temp.get("properties", {}).get("parameter", {})
        temperature_data = daily_data_temp.get("T2M", {})
    else:
        print(f"Error en la consulta de temperatura: {response_temp.status_code}")

    # --- Descarga de datos históricos de radiación en el rango solicitado ---
    current_year = datetime.now().year
    # Usamos los últimos 10 años: si current_year es 2023, usamos de 2014 a 2023.
    start_year = current_year - 9
    end_year = current_year

    user_start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    user_end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Generar segmentos según el rango de años del usuario.
    # Cada segmento corresponde a:
    # - Primer año: desde la fecha de inicio hasta el 31 de diciembre.
    # - Años intermedios: desde 01-01 hasta 31-12.
    # - Último año: desde 01-01 hasta la fecha de fin.
    segments = []
    if user_start_dt.year == user_end_dt.year:
        segments.append((user_start_dt.year, user_start_dt, user_end_dt))
    else:
        for y in range(user_start_dt.year, user_end_dt.year + 1):
            if y == user_start_dt.year:
                seg_start = user_start_dt
                seg_end = datetime(year=y, month=12, day=31)
            elif y == user_end_dt.year:
                seg_start = datetime(year=y, month=1, day=1)
                seg_end = user_end_dt
            else:
                seg_start = datetime(year=y, month=1, day=1)
                seg_end = datetime(year=y, month=12, day=31)
            segments.append((y, seg_start, seg_end))

    # Diccionario para almacenar los datos históricos por segmento (año del usuario)
    # Estructura: { user_year: { "MM-DD": [valores de radiación] } }
    radiation_by_year = {}
    for seg in segments:
        user_year, seg_start, seg_end = seg
        radiation_by_year[user_year] = {}
        # Formateamos los límites del segmento (solo mes y día)
        md_start = seg_start.strftime("%m-%d")
        md_end = seg_end.strftime("%m-%d")
        
        # Para cada uno de los últimos 10 años históricos se consulta el API usando los límites del segmento.
        for hist_year in range(start_year, end_year + 1):
            hist_start_date = f"{hist_year}-{md_start}"  # Ejemplo: "2014-03-01"
            hist_end_date = f"{hist_year}-{md_end}"        # Ejemplo: "2014-12-31" o "2014-09-30"
            hist_start_str = hist_start_date.replace('-', '')
            hist_end_str = hist_end_date.replace('-', '')
            base_url_hist = (
                "https://power.larc.nasa.gov/api/temporal/daily/point"
                "?parameters=ALLSKY_SFC_PAR_TOT&community=AG"
                "&longitude={longitude}&latitude={latitude}&start={start}&end={end}&format=JSON"
            )
            hist_api_url = base_url_hist.format(
                longitude=longitud, latitude=latitud,
                start=hist_start_str, end=hist_end_str
            )
            response_hist = requests.get(url=hist_api_url, verify=True, timeout=30.00)
            if response_hist.status_code == 200:
                hist_data = response_hist.json()
                radiation_data = hist_data.get("properties", {}).get("parameter", {}).get("ALLSKY_SFC_PAR_TOT", {})
                for date_str, value in radiation_data.items():
                    try:
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                    except Exception as e:
                        print(f"Error al convertir la fecha {date_str}: {e}")
                        continue
                    # Usamos la clave mes-día (por ejemplo, "03-15")
                    md_key = date_obj.strftime("%m-%d")
                    try:
                        rad_val = float(value)
                    except Exception as e:
                        print(f"Error al convertir el valor de radiación para {date_str}: {e}")
                        continue
                    radiation_by_year[user_year].setdefault(md_key, []).append(rad_val)
            else:
                print(f"Error en la consulta histórica para el año {hist_year} en el segmento {user_year}: {response_hist.status_code}")

    # --- Cálculo del percentil 95 para cada mes-día en cada segmento ---
    percentil95_by_year = {}
    for user_year, data in radiation_by_year.items():
        percentil95_by_year[user_year] = {}
        for md_key, values in data.items():
            if values:
                percentil95_by_year[user_year][md_key] = np.percentile(values, 95)

    # --- Filtrado de resultados según el rango solicitado ---
    results = []
    current = user_start_dt
    while current <= user_end_dt:
        date_str = current.strftime("%Y%m%d")
        # Obtener la temperatura para la fecha solicitada
        temp_value = temperature_data.get(date_str, None)
        try:
            temp_value = float(temp_value) if temp_value is not None else None
        except Exception as e:
            print(f"Error al convertir la temperatura para {date_str}: {e}")
            temp_value = None
        
        # Se determina a qué segmento (año del usuario) pertenece la fecha actual y se usa la clave mes-día
        user_year = current.year
        md_key = current.strftime("%m-%d")
        rad_percentil_95 = percentil95_by_year.get(user_year, {}).get(md_key, None)

        results.append({
            "fecha": current.date(),
            "temperatura": temp_value,
            "radiacion": rad_percentil_95,
            "latitud": latitud
        })
        current += timedelta(days=1)

    return results

# Función principal para obtener NDVI y datos de NASA POWER
def get_ndvi(polygon, start_date='2024-01-01', end_date='2024-09-30', recurso_forrajero=None, presencia_leñosas=False, porcentaje_leñosas=0):
    ee.Authenticate()
    ee.Initialize(project="proyec2020")

    def maskcloud(img):
        q = img.select("MSK_CLDPRB").lt(1).rename('q')
        return img.updateMask(q).addBands(q)
    
    dataset = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterDate(start_date, end_date) \
        .filterBounds(ee.Geometry.Polygon(polygon['coordinates'][0])) \
        .select("B4", "B8", "MSK_CLDPRB") \
        .filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 10) \
        .map(maskcloud)

    def NDVI(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi).clip(ee.Geometry.Polygon(polygon['coordinates'][0]))

    ndvi = dataset.map(NDVI).select('NDVI')

    def get_image_dates(image):
        return image.set('fecha', image.date().format())

    dates_list = ndvi.map(get_image_dates).aggregate_array('fecha')

    def get_average_ndvi(date):
        daily_ndvi = ndvi.filterDate(date, ee.Date(date).advance(1, 'day')).select('NDVI')
        mean_ndvi = daily_ndvi.mean().rename('mean_NDVI')
        mean_ndvi_roi = mean_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee.Geometry.Polygon(polygon['coordinates'][0]),
            scale=30,
            maxPixels=1e9
        )
        return mean_ndvi_roi.set('date', date)

    daily_ndvi_collection = ee.List(dates_list.map(get_average_ndvi))
    results_ndvi = daily_ndvi_collection.getInfo()

    json_results = []
    for item in results_ndvi:
        result_item = {
            "fecha": item['date'],
            "NDVI": item.get('mean_NDVI', None)
        }
        result_item.update({
            "recurso_forrajero": recurso_forrajero,
            "presencia_leñosas": presencia_leñosas,
            "porcentaje_leñosas": porcentaje_leñosas if presencia_leñosas else 0
        })
        json_results.append(result_item)

    centroid = calculate_centroid(polygon)
    nasa_power_results = get_nasa_power_data(centroid, start_date, end_date)

    combined_results = {
        "nasa_power_data": nasa_power_results
    }
    json_output = json.dumps(combined_results, indent=4)
    return json_output

