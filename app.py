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
    #print(f"Outer: {outer_ring}")
   # print(f"Divide")
    
    mask = gdf['geometry'].apply(lambda x: not x.within(outer_ring))
    print("Mask: " + str(mask))
    outside_shapes = gdf[mask]
    # Get only the polygon from the filtered GeoDataFrame
    outside_polygons = outside_shapes[outside_shapes['geometry'].geom_type == 'Polygon']
    # Reset the index
    outside_polygons = outside_polygons.reset_index(drop=True)
    
    # Access the first polygon
    # Simplify the polyggon(s)
    simplified_polygons = outside_polygons['geometry'].apply(lambda x: x.simplify(0.1))

    # Assign the simplified polyggon(s) back to the GeoDataFrame
    outside_polygons['geometry'] = simplified_polygons
    print(f"Outside Polys: {outside_polygons}")
    ploys.append(outer_ring)
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
            
    print(poly_list)

    gdf = gpd.GeoDataFrame(columns=['geometry'])
    for item in poly_list:
        
        gdf = gdf.append({'geometry': item}, ignore_index=True)
    return gdf

def create_Perimeter_geom(poly):
    poly_array = []

    for pol in poly['geometry']:
        exterior = pol.exterior
        poly_array.append(exterior)
    return poly_array

    
########################################################################################### Get the outer ring and convert it to a Polygon for futher calculations 

def CalcArea(area):
    return round(area / 10000, 2)

def CalcPerimeter(perimeter):

    current_perimeter = perimeter.length


    return round(current_perimeter,2)



def Main():
    Total_Hr = []
    Total_Poly_hr = []
    Total_area_geom = []
    Total_perim_geom = []
    Total_concave_geom = []

    RESULTS = pd.DataFrame(columns=['time_period','Poly_hr_count','area_geom','perim_geom', 'concave_perim_geom'])
    output = create_temporal_output(ISOCHRONES)
    
    
    for name, group in output:
        outer_perimeter = create_concave_perimeter(group)
        poly = construct_area(group)
        perimeter_geom = construct_perimeter(poly)
        forest_intersection = gpd.overlay(poly , FOREST_ISOCHRONES, how='intersection') 
        grass_perimeter = CalcPerimeter(poly) - CalcPerimeter(forest_intersection)
        
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(12, 4))
        plt.title(name)
        perimeter_geom.plot(ax=ax1, cmap='viridis')
        ax1.set_title("Perimeter Outline")
        ax1.annotate(name , xy=(0.5, 0.5), xycoords='axes fraction',
                ha='center', va='center', size=12)
        forest_intersection.plot(ax=ax2)
        ax2.set_title("Forest Interect")
        ax2.annotate(f"Area: {CalcArea(forest_intersection.area)}, Perimeter: {CalcPerimeter(forest_intersection)}, Grass Perimeter: {grass_perimeter}", xy=(0.5, 0.5), xycoords='axes fraction',
                ha='center', va='center', size=12)
        poly.plot(ax=ax3, cmap='viridis') 
        #convex_hull_plot_2d(temp(group), ax=ax3)
        ax3.set_title("Area Polygon")
        ax3.annotate(f"Area: {CalcArea(poly.area)}, Perimeter: {CalcPerimeter(poly)}", xy=(0.5, 0.5), xycoords='axes fraction',
                ha='center', va='center', size=12)
        outer_perimeter.plot(ax=ax4)
        plt.show()
        print('Areas: ' + str(CalcArea(poly.area)))
        print('Perimeter: ' + str(CalcPerimeter(poly)))
        #['time_period','Poly_hr_count','area_geom','perim_geom','total_perimeter', 'total_area']
        count = 1
        print(group['geometry'])
        
        for index, row in poly.iterrows():
           # print("Area" + str(poi['geometry']))
           Total_area_geom.append(row['geometry'])
           Total_Poly_hr.append(count)
           Total_Hr.append(name)
           count = count + 1
        for index, row in outer_perimeter.iterrows():
            Total_concave_geom.append(row['geometry'])
           
        for index, row in perimeter_geom.iterrows():
            Total_perim_geom.append(row['geometry'])
            
    for item in range(len(Total_Hr)):
        RESULTS = RESULTS.append({'time_period': Total_Hr[item], 'Poly_hr_count': Total_Poly_hr[item], 'area_geom': Total_area_geom[item],'perim_geom': Total_perim_geom[item], 'concave_perim_geom': Total_concave_geom[item] },ignore_index=True)    

        

    RESULTS.to_csv('results1.csv')

   # ISOCHRONES['geometry'].plot()
   # output.plot()
    #single_fire_summary.plot()
   # plt.show()
    #single_fire_summary.to_file('concave_hull03.shp')



Main()
