#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##  multicore_worker_process.py
##  AutoRoutePy
##
##  Created by Alan D. Snow 2015.
##  Copyright © 2015 Alan D Snow. All rights reserved.
##
import os
import sys

#local imports
from AutoRoutePy.autoroute import AutoRoute 
from AutoRoutePy.helper_functions import case_insensitive_file_search


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
    #change working directory for python (this is for the input file produced to
    # prevent overwriting)
    os.chdir(autoroute_input_path)
    
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

    #get the manning n raster
    try:
        manning_n_raster = case_insensitive_file_search(autoroute_input_path, r'manning_n\.(?!prj)')
    except Exception:
        manning_n_raster = ""
        print "Manning n raster not found. Ignoring this file ..."
        pass

    #autoroute input file
    try:
        autoroute_input_file = case_insensitive_file_search(autoroute_input_path, r'AUTO_ROUTE_INPUT\.TXT')
    except Exception:
        try:
            autoroute_input_file = case_insensitive_file_search(autoroute_input_path, r'AUTOROUTE_INPUT\.TXT')
        except Exception:
            autoroute_input_file = ""
            print "AUTOROUTE_INPUT_FILE.txt not found. Ignoring this file ..."
            raise
        pass
    
    auto_mng = AutoRoute(autoroute_executable_location,
                         dem_raster_file_path=elevation_raster,
                         stream_info_file_path=case_insensitive_file_search(autoroute_input_path, r'stream_info\.txt'),
                         out_flood_map_raster_path=out_flood_raster_name,
                         manning_n_raster_file_path=manning_n_raster
                         )
                         
    if out_shapefile_name:             
        auto_mng.update_parameters(out_flood_map_shapefile_path=out_shapefile_name)
        
    auto_mng.run_autoroute(autoroute_input_file)

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
    out_flood_raster = os.path.join(node_path, out_flood_raster_name)
    
    full_out_shapefile_name = ""
    if out_shapefile_name:
        full_out_shapefile_name = os.path.join(node_path, out_shapefile_name)
    
    run_AutoRoute(autoroute_executable_location,
                  autoroute_input_path,
                  out_flood_raster,
                  out_shapefile_name=full_out_shapefile_name,
                  delete_flood_raster=delete_flood_raster)
    

if __name__ == "__main__":   
    run_AutoRoute_HTCondor_directory(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])    
