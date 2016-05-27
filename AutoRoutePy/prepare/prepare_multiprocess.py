from glob import glob
from datetime import datetime
import multiprocessing
import os

#local imports
from ..prepare import AutoRoutePrepare
from ..utilities import CaptureStdOutToLog, get_valid_num_cpus

#----------------------------------------------------------------------------------
#MULTIPROCESSING FUNCTIONS
#----------------------------------------------------------------------------------
def get_valid_streamflow_prepare_mode(autoroute_input_directory,
                                      rapid_output_directory,
                                      return_period,
                                      return_period_file,
                                      rapid_output_file
                                      ):
    """
    Determines valid mode to run for streamflor prepare
    """
    
    PREPARE_MODE = 0
    #case 0: run as is - don't generate inputs
    if not os.path.exists(autoroute_input_directory):
        raise Exception("ERROR: AutoRoute watershed {} directory does not exist ...".format(autoroute_input_directory))

    #case 1: generate inputs from ECMWF output
    if rapid_output_directory:
        PREPARE_MODE = 1
        if not os.path.exists(rapid_output_directory):
            raise Exception("ERROR: AutoRoute watershed {} missing RAPID forecast folder ...".format(autoroute_input_directory))

        print("Running in mode {0}. Generating input from ECMWF-RAPID output ...".format(PREPARE_MODE))
    
    #case 2: generate inputs from return period file
    if return_period:
        if PREPARE_MODE > 0:
            raise Exception("ERROR: Cannon run more than one mode for AutoRoute process ...")

        PREPARE_MODE = 2
        valid_return_period_list = ['max_flow', 'return_period_20', 'return_period_10', 'return_period_2']
        if return_period not in valid_return_period_list:
            raise Exception("ERROR: AutoRoute watershed {0} has invalid return period ({1}) ...".format(autoroute_input_directory,
                                                                                                        return_period))
        
        if not return_period_file or not os.path.exists(return_period_file):
            raise Exception("ERROR: AutoRoute watershed {} is missing return period file ...".format(autoroute_input_directory))

        print("Running in mode {0}. Generating input from return period file ({1}) ...".format(PREPARE_MODE, return_period))
        
    #case 3: generate inputs from peaks of single rapid output
    if rapid_output_file:
        if PREPARE_MODE > 0:
            raise Exception("ERROR: Cannon run more than one mode for AutoRoute process ...")

        PREPARE_MODE = 3
        if not os.path.exists(rapid_output_file):
            raise Exception("ERROR: AutoRoute watershed {} missing RAPID output file ...".format(autoroute_input_directory))

        print("Running in mode {0}. Generating input from RAPID output file ({1}) ...".format(PREPARE_MODE, rapid_output_file))
        
    return PREPARE_MODE
    
def prepare_autoroute_streamflow_single_folder(PREPARE_MODE,
                                               autoroute_input_directory,
                                               stream_info_file,
                                               rapid_output_directory,
                                               return_period_file,
                                               return_period,
                                               rapid_output_file,
                                               date_peak_search_start,
                                               date_peak_search_end
                                               ):
    """
    This function prepares streamflow inputs in single directory for AutoRoute
    """
    os.chdir(autoroute_input_directory)
    
    #create input streamflow raster for AutoRoute
    arp = AutoRoutePrepare("", "", stream_info_file)
    if PREPARE_MODE == 1:
        arp.append_streamflow_from_ecmwf_rapid_output(prediction_folder=rapid_output_directory,
                                                      method_x="mean_plus_std", method_y="max")
    elif PREPARE_MODE == 2:
        arp.append_streamflow_from_return_period_file(return_period_file=return_period_file,
                                                      return_period=return_period)
    elif PREPARE_MODE == 3:
        arp.append_streamflow_from_rapid_output(rapid_output_file=rapid_output_file,
                                                date_peak_search_start=date_peak_search_start,
                                                date_peak_search_end=date_peak_search_end)

