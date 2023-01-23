import config
import requests
from json.decoder import JSONDecodeError
from utils import get_kb
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from shapely.strtree import STRtree
import mpu


def get_direct_distance(coords_1, coords_2):
    print(coords_1)
    print(coords_2)
    return round(mpu.haversine_distance((float(coords_1.x), float(coords_1.y)), (float(coords_2.x), float(coords_2.y))), 1)


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

# def select_priority(update, context):
#     address = update.message.text
#     ['Метро', 'Центр', 'Парк']

def full_reply(update, context):
    address = update.message.text

    # Возвращает координаты адреса по яндекс api
    coords, full_address = return_coords(address)

    # Возвращает ближайшую станцию метро
    closest_metro, dist, coords_nearest_metro = get_nearest_moscow_metro(coords)

    # Расстояние до ближайшего метро пешком
    coords_address = get_coords(coords)
    coords_metro = [coords_nearest_metro.x.iloc[0], coords_nearest_metro.y.iloc[0]]

    walk_dist, walk_hours, walk_minutes = get_journey_time([coords_address, coords_metro], 'man')

    # Возвращает ближайший парк и расстояние до него по прямой
    nearest_park_name, nearest_park_distance = get_nearest_moscow_park(coords)
    
    # Расстояние до ближайшего парка пешком

    # Расстояние до центра Москвы    
    msk_cent_coords = Point(37.617592, 55.755922)
    msk_cent_dist = get_direct_distance(Point(float(coords.split(" ")[0]), float(coords.split(" ")[1])), msk_cent_coords)

    # Полная строка текстового ответа
    # Координаты: {coords}.
    update.message.reply_text(f"Полный адрес: {full_address}. Ближайшая станция метро - {closest_metro}, расстояние до неё по прямой {dist} км. Пешком до метро {walk_dist} км, время в пути {walk_hours} ч {walk_minutes} мин. Ближайший парк - {nearest_park_name}, расстояние до неё по прямой {nearest_park_distance} км. Расстояние по прямой до центра Москвы {msk_cent_dist} км.")

    # Отправка картинки с картой
    return_map_image(coords)
    context.bot.send_photo(update.message.chat.id, photo=open('response.jpg', 'rb'))

    # Общий score адреса    
    total_score = (0.3 * get_total_score(dist) + 0.2 * get_total_score(nearest_park_distance) + 0.5 * get_total_score(msk_cent_dist / 10))
    update.message.reply_text(f"Общий рейтинг данной локации {round(total_score, 1)} из 10.")

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
        f'Приветствую, {username.capitalize()}! Я умею оценивать расположения домов в Москве относительно ближайшего метро, парка и удаления от центра. Выберите в порядке убывания важности для вас объекты и нажмите кнопку старт. По умолчанию приоритизация: расстояние до центра, метро, парк.',
        reply_markup=get_kb()
        )


def get_nearest_moscow_park(coords):

    path = "moscow_parks.geojson"

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

        df_stations = pd.read_csv('moscow_metro_stations.csv')
        df_stations_gdf = gp.GeoDataFrame(df_stations, geometry=gp.points_from_xy(df_stations.Longitude, df_stations.Latitude))

        tree = STRtree(df_stations_gdf['geometry'])

        coords_1 = Point(float(coords.split(" ")[0]), float(coords.split(" ")[1]))
        coords_2 = (df_stations_gdf[df_stations_gdf['geometry'] == tree.nearest(coords_1)]['geometry'])

        # print('coords_2', coords_2)
        # print(type(coords_2))
        dist = get_direct_distance(coords_1, coords_2)
        closest_metro = df_stations_gdf[df_stations_gdf['geometry'] == tree.nearest(coords_1)]['Name'].iloc[0]

        return closest_metro, dist, coords_2


def get_total_score(distance):
    
    score = 0
    if distance < 0.1:
        score = 10
    elif (distance >= 0.1) & (distance < 0.2):
        score = 9
    elif (distance >= 0.2) & (distance < 0.4):
        score = 8
    elif (distance >= 0.4) & (distance < 0.7):
        score = 7
    elif (distance >= 0.7) & (distance < 1.0):
        score = 6
    elif (distance >= 1.0) & (distance < 1.5):
        score = 5
    elif (distance >= 1.5) & (distance < 2):
        score = 4
    elif (distance >= 2) & (distance < 3):
        score = 3
    elif (distance >= 3) & (distance < 4):
        score = 2
    elif (distance >= 4) & (distance < 5):
        score = 1
    else:
       score = 0

    return score

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