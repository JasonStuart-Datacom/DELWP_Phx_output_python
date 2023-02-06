
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon,LineString
from shapely.ops import cascaded_union
from scipy.spatial import ConvexHull
import pandas as pd
ISOCHRONES = gpd.read_file("bushfire_test2_Iso.shp", crs='epsg:32618')
FOREST_ISOCHRONES = gpd.read_file("forest_areas_tanker_accessv3ii.shp", crs='epsg:32618')


def create_temporal_output(gdf):
        # Convert the MINUTES column to hours
    gdf['MINUTES'] = gdf['MINUTES'] / 60

    # Create a new column that groups the MINUTES into the specified intervals
    gdf['Interval'] = '0-2 hours'
    gdf.loc[(gdf['MINUTES'] > 2) & (gdf['MINUTES'] <= 4), 'Interval'] = '2-4 hours'
    gdf.loc[(gdf['MINUTES'] > 4) & (gdf['MINUTES'] <= 8), 'Interval'] = '4-8 hours'
    gdf.loc[(gdf['MINUTES'] > 8) & (gdf['MINUTES'] <= 18), 'Interval'] = '8-18 hours'
    
    grouped = gdf.groupby('Interval')
    return grouped



######################################################################################### calc the ISOCRONES by hours 










def create_Area_geom(df):
    
    ploys = []
   
    gdf = gpd.GeoDataFrame(columns=['geometry'])
    line_strings = [l for l in df.geometry]
    for line in range(len(line_strings)):
            merged_line_string = LineString(line_strings[line])

            polygon = Polygon(merged_line_string)
            gdf = gdf.append({'geometry': polygon}, ignore_index=True)
        # convert the Polygon geometry to a GeoDataFrame
    gdf['geometry'] = gdf['geometry'].apply(lambda x: x if x.is_valid else Polygon(x).buffer(0))

    max_area = gdf['geometry'].area.idxmax()
    outer_ring = gdf.loc[max_area,'geometry']
    outer_ring = outer_ring.buffer(2)
    outer_ring_simplify = outer_ring.simplify(0.1)

    #print(f"Outer: {outer_ring}")
   # print(f"Divide")
    
    mask = gdf['geometry'].apply(lambda x: not x.within(outer_ring_simplify))
    print("Mask: " + str(mask))
    outside_shapes = gdf[mask]
    # Get only the polygon from the filtered GeoDataFrame
    outside_polygons = outside_shapes[outside_shapes['geometry'].geom_type == 'Polygon']
    # Reset the index
    outside_polygons = outside_polygons.reset_index(drop=True)
    
    # Access the first polygon
    # Simplify the polyggon(s)
    simplified_polygons = outside_polygons['geometry'].apply(lambda x: x.simplify(0.01))

    # Assign the simplified polyggon(s) back to the GeoDataFrame
    outside_polygons['geometry'] = simplified_polygons
    print(f"Outside Polys: {outside_polygons}")
    ploys.append(outer_ring_simplify)
    for item in range(len(outside_polygons)):
        outside_polygon = outside_polygons.loc[item, 'geometry']
        ploys.append(outside_polygon)


  

    return ploys

def construct_area(df):

    gdf = gpd.GeoDataFrame(columns=['geometry'])
    area_geom = create_Area_geom(df)

    for area in area_geom:
         gdf = gdf.append({'geometry': area}, ignore_index=True)
    return gdf

def construct_perimeter(df):
    
    gdf = gpd.GeoDataFrame(columns=['geometry'])
    perimeter_geom = create_Perimeter_geom(df)
    print(f"Perimeter {perimeter_geom}")
    for area in perimeter_geom:

         gdf = gdf.append({'geometry': area}, ignore_index=True)
    return gdf

def construct_concave_perimeter(df):
    gdf = gpd.GeoDataFrame(columns=['geometry'])
    concave = create_concave_perimeter(df)
    for item in concave:
        
        gdf = gdf.append({'geometry': item}, ignore_index=True)
    return gdf 

def create_concave_perimeter(df):
    
   # # Convert the MultiLineString to a Polygon
    multipolygon = cascaded_union(list(gpd.GeoSeries(df.geometry).buffer(1)))
    print(type(multipolygon))
    poly_list = []
    if isinstance(multipolygon, MultiPolygon):
      
        #print(multipolygon)
        for polygon in multipolygon.geoms:
            print("start")
            #print(Polygon(polygon))
           # print('n')
            hull = ConvexHull(polygon.exterior.coords)
                        # create a sub-sampled version of the convex hull using the threshold
            #subsampled_hull = hull.vertices[hull.equations[:, -1] < tightness]
           # print(hull)concave_hull = hull.partial_Hull(tightness)
            newPoly = LineString([[p[0], p[1]] for p in hull.points[hull.vertices]])
            
            print(newPoly)
            poly_list.append(newPoly)
            print(len(poly_list))
            print("end")
    else:
        if isinstance(multipolygon, Polygon):
                
                
                hull = ConvexHull(multipolygon.exterior.coords)
                newPoly = LineString([[p[0], p[1]] for p in hull.points[hull.vertices]])
                poly_list.append(newPoly)
            
    #print(poly_list)

    
    return poly_list

