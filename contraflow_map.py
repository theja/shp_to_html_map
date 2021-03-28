import folium
import shapefile
import geopandas as gpd
import numpy as np
import json
from bisect import bisect

def line_color(row):
    if row['StOperNEU'] == 1 and row['FEDERALFUN'] == 7:
        return 'red'
    elif row['StOperNEU'] == 21:
        return 'yellow'
    else:
        return 'green'

def line_weight(row, break_points, wgt_limits=(0.5, 4)):
    wgt_step = (wgt_limits[1]-wgt_limits[0])/(len(break_points)-1)
    break_points = sorted(np.array(break_points))
    return (wgt_limits[0]+wgt_step*bisect(break_points, row['scaled_centrality']))

def line_style(feature):
    return {
        'opacity': 1,
        'weight': feature['properties']['line_weight'],
        'color': feature['properties']['line_color']
    }
    
contraflow_shp = "C:/Users/tputta/Dropbox/Dec_2018_laptop_work_files/Street_Network_from_Theja_Jul16_2019/Street_Network_from_Theja_Jul16_2019.shp"

gdf = gpd.read_file(contraflow_shp)
gdf.to_crs(epsg=4326, inplace=True)

keep_cols = ['StOperNEU', 'FEDERALFUN', 'STREETNAME', 'Cent_Rank', 'lts2_trps2', 'geometry', 'ContrMile']
oneway_st = {'StOperNEU': 1}
contraflow_st = {'StOperNEU': 21}
local_st = {'FEDERALFUN': 7}
streetname = 'STREETNAME'
centrality_rank = 'Cent_Rank'
centrality_score = 'lts2_trps2' # if value > 0 then low-stress
contraflow_miles = 'ContrMile'
break_points = (
    0.0025,
    0.0086,
    0.0183,
    0.0321,
    0.0490,
    0.0779,
    0.1312,
    0.2073,
    0.3284,
    1.0000
)

# drop unwanted columns
drop_cols = np.setdiff1d(gdf.columns, keep_cols)
gdf.drop(columns=drop_cols, inplace=True)
# Drop high stress links
gdf.drop(gdf[gdf['lts2_trps2'] <= 0].index, inplace=True)

# add a column with centrality scaled between 0 and 1
gdf['scaled_centrality'] = np.array(gdf.lts2_trps2)/max(gdf.lts2_trps2)

# add a line color and weight column for the map
gdf['line_color'] = gdf.apply(lambda row:line_color(row), axis=1)
gdf['line_weight'] = gdf.apply(lambda row:line_weight(row, break_points=break_points), axis=1)

# create a folium map and add features to it
map_bounds = gdf.total_bounds
map_center = [(map_bounds[1]+map_bounds[3])/2, (map_bounds[0]+map_bounds[2])/2]
gjson = json.loads(gdf.to_json())

m = folium.Map(location=map_center,
               zoom_start=11,
               tiles='cartodbpositron',
               control_scale=True,
               min_zoom=9,
               min_lon=map_bounds[0]-0.5,
               min_lat=map_bounds[1]-0.5,
               max_lon=map_bounds[0]+0.5,
               max_lat=map_bounds[1]+0.5,
               max_bounds=True
              )
layer_geom = folium.FeatureGroup(name='Low-Stress Links', control=True)

geojson_layer = folium.GeoJson(gjson, style_function=line_style)
geojson_layer.add_to(layer_geom)
layer_geom.add_to(m)