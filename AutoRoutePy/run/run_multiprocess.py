# -*- coding: utf-8 -*-
##
##  run_multiprocess.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License BSD 3-Clause

from datetime import datetime
import multiprocessing
import os

HTCONDOR_ENABLED = False
try:
    from condorpy import Job as CJob
    from condorpy import Templates as tmplt
    HTCONDOR_ENABLED = True
except ImportError:
    print "condorpy unable to be imported. If you would like to use HTCondor", \
          "mode, please install condorpy (i.e. pip install condorpy)."
    pass

#local imports
from ..utilities import (CaptureStdOutToLog, 
                        case_insensitive_file_search, 
                        get_valid_num_cpus)
from .worker_multiprocess import run_AutoRoute
from ..prepare.prepare_multiprocess import (get_valid_streamflow_prepare_mode,
                                            prepare_autoroute_streamflow_multiprocess_worker)

#----------------------------------------------------------------------------------------
# MULTIPROCESS FUNCTIONS
#----------------------------------------------------------------------------------------
def run_autoroute_multiprocess_worker(args):
    """
    Run autoroute on one of multiple cores
    """
    job_name = args[7]
    log_directory = args[8]
    log_file_path = os.path.join(log_directory, "{0}-{1}.log".format(job_name, datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    with CaptureStdOutToLog(log_file_path):
        run_AutoRoute(autoroute_executable_location=args[0],
                      autoroute_manager=args[1],
                      autoroute_input_path=args[2],
                      out_flood_map_raster_name=args[3],
                      out_flood_depth_raster_name=args[4],
                      out_shapefile_name=args[5],
                      delete_flood_raster=args[6])
        
    return args[2], args[3], args[4], job_name

#----------------------------------------------------------------------------------------
# MAIN PROCESS
#----------------------------------------------------------------------------------------
def run_autoroute_multiprocess(autoroute_input_directory, #path to AutoRoute input directory
                               autoroute_output_directory, #path to AutoRoute output directory
                               log_directory, #path to HTCondor/multiprocessing logs
                               autoroute_executable_location="", #location of AutoRoute executable
                               autoroute_manager=None, #AutoRoute manager with default parameters
                               rapid_output_directory="", #path to ECMWF RAPID input/output directory
                               return_period="", # return period name in return period file
                               return_period_file="", # return period file generated from RAPID historical run
                               rapid_output_file="", #path to RAPID output file to be used
                               date_peak_search_start=None, #datetime of start of search for peakflow
                               date_peak_search_end=None, #datetime of end of search for peakflow
                               river_id="", #field with unique identifier of river
                               streamflow_id="", #field with streamflow
                               stream_network_shapefile="", #stream network shapefile
                               mode="multiprocess", #multiprocess or htcondor 
                               generate_flood_map_raster=True, #generate flood raster
                               generate_flood_depth_raster=False, #generate flood raster
                               generate_flood_map_shapefile=False, #generate a flood map shapefile
                               wait_for_all_processes_to_finish=True, #waits for all processes to finish before ending script
                               num_cpus=-17 #number of processes to use on computer
                               ):
    """
    This it the main AutoRoute-RAPID process
    """
    time_start_all = datetime.utcnow()
    if not generate_flood_depth_raster and not generate_flood_map_raster and not generate_flood_map_shapefile:
        raise Exception("ERROR: Must set generate_flood_depth_raster, generate_flood_map_raster, or generate_flood_map_shapefile to True to proceed ...")
        
    #--------------------------------------------------------------------------
    #Validate Inputs
    #--------------------------------------------------------------------------
    valid_mode_list = ['multiprocess','htcondor']
    if mode not in valid_mode_list:
        raise Exception("ERROR: Invalid multiprocess mode {}. Only multiprocess or htcondor allowed ...".format(mode))
        
    if mode == "htcondor" and not HTCONDOR_ENABLED:
        raise Exception("ERROR: HTCondor mode not allowed. Must have condorpy and HTCondor installed to work ...".format(mode))
        
    #DETERMINE MODE TO PREPARE STREAMFLOW
    PREPARE_MODE = get_valid_streamflow_prepare_mode(autoroute_input_directory,
                                                     rapid_output_directory,
                                                     return_period,
                                                     return_period_file,
                                                     rapid_output_file,
                                                     river_id,
                                                     streamflow_id,
                                                     stream_network_shapefile,
                                                     )    
    #--------------------------------------------------------------------------
    #Initialize Run
    #--------------------------------------------------------------------------
    try:
        os.makedirs(autoroute_output_directory)
    except OSError:
        pass
    
    local_scripts_location = os.path.dirname(os.path.realpath(__file__))

    #initialize HTCondor/multiprocess log directories
    prepare_log_directory = os.path.join(log_directory, "prepare")
    try:
        os.makedirs(prepare_log_directory)
    except OSError:
        pass
    if PREPARE_MODE > 0:
        print("Streamflow preparation logs can be found here: {0}".format(prepare_log_directory))
        
    run_log_directory = os.path.join(log_directory, "run")
    try:
        os.makedirs(run_log_directory)
    except OSError:
        pass
    print("AutoRoute simulation logs can be found here: {0}".format(run_log_directory))

    #keep list of jobs
    autoroute_job_info = {
                            'multiprocess_job_list': [],
                            'htcondor_job_list': [],
                            'htcondor_job_info': [],
                            'output_folder': autoroute_output_directory,
                           }
                           
    if mode == "multiprocess":
        num_cpus = get_valid_num_cpus(num_cpus)                    
        #start pool
        pool_streamflow = multiprocessing.Pool(num_cpus)
        pool_main = multiprocessing.Pool(num_cpus)

    #--------------------------------------------------------------------------
    #Run the model
    #--------------------------------------------------------------------------
    #loop through sub-directories
    streamflow_job_list = []
    for directory in os.listdir(autoroute_input_directory):
        master_watershed_autoroute_input_directory = os.path.join(autoroute_input_directory, directory)
        if os.path.isdir(master_watershed_autoroute_input_directory):
            autoroute_watershed_name = os.path.basename(autoroute_input_directory)
            autoroute_job_name = "{0}-{1}".format(autoroute_watershed_name, directory)
            
            try:
                case_insensitive_file_search(master_watershed_autoroute_input_directory, r'elevation\.(?!prj)')
            except Exception:
                try:
                    case_insensitive_file_search(os.path.join(master_watershed_autoroute_input_directory, 'elevation'), r'hdr\.adf')
                except Exception:
                    print("ERROR: Elevation raster not found. Skipping run ...")
                    continue
                    pass
                pass
            
            try:
                stream_info_file = case_insensitive_file_search(master_watershed_autoroute_input_directory,
                                                                r'stream_info\.txt')
            except Exception:
                print("Stream info file not found. Skipping run ...")
                continue
                pass

            if PREPARE_MODE > 0:
                streamflow_job_list.append((PREPARE_MODE,
                                            master_watershed_autoroute_input_directory,
                                            stream_info_file,
                                            rapid_output_directory,
                                            return_period_file,
                                            return_period,
                                            rapid_output_file,
                                            date_peak_search_start,
                                            date_peak_search_end,
                                            river_id,
                                            streamflow_id,
                                            stream_network_shapefile,
                                            autoroute_job_name,
                                            prepare_log_directory,
                                            ))
            
            output_shapefile_base_name = '{0}_{1}'.format(autoroute_watershed_name, directory)
            #set up flood raster name
            output_flood_map_raster_name = 'flood_map_raster_{0}.tif'.format(output_shapefile_base_name)
            master_output_flood_map_raster_name = os.path.join(autoroute_output_directory, output_flood_map_raster_name)
            #set up flood raster name
            output_flood_depth_raster_name = 'flood_depth_raster_{0}.tif'.format(output_shapefile_base_name)
            master_output_flood_depth_raster_name = os.path.join(autoroute_output_directory, output_flood_depth_raster_name)
            #set up flood shapefile name
            output_shapefile_shp_name = '{0}.shp'.format(output_shapefile_base_name)
            master_output_shapefile_shp_name = os.path.join(autoroute_output_directory, output_shapefile_shp_name)

            delete_flood_map_raster = False
            if not generate_flood_map_shapefile:
                master_output_shapefile_shp_name = ""
            else:
                if not generate_flood_map_raster:
                    generate_flood_map_raster = True
                    delete_flood_map_raster = True
                
            if not generate_flood_map_raster:
                master_output_flood_map_raster_name = ""

            if not generate_flood_depth_raster:
                master_output_flood_depth_raster_name = ""

            if mode == "htcondor":
                #create job to run autoroute for each raster in watershed
                job = CJob('job_autoroute_{0}_{1}'.format(os.path.basename(autoroute_input_directory), directory), tmplt.vanilla_transfer_files)
                

                if generate_flood_map_shapefile:
                    #setup additional floodmap shapfile names
                    output_shapefile_shx_name = '{0}.shx'.format(output_shapefile_base_name)
                    master_output_shapefile_shx_name = os.path.join(autoroute_output_directory, output_shapefile_shx_name)
                    output_shapefile_prj_name = '{0}.prj'.format(output_shapefile_base_name)
                    master_output_shapefile_prj_name = os.path.join(autoroute_output_directory, output_shapefile_prj_name)
                    output_shapefile_dbf_name = '{0}.dbf'.format(output_shapefile_base_name)
                    master_output_shapefile_dbf_name = os.path.join(autoroute_output_directory, output_shapefile_dbf_name)
                
                    transfer_output_remaps = "{0} = {1}; {2} = {3}; {4} = {5};" \
                                             " {6} = {7}; {8} = {9}".format(output_shapefile_shp_name, 
                                                                            master_output_shapefile_shp_name,
                                                                            output_shapefile_shx_name,
                                                                            master_output_shapefile_shx_name,
                                                                            output_shapefile_prj_name,
                                                                            master_output_shapefile_prj_name,
                                                                            output_shapefile_dbf_name,
                                                                            master_output_shapefile_dbf_name,
                                                                            output_flood_map_raster_name,
                                                                            master_output_flood_map_raster_name)
                    
                    if generate_flood_depth_raster:
                        transfer_output_remaps += "; {0} = {1}".format(output_flood_depth_raster_name, 
                                                                       master_output_flood_depth_raster_name)
                else:
                    output_shapefile_shp_name = ""
                    transfer_output_remaps = ""
                    if generate_flood_map_raster:
                        transfer_output_remaps = "{0} = {1}".format(output_flood_map_raster_name, 
                                                                    master_output_flood_map_raster_name)
                    if generate_flood_depth_raster:
                        if transfer_output_remaps:
                            transfer_output_remaps += "; "
                            
                        transfer_output_remaps += "{0} = {1}".format(output_flood_depth_raster_name, 
                                                                     master_output_flood_depth_raster_name)
                                                                     
                job.set('transfer_output_remaps',"\"{0}\"" .format(transfer_output_remaps))
                                                                      
                job.set('executable', os.path.join(local_scripts_location,'multicore_worker_process.py'))
                job.set('transfer_input_files', "{0}".format(master_watershed_autoroute_input_directory))
                job.set('initialdir', run_log_directory)
                    
                job.set('arguments', '{0} {1} {2} {3} {4} {5} {6}' % (autoroute_executable_location,
                                                                      autoroute_manager,
                                                                      directory,
                                                                      output_flood_map_raster_name,
                                                                      output_flood_depth_raster_name,
                                                                      output_shapefile_shp_name,
                                                                      delete_flood_map_raster))
                                                              
                autoroute_job_info['htcondor_job_list'].append(job)
                autoroute_job_info['htcondor_job_info'].append({ 'output_shapefile_base_name': output_shapefile_base_name,
                                                                 'autoroute_job_name': autoroute_job_name})

            else: #mode == "multiprocess":
                autoroute_job_info['multiprocess_job_list'].append((autoroute_executable_location,
                                                                    autoroute_manager,
                                                                    master_watershed_autoroute_input_directory,
                                                                    master_output_flood_map_raster_name,
                                                                    master_output_flood_depth_raster_name,
                                                                    master_output_shapefile_shp_name,
                                                                    delete_flood_map_raster,
                                                                    autoroute_job_name,
                                                                    run_log_directory
                                                                    ))
                #For testing function serially
                """
                run_autoroute_multiprocess_worker((autoroute_executable_location,
                                                   autoroute_manager,
                                                   master_watershed_autoroute_input_directory,
                                                   master_output_flood_map_raster_name,
                                                   master_output_flood_depth_raster_name,
                                                   master_output_shapefile_shp_name,
                                                   delete_flood_map_raster,
                                                   autoroute_job_name,
                                                   run_log_directory))
                """
    if PREPARE_MODE > 0:
        #generate streamflow
        streamflow_job_list = pool_streamflow.imap_unordered(prepare_autoroute_streamflow_multiprocess_worker,
                                                             streamflow_job_list,
                                                             chunksize=1)
        for streamflow_job_output in streamflow_job_list:
            print("STREAMFLOW READY: {0}".format(streamflow_job_output))
        pool_streamflow.close()
        pool_streamflow.join()
        
    print("Running AutoRoute simulations ...")
    #submit jobs to run
    if mode == "multiprocess":
        autoroute_job_info['multiprocess_worker_list'] = pool_main.imap_unordered(run_autoroute_multiprocess_worker, 
                                                                                 autoroute_job_info['multiprocess_job_list'], 
                                                                                 chunksize=1)
    else:
        for htcondor_job in autoroute_job_info['htcondor_job_list']:
            htcondor_job.submit()

    if wait_for_all_processes_to_finish:
        #wait for all of the jobs to complete
        if mode == "multiprocess":
            for multi_job_output in autoroute_job_info['multiprocess_worker_list']:
                print("JOB FINISHED: {0}".format(multi_job_output[3]))
            #just in case ...
            pool_main.close()
            pool_main.join()
        else:
            for htcondor_job_index, htcondor_job in enumerate(autoroute_job_info['htcondor_job_list']):
                htcondor_job.wait()
                print("JOB FINISHED: {0}".format(autoroute_job_info['htcondor_job_info'][htcondor_job_index]['autoroute_job_name']))
    
        print("Time to complete entire AutoRoute process: {0}".format(datetime.utcnow()-time_start_all))
    else:       
        return autoroute_job_info

