# -*- coding: utf-8 -*-
##
##  run_autoroute_multicore.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##
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

##try:
##    from psutil import virtual_memory
##except ImportError:
##    print "psutil unable to be imported. If you would like to use multiprocessing", \
##          "mode, please install psutil (i.e. pip install psutil)."
##    pass

from datetime import datetime

#local imports
from helper_functions import case_insensitive_file_search
from multicore_worker_process import run_AutoRoute

#package imports
from autoroute_prepare import AutoRoutePrepare 

#----------------------------------------------------------------------------------------
# MULTIPROCESS FUNCTION
#----------------------------------------------------------------------------------------
def run_autoroute_multiprocess_worker(args):
    """
    Run autoroute on one of multiple cores
    """
    try:
        run_AutoRoute(autoroute_executable_location=args[0],
                      autoroute_input_path=args[1],
                      out_flood_raster_name=args[2],
                      out_shapefile_name=args[3],
                      delete_flood_raster=args[4])
    except Exception as ex:
        print ex
        
    return args[2], args[3]
                  
#----------------------------------------------------------------------------------------
# MAIN PROCESS
#----------------------------------------------------------------------------------------
def run_autoroute_multicore(autoroute_executable_location, #location of AutoRoute executable
                            autoroute_input_directory, #path to AutoRoute input directory
                            autoroute_output_directory, #path to AutoRoute output directory
                            rapid_output_directory="", #path to ECMWF RAPID input/output directory
                            return_period="", # return period name in return period file
                            return_period_file="", # return period file generated from RAPID historical run
                            rapid_output_file="", #path to RAPID output file to be used
                            condor_log_directory="", #path to HTCondor logs
                            mode="multiprocess", #multiprocess or htcondor 
                            delete_flood_raster=True, #delete flood raster generated
                            generate_floodmap_shapefile=True, #generate a flood map shapefile
                            wait_for_all_processes_to_finish=True,
                            num_cpus=-17
                            ):
    """
    This it the main AutoRoute-RAPID process
    """
    time_start_all = datetime.utcnow()
    #--------------------------------------------------------------------------
    #Validate Inputs
    #--------------------------------------------------------------------------
    valid_mode_list = ['multiprocess','htcondor']
    if mode not in valid_mode_list:
        raise Exception("ERROR: Invalid multiprocess mode {}. Only multiprocess or htcondor allowed ...".format(mode))
        
    if mode == "htcondor" and not HTCONDOR_ENABLED:
        raise Exception("ERROR: HTCondor mode not allowed. Must have condorpy and HTCondor installed to work ...".format(mode))
        

    RUN_CASE = 0
    #case 0: run as is - don't generate inputs
    if not os.path.exists(autoroute_input_directory):
        raise Exception("ERROR: AutoRoute watershed {} directory does not exist ...".format(autoroute_input_directory))

    #case 1: generate inputs from ECMWF output
    if rapid_output_directory:
        RUN_CASE = 1
        if not os.path.exists(rapid_output_directory):
            raise Exception("ERROR: AutoRoute watershed {} missing RAPID forecast folder ...".format(autoroute_input_directory))

        print "Running in mode", RUN_CASE, ". Generating input from ECMWF-RAPID output ..."
    
    #case 2: generate inputs from return period file
    valid_return_period_list = ['return_period_20', 'return_period_10', 'return_period_2']

    if return_period:
        if RUN_CASE > 0:
            raise Exception("ERROR: Cannon run more than one mode for AutoRoute process ...")

        RUN_CASE = 2
        if return_period not in valid_return_period_list:
            raise Exception("ERROR: AutoRoute watershed {0} has invalid return period ({1}) ...".format(autoroute_input_directory,
                                                                                                        return_period))
        
        if not return_period_file or not os.path.exists(return_period_file):
            raise Exception("ERROR: AutoRoute watershed {} is missing return period file ...".format(autoroute_input_directory))

        print "Running in mode", RUN_CASE, ". Generating input from return period file (", return_period, ") ..."
        
    #case 3: generate inputs from peaks of single rapid output
    if rapid_output_file:
        if RUN_CASE > 0:
            raise Exception("ERROR: Cannon run more than one mode for AutoRoute process ...")

        RUN_CASE = 3
        if not os.path.exists(rapid_output_file):
            raise Exception("ERROR: AutoRoute watershed {} missing RAPID output file ...".format(autoroute_input_directory))

        print "Running in mode", RUN_CASE, ". Generating input from RAPID output file (", rapid_output_file, ") ..."
    
    
    #--------------------------------------------------------------------------
    #Initialize Run
    #--------------------------------------------------------------------------
    try:
        os.makedirs(autoroute_output_directory)
    except OSError:
        pass
    
    local_scripts_location = os.path.dirname(os.path.realpath(__file__))

    #initialize HTCondor Directory
    try:
        os.makedirs(condor_log_directory)
    except OSError:
        pass

    #keep list of jobs
    autoroute_job_info = {
                            'multiprocess_job_list': [],
                            'htcondor_job_list': [],
                            'htcondor_job_info': [],
                            'output_folder': autoroute_output_directory,
                           }

    pool = None
    if mode == "multiprocess":
        #set number of cpus to use (recommended 8 GB per cpu)
        total_cpus = multiprocessing.cpu_count()
