import pandas as pd
import geopandas as gp
import shapely.geometry as sgeo

from shapely.geometry import Point
from shapely.strtree import STRtree

df_stations = pd.read_csv('moscow_metro_stations.csv')
df_stations_gdf = gp.GeoDataFrame(df_stations, geometry=gp.points_from_xy(df_stations.Longitude, df_stations.Latitude))

tree = STRtree(df_stations_gdf['geometry'])

coords_1 = Point(37.585700, 55.693312)
print('coords_1 ', tree.nearest(coords_1))
print(df_stations_gdf[df_stations_gdf.index == 46]['geometry'])

coords_2 = (df_stations_gdf[df_stations_gdf.index == tree.nearest(coords_1)]['geometry']).ravel()[0]
print('coords_2 ', coords_2)
# (37.58499 55.70678)