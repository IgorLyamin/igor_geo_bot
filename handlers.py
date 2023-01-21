import config
import requests
from json.decoder import JSONDecodeError
from utils import get_kb
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from shapely.strtree import STRtree
import mpu


def get_coords(coords):
    coords_address = map(float, coords.split())
    return list(coords_address)


def get_response(url, params=None):
    response = requests.get(url, params=params)
    if not response:
        print("Ошибка выполнения запроса:")
        print(url)
        print(f"Http статус: {response.status_code} ('{response.reason}')")
    return response


def full_reply(update, context):
    address = update.message.text

    # Возвращает координаты адреса по яндекс api
    coords, full_address = return_coords(address)

    # Возвращает ближайшую станцию метро
    closest_metro, dist, coords_nearest_metro = get_nearest_moscow_metro(coords)

    # Расстояние до ближайшего метро пешком
    coords_address = get_coords(coords)
    print('coords_nearest_metro ', coords_nearest_metro)
    coords_metro = [coords_nearest_metro.x.iloc[0], coords_nearest_metro.y.iloc[0]]

    walk_dist, walk_hours, walk_minutes = get_journey_time([coords_address, coords_metro], 'man')

    # Возвращает ближайший парк и расстояние до него по прямой
    nearest_park_name, nearest_park_distance = get_nearest_moscow_park(coords)

    # Расстояние до ближайшего парка пешком

    # Полная строка текстового ответа
    update.message.reply_text(f"Координаты: {coords}. Полный адрес: {full_address}. Ближайшая станция метро - {closest_metro}, расстояние до неё по прямой {dist} км. Пешком до метро {walk_dist} км, время в пути {walk_hours} ч {walk_minutes} мин. Ближайший парк - {nearest_park_name}, расстояние до неё по прямой {nearest_park_distance} км.")

    # Отправка картинки с картой
    return_map_image(coords)
    context.bot.send_photo(update.message.chat.id, photo=open('response.jpg', 'rb'))


def get_journey_time(coords, type_):
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'Authorization': config.API_KEY_OPENROUTESERVICE,
    }
    types = {
        'car': 'driving-car',
        'man': 'foot-walking',
    }
    data = {
        'locations': coords,
        'metrics': ['distance', 'duration'],
        'units': 'm'
    }
    response = requests.post(
        f'https://api.openrouteservice.org/v2/matrix/{types[type_]}',
        headers=headers, json=data
    ).json()
    duration = response['durations'][0][1]
    hours = int(duration // 3600)
    minutes = int(duration % 3600 // 60)
    dist = response['distances'][0][1]
    dist = round(dist / 1000, 1)

    return dist, hours, minutes


def return_coords(address):
    API_KEY = config.API_KEY_YANDEX
    url = config.url_yandex

    params = {
        'apikey': API_KEY,
        'format': 'json',
        'geocode': address
    }
    response = get_response(url, params)

    try:
        response = response.json()
        # print(response)
        coords = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        full_address = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']        

    except (IndexError, KeyError, JSONDecodeError):
        print('Некорретный формат ответа от API')

    return coords, full_address


def return_map_image(coords):
    map_request = "http://static-maps.yandex.ru/1.x/?ll={ll}&z={z}&l={type}&pt={ll},pm2bll".format(ll = str(coords).replace(' ', ','), z = 14, type = "map")

    map_response = requests.get(map_request)

    if not map_response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", map_response.status_code, "(", map_response.reason, ")")

    map_file = "response.jpg"
    with open(map_file, "wb") as file:
        file.write(map_response.content)


def say_hello(update, context):
    username = update.message.chat.username
    update.message.reply_text(
        f'Привет, {username.capitalize()}!',
        # reply_markup=get_kb()
        )


def get_nearest_moscow_park(coords):

    path = "geo_data/moscow_parks.geojson"

    with open(path, "r", encoding="utf8") as file:
        df = gp.read_file(file)

    coords1, coords2 = map(float, coords.split())
    current_point = Point(coords1, coords2)
    polygon_index = df.distance(current_point).sort_values().index[0]

    nearest_park_name = df['Attributes'][polygon_index]['CommonName']
    nearest_park_distance = df.distance(current_point).sort_values().reset_index(drop=True)[0]

    # TODO есть расстояние между точкой и полигоном, надо найти координаты ближайшей точки на полигоне

    return nearest_park_name, round(nearest_park_distance * 10**2, 1)


def get_nearest_moscow_metro(coords):

        df_stations = pd.read_csv('geo_data/moscow_metro_stations.csv')
        df_stations_gdf = gp.GeoDataFrame(df_stations, geometry=gp.points_from_xy(df_stations.Longitude, df_stations.Latitude))

        tree = STRtree(df_stations_gdf['geometry'])

        coords_1 = Point(float(coords.split(" ")[0]), float(coords.split(" ")[1]))
        coords_2 = df_stations_gdf[df_stations_gdf['geometry'] == tree.nearest(coords_1)]['geometry']


        # dist = round(mpu.haversine_distance((coords_1.x, coords_1.y), (float(coords_2.x), float(coords_2.y))), 1)
        dist = 1
        # closest_metro = df_stations_gdf[df_stations_gdf['geometry'] == tree.nearest(coords_1)]['Name'].iloc[0]
        closest_metro = 1

        return closest_metro, dist, coords_2


# def detect_address(ll):
#     API_KEY = '40d1649f-0493-4b70-98ba-98533de7710b'
#     url = 'https://geocode-maps.yandex.ru/1.x/' # Вынести в settings!
#     params = {
#         'apikey': API_KEY,
#         'geocode': ll,
#         'format': 'json'
#     }
#     response = get_response(url, params)
#     try:
#         response = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
#         postal_code = response['metaDataProperty']['GeocoderMetaData']['Address'].get('postal_code', 'Не определен')
#         response = response['metaDataProperty']['GeocoderMetaData']['Address']['formatted']
#         return response, postal_code
#     except (IndexError, KeyError, ValueError):
#         print('Некорретный формат ответа от API')