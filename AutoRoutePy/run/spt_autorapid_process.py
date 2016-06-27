# -*- coding: utf-8 -*-
##
##  spt_autorapid_process.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License: BSD-3 Clause

from glob import glob
import os
GEOSERVER_ENABLED = False
try:
    from geoserver.catalog import FailedRequestError as geo_cat_FailedRequestError
    from .spt_dataset_manager.dataset_manager import GeoServerDatasetManager
    GEOSERVER_ENABLED = True
except ImportError:
    print("Geoserver functionality will not work. Need to pip install tethys_dataset_services to work.")
    pass

#local imports
from ..utilities import (case_insensitive_file_search, 
                        get_valid_watershed_list,
                        get_watershed_subbasin_from_folder)

#package imports
from .run_multiprocess import run_autoroute_multiprocess
from ..post.post_process import get_shapefile_layergroup_bounds, rename_shapefiles

#----------------------------------------------------------------------------------------
# MAIN PROCESS
#----------------------------------------------------------------------------------------
def run_spt_autorapid_process(autoroute_executable_location, #location of AutoRoute executable
                              autoroute_io_files_location, #path to AutoRoute input/output directory
                              rapid_io_files_location, #path to RAPID input/output directory
                              log_directory,
                              return_period_list=['return_period_20', 'return_period_10', 'return_period_2'],
                              delete_flood_raster=False,
                              generate_floodmap_shapefile=False,
                              geoserver_url='',
                              geoserver_username='',
                              geoserver_password='',
                              app_instance_id='',
                              num_cpus=-17
                              ):
    """
    This it the main AutoRoute-RAPID process for 
    generating historical flood maps and uploading to geoserver
    for the Streamflow Prediction Tool (SPT)
    """
    valid_return_period_list = ['max_flow', 'return_period_20', 'return_period_10', 'return_period_2']

    #validate return period list
    for return_period in return_period_list:
        if return_period not in valid_return_period_list:
            raise Exception("%s not a valid return period index ...")

    #loop through input watershed folders
    autoroute_input_folder = os.path.join(autoroute_io_files_location, "input")
    autoroute_output_folder = os.path.join(autoroute_io_files_location, "output")
    autoroute_input_directories = get_valid_watershed_list(autoroute_input_folder)

    for return_period in return_period_list:
        print "Running AutoRoute process for:", return_period
        #run autorapid for each watershed
        autoroute_watershed_jobs = {}
        for autoroute_input_directory in autoroute_input_directories:
            watershed, subbasin = get_watershed_subbasin_from_folder(autoroute_input_directory)
            
            #RAPID file paths
            master_watershed_rapid_input_directory = os.path.join(rapid_io_files_location, "input", autoroute_input_directory)
                                                                   
            if not os.path.exists(master_watershed_rapid_input_directory):
                print "AutoRoute watershed", autoroute_input_directory, "not in RAPID IO folder. Skipping ..."
                continue
            try:
                return_period_file=case_insensitive_file_search(master_watershed_rapid_input_directory, r'return_period.*?\.nc')
            except Exception:
                print "AutoRoute watershed", autoroute_input_directory, "missing return period file. Skipping ..."
                continue
            
            #setup the output location
            master_watershed_autoroute_output_directory = os.path.join(autoroute_output_folder,
                                                                       autoroute_input_directory, 
                                                                       return_period)
            try:
                os.makedirs(master_watershed_autoroute_output_directory)
            except OSError:
                pass
            #loop through sub-directories
            autoroute_watershed_directory_path = os.path.join(autoroute_input_folder, autoroute_input_directory)        
            autoroute_watershed_jobs[autoroute_input_directory] = run_autoroute_multiprocess(autoroute_executable_location, 
                                                                                             autoroute_input_directory=autoroute_watershed_directory_path, 
                                                                                             autoroute_output_directory=master_watershed_autoroute_output_directory,
                                                                                             log_directory=log_directory,
                                                                                             return_period=return_period, 
                                                                                             return_period_file=return_period_file, 
                                                                                             mode="multiprocess", 
                                                                                             delete_flood_raster=delete_flood_raster, 
                                                                                             generate_floodmap_shapefile=generate_floodmap_shapefile,
                                                                                             wait_for_all_processes_to_finish=False,
                                                                                             num_cpus=num_cpus
                                                                                             )
    geoserver_manager = None
    if GEOSERVER_ENABLED and geoserver_url and geoserver_username \
        and geoserver_password and app_instance_id and generate_floodmap_shapefile:
        try:
            geoserver_manager = GeoServerDatasetManager(geoserver_url, 
                                                        geoserver_username, 
                                                        geoserver_password, 
                                                        app_instance_id)
        except Exception as ex:
            print ex
            print "Skipping geoserver upload ..."
            geoserver_manager = None
            pass
    else:
        print "GeoServer parameters incomplete. Skipping upload ..."
        
    #wait for jobs to finish by watershed
    for autoroute_watershed_directory, autoroute_watershed_job in autoroute_watershed_jobs.iteritems():
        master_watershed_autoroute_output_directory = os.path.join(autoroute_output_folder,
                                                                   autoroute_watershed_directory, 
                                                                   return_period)
        #time stamped layer name
        geoserver_layer_group_name = "%s-floodmap-%s" % (autoroute_watershed_directory, 
                                                         return_period)
        geoserver_resource_list = []
        upload_shapefile_list = []
        for job_index, job_output in enumerate(autoroute_watershed_job['multiprocess_worker_list']):
            #upload to GeoServer
            if geoserver_manager and job_output[1]:
                #time stamped layer name
                geoserver_resource_name = "%s-%s" % (geoserver_layer_group_name,
                                                     job_index)
                #upload each shapefile
                upload_shapefile = os.path.join(master_watershed_autoroute_output_directory, 
                                                "%s%s" % (geoserver_resource_name, ".shp"))
                #rename files
                rename_shapefiles(master_watershed_autoroute_output_directory, 
                                  os.path.splitext(upload_shapefile)[0], 
                                  os.path.splitext(os.path.basename(job_output[1]))[0])
                                  
                if os.path.exists(upload_shapefile):
                    upload_shapefile_list.append(upload_shapefile)
                    print "Uploading", upload_shapefile, "to GeoServer as", geoserver_resource_name
                    shapefile_basename = os.path.splitext(upload_shapefile)[0]
                    #remove past layer if exists
                    #geoserver_manager.purge_remove_geoserver_layer(geoserver_manager.get_layer_name(geoserver_resource_name))
                    
                    #upload updated layer
                    shapefile_list = glob("%s*" % shapefile_basename)
                    #Note: Added try, except statement because the request search fails when the app
                    #deletes the layer after request is made (happens hourly), so the process may throw
                    #an exception even though it was successful.
                    """
                    ...
                      File "/home/alan/work/scripts/spt_ecmwf_autorapid_process/spt_dataset_manager/dataset_manager.py", line 798, in upload_shapefile
                        overwrite=True)
                      File "/usr/lib/tethys/local/lib/python2.7/site-packages/tethys_dataset_services/engines/geoserver_engine.py", line 1288, in create_shapefile_resource
                        new_resource = catalog.get_resource(name=name, workspace=workspace)
                      File "/usr/lib/tethys/local/lib/python2.7/site-packages/geoserver/catalog.py", line 616, in get_resource
                        resource = self.get_resource(name, store)
                      File "/usr/lib/tethys/local/lib/python2.7/site-packages/geoserver/catalog.py", line 606, in get_resource
                        candidates = [s for s in self.get_resources(store) if s.name == name]
                      File "/usr/lib/tethys/local/lib/python2.7/site-packages/geoserver/catalog.py", line 645, in get_resources
                        return store.get_resources()
                      File "/usr/lib/tethys/local/lib/python2.7/site-packages/geoserver/store.py", line 58, in get_resources
                        xml = self.catalog.get_xml(res_url)
                      File "/usr/lib/tethys/local/lib/python2.7/site-packages/geoserver/catalog.py", line 188, in get_xml
                        raise FailedRequestError("Tried to make a GET request to %s but got a %d status code: \n%s" % (rest_url, response.status, content))
                    geoserver.catalog.FailedRequestError: ...
                    """
                    try:
                        geoserver_manager.upload_shapefile(geoserver_resource_name, 
                                                           shapefile_list)
                    except geo_cat_FailedRequestError as ex:
                        print ex
                        print "Most likely OK, but always wise to check ..."
                        pass
                                                       
                    geoserver_resource_list.append(geoserver_manager.get_layer_name(geoserver_resource_name))
                    #TODO: Upload to CKAN for history of predicted floodmaps?
                else:
                    print upload_shapefile, "not found. Skipping upload to GeoServer ..."
        
        if geoserver_manager and geoserver_resource_list:
            print "Creating Layer Group:", geoserver_layer_group_name
            style_list = ['green' for i in range(len(geoserver_resource_list))]
            bounds = get_shapefile_layergroup_bounds(upload_shapefile_list)
            geoserver_manager.dataset_engine.create_layer_group(layer_group_id=geoserver_manager.get_layer_name(geoserver_layer_group_name), 
                                                                layers=tuple(geoserver_resource_list), 
                                                                styles=tuple(style_list),
                                                                bounds=tuple(bounds))
            #remove local shapefile when done
            for upload_shapefile in upload_shapefile_list:
                shapefile_parts = glob("%s*" % os.path.splitext(upload_shapefile)[0])
                for shapefile_part in shapefile_parts:
                    try:
                        os.remove(shapefile_part)
                    except OSError:
                        pass
                    
            #remove local directories when done
            try:
                os.rmdir(master_watershed_autoroute_output_directory)
            except OSError:
                pass
"""
##EXAMPLE
if __name__ == "__main__":
    run_autorapid_process(autoroute_executable_location='/home/alan/work/scripts/AutoRoute/source_code/autoroute',
                          autoroute_io_files_location='/home/alan/work/autoroute-io',
                          rapid_io_files_location='/home/alan/work/rapid-io',
                          return_period_list=['max_flow'],
                          delete_flood_raster=True,
                          generate_floodmap_shapefile=True,
                          )
"""