def create_Perimeter_geom(poly):
    poly_array = []

    for pol in poly['geometry']:
        exterior = pol.exterior
        new_lineString = LineString(exterior)
        poly_array.append(new_lineString)
    return poly_array

    
########################################################################################### Get the outer ring and convert it to a Polygon for futher calculations 

def CalcArea(area):
    return round(area / 10000, 2)

def CalcPerimeter(perimeter):

    current_perimeter = perimeter.length


    return round(current_perimeter,2)

def showVisuals(hour, concave_geom,area_geom,perimeter_geom, forest_geom):
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(12, 4))
        plt.title(hour)
        perimeter_geom.plot(ax=ax1, cmap='viridis')
        ax1.set_title("Perimeter Geom")
        ax1.annotate(hour , xy=(0.5, 0.5), xycoords='axes fraction',
                ha='center', va='center', size=12)
        forest_geom.plot(ax=ax2)
        ax2.set_title("Forest Interect")
        
        area_geom.plot(ax=ax3, cmap='viridis') 
        #convex_hull_plot_2d(temp(group), ax=ax3)
        ax3.set_title("Area Geom")
        
        concave_geom.plot(ax=ax4)
        ax4.set_title("Concave Geom")
        plt.show()

def SaveResults(time_hour, concave_geom,area_geom,perimeter_geom, poly_hr_count):
    
    # Change the name of the column in each GeoDataFrame to avoid conflicts when concatenating
    area_geom.rename(columns={'geometry': 'geometry1'}, inplace=True)
    perimeter_geom.rename(columns={'geometry': 'geometry2'}, inplace=True)
    concave_geom.rename(columns={'geometry': 'geometry3'}, inplace=True)


    gdf_final = pd.concat([area_geom, perimeter_geom, concave_geom], axis=1)
    gdf_final = gdf_final[['geometry1', 'geometry2', 'geometry3']]
    # Rename the columns to match the desired header
    gdf_final.rename(columns={'geometry1': 'area_geom', 'geometry2': 'perim_geom', 'geometry3': 'concave_perim_geom'}, inplace=True)

    gdf_final['time_period'] = time_hour
    gdf_final['Poly_hr_count'] = poly_hr_count
    # Reorder the columns to match the desired header
    gdf_final = gdf_final[['time_period','Poly_hr_count','area_geom','perim_geom', 'concave_perim_geom']]
    print(gdf_final)
    gdf_final.to_csv('data.csv', mode='w', header=True, index=True)
  


def Main():
    
    
    output = create_temporal_output(ISOCHRONES)
    gdf_area = gpd.GeoDataFrame(columns=['geometry'])
    gdf_concave = gpd.GeoDataFrame(columns=['geometry'])
    gdf_perimeter = gpd.GeoDataFrame(columns=['geometry'])
    gdf_time_hour = gpd.GeoDataFrame(columns=['Interval'])
    gdf_Poly_hour = gpd.GeoDataFrame(columns=['Poly_hr_count'])
    for hour, group in output:
        concave_perimeter = construct_concave_perimeter(group)
        area_geom = construct_area(group)
        print(area_geom)
        perimeter_geom = construct_perimeter(area_geom)
        forest_intersection = gpd.overlay(area_geom , FOREST_ISOCHRONES, how='intersection') 
        showVisuals(hour,concave_perimeter,area_geom,perimeter_geom,forest_intersection)
        #['time_period','Poly_hr_count','area_geom','perim_geom','total_perimeter', 'total_area']
        poly_hr_count = 1
        for idx, row in area_geom.iterrows():
            gdf_area = gdf_area.append({'geometry': row['geometry']}, ignore_index=True)
            gdf_time_hour = gdf_time_hour.append({'Interval': hour}, ignore_index=True)
            gdf_Poly_hour = gdf_Poly_hour.append({'Poly_hr_count': poly_hr_count}, ignore_index=True)
            poly_hr_count = poly_hr_count + 1
        for idx, row in concave_perimeter.iterrows():
            gdf_concave = gdf_concave.append({'geometry': row['geometry']}, ignore_index=True)
        for idx, row in perimeter_geom.iterrows():
            gdf_perimeter = gdf_perimeter.append({'geometry': row['geometry']}, ignore_index=True)

    SaveResults(gdf_time_hour,gdf_concave,gdf_area,gdf_perimeter, gdf_Poly_hour)
        

            
    

        

   

if __name__ == "__main__": 
    Main()
