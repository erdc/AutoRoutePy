#!/usr/bin/env python
import os
import sys

#package imports
from spt_erai_autorapid_process.AutoRoutePy.autoroute import AutoRoute 

#local imports
from spt_erai_autorapid_process.imports.helper_functions import case_insensitive_file_search


#------------------------------------------------------------------------------
#MAIN PROCESS
#------------------------------------------------------------------------------
def run_AutoRoute(autoroute_executable_location,
                  autoroute_input_path,
                  out_flood_raster_name,
                  out_shapefile_name="",
                  delete_flood_raster=False):
                      
    """
    Run AutoRoute with searching for inputs in directory
    """
        
    #get the raster for elevation    
    try:
        elevation_raster = case_insensitive_file_search(autoroute_input_path, r'elevation\.(?!prj)')
    except Exception:
        try:
            elevation_raster = case_insensitive_file_search(os.path.join(autoroute_input_path, 'elevation'), r'hdr\.adf')
        except Exception:
            print "Elevation raster not found. Skipping entire process ..."
            raise
        pass

    #get the land use information
    try:
        land_use_raster = case_insensitive_file_search(autoroute_input_path, r'land_use\.(?!prj)')
        land_use_manning_n_table = case_insensitive_file_search(autoroute_input_path, r'land_use_manning_n_table\.txt')
    except Exception:
        land_use_raster = ""
        land_use_manning_n_table = ""    
        print "Land use raster/manning n table not found. Ignoring these files ..."
        pass
    
    auto_mng = AutoRoute(autoroute_executable_location,
                         stream_file=case_insensitive_file_search(autoroute_input_path, r'streamflow_raster\.(?!prj)'),
                         dem_file=elevation_raster,
                         shp_out_file=out_flood_raster_name,
                         lu_raster=land_use_raster,
                         lu_manning_n=land_use_manning_n_table
                         )
                         
    if out_shapefile_name:             
        auto_mng.update_parameters(shp_out_shapefile=out_shapefile_name)
        
    auto_mng.run_autoroute(autoroute_input_file=case_insensitive_file_search(autoroute_input_path, r'AUTOROUTE_INPUT_FILE\.txt'))

    if delete_flood_raster:
        try:
            os.remove(out_flood_raster_name)
            os.remove("%s.prj" % os.path.splitext(out_flood_raster_name)[0])
        except OSError:
            pass
    

def run_AutoRoute_HTCondor_directory(autoroute_executable_location,
                                     autoroute_input_directory,
                                     out_flood_raster_name,
                                     out_shapefile_name="",
                                     delete_flood_raster=False):
    """
    Run AutoRoute in HTCondor execute directory
    """
    os.rename(autoroute_input_directory, "autoroute_input")
    node_path = os.path.dirname(os.path.realpath(__file__))
    autoroute_input_path = os.path.join(node_path, "autoroute_input")
    shp_out_raster = os.path.join(node_path, out_flood_raster_name)
    
    full_out_shapefile_name = ""
    if out_shapefile_name:
        full_out_shapefile_name = os.path.join(node_path, out_shapefile_name)
    
    run_AutoRoute(autoroute_executable_location,
                  autoroute_input_path,
                  shp_out_raster,
                  out_shapefile_name=full_out_shapefile_name,
                  delete_flood_raster=delete_flood_raster)
    

if __name__ == "__main__":   
    run_AutoRoute_HTCondor_directory(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])    