##        mem = virtual_memory()
##        recommended_max_num_cpus = max(1, int(mem.total  * 1e-9 / 8))
        if num_cpus <= 0:
            num_cpus = total_cpus
##            num_cpus = min(recommended_max_num_cpus, total_cpus)
        if num_cpus > total_cpus:
            num_cpus = total_cpus
            print "Number of cores entered is greater then available cpus. Using all avalable cpus ..."
##        if num_cpus > recommended_max_num_cpus:
##            print "WARNING: Number of cpus allotted (", num_cpus , ") exceeds maximum recommended (", \
##                    recommended_max_num_cpus, "). This may cause memory issues ..."
        #start pool
        pool = multiprocessing.Pool(num_cpus)


    #--------------------------------------------------------------------------
    #Run the model
    #--------------------------------------------------------------------------
    #loop through sub-directories
    for directory in os.listdir(autoroute_input_directory):
        master_watershed_autoroute_input_directory = os.path.join(autoroute_input_directory, directory)
        if os.path.isdir(master_watershed_autoroute_input_directory):
            autoroute_job_name = os.path.basename(autoroute_input_directory)
            print "Running AutoRoute for watershed:", autoroute_job_name, "sub directory:", directory
            
            if RUN_CASE > 0:
                #create input streamflow raster for AutoRoute
                try:
                    elevation_raster = case_insensitive_file_search(master_watershed_autoroute_input_directory, r'elevation\.(?!prj)')
                except Exception:
                    try:
                        elevation_raster = case_insensitive_file_search(os.path.join(master_watershed_autoroute_input_directory, 'elevation'), r'hdr\.adf')
                    except Exception:
                        print "Elevation raster not found. Skipping run ..."
                        continue
                        pass
                    pass
                
                try:
                    stream_info_file = case_insensitive_file_search(master_watershed_autoroute_input_directory,
                                                                    r'stream_info\.txt')
                except Exception:
                    print "Stream info file not found. Skipping run ..."
                    continue
                    pass
                
                arp = AutoRoutePrepare(autoroute_executable_location,
                                       elevation_raster)
                if RUN_CASE == 1:
                    arp.append_streamflow_from_ecmwf_rapid_output(stream_info_file=stream_info_file,
                                                                  prediction_folder=rapid_output_directory,
                                                                  method_x="mean_plus_std", method_y="max")
                elif RUN_CASE == 2:
                    arp.append_streamflow_from_return_period_file(stream_info_file=stream_info_file,
                                                                  return_period_file=return_period_file,
                                                                  return_period=return_period)
                elif RUN_CASE == 3:
                    arp.append_streamflow_from_rapid_output(stream_info_file=stream_info_file,
                                                            rapid_output_file=rapid_output_file)
                    
            
            output_shapefile_base_name = '%s_%s' % (autoroute_job_name, directory)
            #set up flood raster name
            output_flood_raster_name = '%s_raster.tif' % output_shapefile_base_name
            master_output_flood_raster_name = os.path.join(autoroute_output_directory, output_flood_raster_name)
            #set up flood shapefile name
            output_shapefile_shp_name = '%s.shp' % output_shapefile_base_name
            master_output_shapefile_shp_name = os.path.join(autoroute_output_directory, output_shapefile_shp_name)

            if mode == "htcondor":
                #create job to run autoroute for each raster in watershed
                job = CJob('job_autoroute_%s_%s' % (os.path.basename(autoroute_input_directory), directory), tmplt.vanilla_transfer_files)
                

                if generate_floodmap_shapefile:
                    #setup additional floodmap shapfile names
                    output_shapefile_shx_name = '%s.shx' % output_shapefile_base_name
                    master_output_shapefile_shx_name = os.path.join(autoroute_output_directory, output_shapefile_shx_name)
                    output_shapefile_prj_name = '%s.prj' % output_shapefile_base_name
                    master_output_shapefile_prj_name = os.path.join(autoroute_output_directory, output_shapefile_prj_name)
                    output_shapefile_dbf_name = '%s.dbf' % output_shapefile_base_name
                    master_output_shapefile_dbf_name = os.path.join(autoroute_output_directory, output_shapefile_dbf_name)

                    job.set('transfer_output_remaps',"\"%s = %s; %s = %s; %s = %s;  %s = %s; %s = %s\"" % (output_shapefile_shp_name, 
                                                                                                           master_output_shapefile_shp_name,
                                                                                                           output_shapefile_shx_name,
                                                                                                           master_output_shapefile_shx_name,
                                                                                                           output_shapefile_prj_name,
                                                                                                           master_output_shapefile_prj_name,
                                                                                                           output_shapefile_dbf_name,
                                                                                                           master_output_shapefile_dbf_name,
                                                                                                           output_flood_raster_name,
                                                                                                           master_output_flood_raster_name))
                
                else:
                    output_shapefile_shp_name = ""
                    job.set('transfer_output_remaps',"\"%s = %s\"" % (output_flood_raster_name,
                                                                      master_output_flood_raster_name))
                                                                      
                job.set('executable', os.path.join(local_scripts_location,'multicore_worker_process.py'))
                job.set('transfer_input_files', "%s" % (master_watershed_autoroute_input_directory))
                job.set('initialdir', condor_log_directory)
                    
                job.set('arguments', '%s %s %s %s %s' % (autoroute_executable_location,
                                                         directory,
                                                         output_flood_raster_name,
                                                         output_shapefile_shp_name,
                                                         delete_flood_raster))
                job.submit()
                autoroute_job_info['htcondor_job_list'].append(job)
                autoroute_job_info['htcondor_job_info'].append({ 'output_shapefile_base_name': output_shapefile_base_name })

            else: #mode == "multiprocess":
            
                if not generate_floodmap_shapefile:
                    master_output_shapefile_shp_name = ""

                autoroute_job_info['multiprocess_job_list'].append((autoroute_executable_location,
                                                                    master_watershed_autoroute_input_directory,
                                                                    master_output_flood_raster_name,
                                                                    master_output_shapefile_shp_name,
                                                                    delete_flood_raster))
                """
                #For testing function serially
                run_autoroute_multiprocess_worker((autoroute_executable_location,
                                                  master_watershed_autoroute_input_directory,
                                                  master_output_flood_raster_name,
                                                  master_output_shapefile_shp_name,
                                                  delete_flood_raster))
                """
    
    if mode == "multiprocess":
        autoroute_job_info['multiprocess_worker_list'] = pool.imap_unordered(run_autoroute_multiprocess_worker, 
                                                                             autoroute_job_info['multiprocess_job_list'], 
                                                                             chunksize=1)
            
    if wait_for_all_processes_to_finish:
        #wait for all of the jobs to complete
        if mode == "multiprocess":
            for multi_job_output in autoroute_job_info['multiprocess_worker_list']:
                print "READY:", multi_job_output[1]
            #just in case ...
            pool.close()
            pool.join()
        else:
            for htcondor_job_index, htcondor_job in enumerate(autoroute_job_info['htcondor_job_list']):
                htcondor_job.wait()
                print "READY:", autoroute_job_info['htcondor_job_info'][htcondor_job_index]['output_shapefile_base_name']
    
        print "Time to complete entire AutoRoute process:", datetime.utcnow()-time_start_all
        
    return autoroute_job_info