def prepare_autoroute_streamflow_multiprocess_worker(args):
    """
    Prepare streamflow for AutoRoute simulation on one of multiple cores
    """
    job_name = args[9]
    log_directory = args[10]
    log_file_path = os.path.join(log_directory, "{0}-{1}.log".format(job_name, datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    with CaptureStdOutToLog(log_file_path):
        prepare_autoroute_streamflow_single_folder(args[0],
                                                   args[1],
                                                   args[2],
                                                   args[3],
                                                   args[4],
                                                   args[5],
                                                   args[6],
                                                   args[7],
                                                   args[8],
                                                   )
    return job_name

def prepare_autoroute_single_folder(sub_folder,
                                    autoroute_executable_location,
                                    stream_network_shapefile,
                                    land_use_raster="",
                                    manning_n_table="",
                                    dem_extension='img',
                                    river_id='COMID',
                                    slope_id='SLOPE',
                                    default_manning_n=0.035,
                                    rapid_output_directory="", #path to ECMWF RAPID input/output directory
                                    return_period="", # return period name in return period file
                                    return_period_file="", # return period file generated from RAPID historical run
                                    rapid_output_file="", #path to RAPID output file to be used
                                    date_peak_search_start=None, #datetime of start of search for peakflow
                                    date_peak_search_end=None, #datetime of end of search for peakflow
                                    ):
    """
    Worker process for multiprocessing that manages one folders preparation
    """
    if sub_folder and os.path.exists(sub_folder) \
    and autoroute_executable_location and os.path.exists(autoroute_executable_location) \
    and stream_network_shapefile and os.path.exists(stream_network_shapefile):
    
        print("Running AutoRoute prepare for folder: {0}".format(sub_folder))
        os.chdir(sub_folder)
        
        out_rasterized_streamfile = os.path.join(sub_folder, 'rasterized_streamfile.tif')
        stream_info_file = os.path.join(sub_folder,'stream_info.txt')
        
        #rename elevation file for running autoroute
        original_elevation_dem_file = glob(os.path.join(sub_folder, '*.{0}'.format(dem_extension)))[0]
        elevation_dem_file = os.path.join(sub_folder, 'elevation.{0}'.format(dem_extension))
        os.rename(original_elevation_dem_file,
                  elevation_dem_file)
        
        #----------------------------------------------------------------------
        # Prepare stream info file
        #----------------------------------------------------------------------
        arp = AutoRoutePrepare(autoroute_executable_location,
                               elevation_dem_file,
                               stream_info_file,
                               stream_network_shapefile)
                               
        arp.rasterize_stream_shapefile(out_rasterized_streamfile, river_id)
           
        arp.generate_stream_info_file_with_direction(out_rasterized_streamfile,
                                                     search_radius=1)
       
        arp.append_slope_to_stream_info_file(river_id, slope_id)

        #----------------------------------------------------------------------
        # Method to generate streamflow for AutoRoute simulation (Optional)
        #----------------------------------------------------------------------
        try:
            PREPARE_MODE = get_valid_streamflow_prepare_mode(sub_folder,
                                                             rapid_output_directory,
                                                             return_period,
                                                             return_period_file,
                                                             rapid_output_file)
        except Exception as ex:
            print(ex)
            PREPARE_MODE = 0
            pass
        
        if PREPARE_MODE > 0:
            prepare_autoroute_streamflow_single_folder(PREPARE_MODE,
                                                       sub_folder,
                                                       stream_info_file,
                                                       rapid_output_directory,
                                                       return_period_file,
                                                       return_period,
                                                       rapid_output_file,
                                                       date_peak_search_start,
                                                       date_peak_search_end)
       
        #----------------------------------------------------------------------
        # Method to generate manning_n file from DEM, Land Use Raster, 
        # and Manning N Table with new AutoRoute
        # NOTE: This section is optional (WARNING: See 
        # "Prepare Manning's N Raster" section for projection info)
        #----------------------------------------------------------------------
        if land_use_raster and os.path.exists(land_use_raster) \
        and manning_n_table and os.path.exists(manning_n_table):
            arp.generate_manning_n_raster(land_use_raster,
                                          manning_n_table,
                                          os.path.join(sub_folder, 'manning_n.tif'),
                                          default_manning_n)

        try:
            os.remove(out_rasterized_streamfile)
        except OSError:
            pass

    else:
        print("Required files not found for preparing input. Skipping folder: {0}".format(sub_folder))


def prepare_autoroute_multiprocess_worker(args):
    """
    Run autoroute on one of multiple cores
    """
    job_name = args[15]
    log_directory = args[16]
    log_file_path = os.path.join(log_directory, "{0}-{1}.log".format(job_name, datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    with CaptureStdOutToLog(log_file_path):
        prepare_autoroute_single_folder(args[0],
                                        args[1],
                                        args[2],
                                        args[3],
                                        args[4],
                                        args[5],
                                        args[6],
                                        args[7],
                                        args[8],
                                        args[9],
                                        args[10],
                                        args[11],
                                        args[12],
                                        args[13],
                                        args[14])
    return job_name

#----------------------------------------------------------------------------------------
# MAIN PROCESS
#----------------------------------------------------------------------------------------
def prepare_autoroute_multiprocess(watershed_folder,
                                   autoroute_executable_location,
                                   stream_network_shapefile,
                                   log_directory, #path to multiprocessing logs
                                   land_use_raster="",
                                   manning_n_table="",
                                   dem_extension='img',
                                   river_id='COMID',
                                   slope_id='SLOPE',
                                   default_manning_n=0.035,
                                   rapid_output_directory="", #path to ECMWF RAPID input/output directory
                                   return_period="", # return period name in return period file
                                   return_period_file="", # return period file generated from RAPID historical run
                                   rapid_output_file="", #path to RAPID output file to be used
                                   date_peak_search_start=None, #datetime of start of search for peakflow
                                   date_peak_search_end=None, #datetime of end of search for peakflow
                                   num_cpus=-17
                                   ):
    """
    Function to prepare AutoRoute input using multiprocessing with the same folder 
    structure as running multiprocessing
    """
    #initialize multiprocess log directory
    prepare_log_directory = os.path.join(log_directory, "prepare")
    try:
        os.makedirs(prepare_log_directory)
    except OSError:
        pass
    
    print("Preparing input for AutoRoute ...")
    print("Logs can be found here: {0}".format(prepare_log_directory))

    watershed_name = os.path.basename(watershed_folder)
    multiprocessing_input = [(os.path.join(watershed_folder, sub_folder), autoroute_executable_location, stream_network_shapefile,
                              land_use_raster, manning_n_table, dem_extension, river_id, slope_id, default_manning_n,
                              rapid_output_directory, return_period, return_period_file, rapid_output_file,
                              date_peak_search_start, date_peak_search_end, "{0}-{1}".format(watershed_name, sub_folder), prepare_log_directory)
                             for sub_folder in os.listdir(watershed_folder) \
                             if os.path.isdir(os.path.join(watershed_folder, sub_folder))]

    pool = multiprocessing.Pool(get_valid_num_cpus(num_cpus))

    mp_worker_list = pool.imap_unordered(prepare_autoroute_multiprocess_worker,
                                         multiprocessing_input,
                                         chunksize=1)
                                         
    for multi_job_output in mp_worker_list:
        print("JOB FINISHED: {0}".format(multi_job_output))

    pool.close()
    pool.join()
