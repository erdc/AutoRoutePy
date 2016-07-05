# -*- coding: utf-8 -*-
##
##  worker_multiprocess.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License BSD 3-Clause

import os
import sys

#local imports
from ..autoroute import AutoRoute 
from ..utilities import case_insensitive_file_search

#------------------------------------------------------------------------------
#MAIN PROCESS
#------------------------------------------------------------------------------
def run_AutoRoute(autoroute_executable_location,
                  autoroute_manager,
                  autoroute_input_path,
                  out_flood_map_raster_name,
                  out_flood_depth_raster_name,
                  out_shapefile_name="",
                  delete_flood_raster=False):
                      
    """
    Run AutoRoute with searching for inputs in directory
    """
    #change working directory for python (this is for the input file produced to
    # prevent overwriting)
    os.chdir(autoroute_input_path)
    
    if not autoroute_manager:
        autoroute_manager = AutoRoute(autoroute_executable_location)

    valid_raster_extensions = "asc|bmp|dt2|img|jp2|j2c|j2k|jpeg|jpg2|jpg|png|tif|tiff"
    
    #get the raster for elevation    
    try:
        elevation_raster = case_insensitive_file_search(autoroute_input_path, r'elevation\.(?:{})'.format(valid_raster_extensions))
    except IndexError:
        try:
            elevation_raster = case_insensitive_file_search(os.path.join(autoroute_input_path, 'elevation'), r'hdr\.adf')
        except IndexError:
            print "Elevation raster not found. Skipping entire process ..."
            raise
        pass

    #get the manning n raster
    try:
        manning_n_raster = case_insensitive_file_search(autoroute_input_path, r'manning_n\.(?:{})'.format(valid_raster_extensions))
    except IndexError:
        manning_n_raster = ""
        print "Manning n raster not found. Ignoring this file ..."
        pass

    #autoroute input file
    try:
        autoroute_input_file = case_insensitive_file_search(autoroute_input_path, r'AUTOROUTE_INPUT_FILE\.TXT')
        autoroute_manager.update_input_file(autoroute_input_file)
    except IndexError:
        print "AUTOROUTE_INPUT_FILE.txt not found. Ignoring this file ..."
        pass

        
    autoroute_manager.update_parameters(dem_raster_file_path=elevation_raster,
                                        stream_info_file_path=case_insensitive_file_search(autoroute_input_path, r'stream_info\.txt'),
                                        out_flood_map_raster_path=out_flood_map_raster_name,
                                        out_flood_depth_raster_path=out_flood_depth_raster_name,
                                        out_flood_map_shapefile_path=out_shapefile_name,
                                        manning_n_raster_file_path=manning_n_raster
                                        )
                         
    autoroute_manager.run_autoroute()

    if delete_flood_raster:
        try:
            os.remove(out_flood_map_raster_name)
            os.remove("%s.prj" % os.path.splitext(out_flood_map_raster_name)[0])
        except OSError:
            pass
    
def run_AutoRoute_HTCondor_directory(autoroute_executable_location,
                                     autoroute_manager,
                                     autoroute_input_directory,
                                     out_flood_map_raster_name,
                                     out_flood_depth_raster_name,
                                     out_shapefile_name="",
                                     delete_flood_raster=False):
    """
    Run AutoRoute in HTCondor execute directory
    """
    os.rename(autoroute_input_directory, "autoroute_input")
    node_path = os.path.dirname(os.path.realpath(__file__))
    autoroute_input_path = os.path.join(node_path, "autoroute_input")
    out_flood_map_raster = os.path.join(node_path, out_flood_map_raster_name)
    out_flood_depth_raster = os.path.join(node_path, out_flood_depth_raster_name)
    
    full_out_shapefile_name = ""
    if out_shapefile_name:
        full_out_shapefile_name = os.path.join(node_path, out_shapefile_name)
    
    run_AutoRoute(autoroute_executable_location,
                  autoroute_manager,
                  autoroute_input_path,
                  out_flood_map_raster,
                  out_flood_depth_raster,
                  out_shapefile_name=full_out_shapefile_name,
                  delete_flood_raster=delete_flood_raster)
    

if __name__ == "__main__":   
    run_AutoRoute_HTCondor_directory(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])    
