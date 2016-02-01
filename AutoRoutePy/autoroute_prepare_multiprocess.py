from AutoRoutePy.autoroute_prepare import AutoRoutePrepare
from glob import glob
import multiprocessing
import os

#----------------------------------------------------------------------------------
#MULTIPROCESSING FUNCTION
#----------------------------------------------------------------------------------
def autoroute_prepare_single_folder(sub_folder,
                                    autoroute_executable_location,
                                    stream_network_shapefile,
                                    land_use_raster="",
                                    manning_n_table="",
                                    dem_extension='img',
                                    river_id='COMID',
                                    slope_id='SLOPE',
                                    default_manning_n=0.035,
                                    ):
    """
    Worker process for multiprocessing that manages one folders preparation
    """
    if sub_folder and os.path.exists(sub_folder) \
    and autoroute_executable_location and os.path.exists(autoroute_executable_location) \
    and stream_network_shapefile and os.path.exists(stream_network_shapefile):
    
        print "Running AutoRoute prepare for folder:", sub_folder
        
        out_rasterized_streamfile = os.path.join(sub_folder, 'rasterized_streamfile.tif')
        stream_info_file = os.path.join(sub_folder,'stream_info.txt')
        
        #rename elevation file for running autoroute
        original_elevation_dem_file = glob(os.path.join(sub_folder, '*.{0}'.format(dem_extension)))[0]
        elevation_dem_file = os.path.join(sub_folder, 'elevation.{0}'.format(dem_extension))
        os.rename(original_elevation_dem_file,
                  elevation_dem_file)
        
        arp = AutoRoutePrepare(autoroute_executable_location,
                               elevation_dem_file,
                               stream_network_shapefile)
                               
        arp.rasterize_stream_shapefile(out_rasterized_streamfile, river_id)
           
        arp.generate_stream_info_file_with_direction(out_rasterized_streamfile,
                                                     stream_info_file,
                                                     search_radius=1)
       
        arp.append_slope_to_stream_info_file(stream_info_file, river_id, slope_id)
       
       
        #This section is optional (WARNING: See "Prepare Manning's N Raster" section for
        #projection info)
           
        #Method to generate manning_n file from DEM, Land Use Raster, and Manning N Table with new AutoRoute
        if land_use_raster and os.path.exists(land_use_raster) \
        and manning_n_table and os.path.exists(manning_n_table):
            arp.generate_manning_n_raster(land_use_raster,
                                          manning_n_table,
                                          os.path.join(local_dir, 'manning_n.tif'),
                                          default_manning_n)

        try:
            os.remove(out_rasterized_streamfile)
        except OSError:
            pass

    else:
        print "Required files not found for preparing input. Skipping folder:", sub_folder


def prepare_autoroute_multiprocess_worker(args):
    """
    Run autoroute on one of multiple cores
    """
    try:
        autoroute_prepare_single_folder(args[0],
                                        args[1],
                                        args[2],
                                        args[3],
                                        args[4],
                                        args[5],
                                        args[6],
                                        args[7],
                                        args[8])
    except Exception as ex:
        print ex

#----------------------------------------------------------------------------------------
# MAIN PROCESS
#----------------------------------------------------------------------------------------
def autoroute_prepare_multiprocess(watershed_folder,
                                   autoroute_executable_location,
                                   stream_network_shapefile,
                                   land_use_raster="",
                                   manning_n_table="",
                                   dem_extension='img',
                                   river_id='COMID',
                                   slope_id='SLOPE',
                                   default_manning_n=0.035,
                                   ):
    """
    Function to prepare AutoRoute input using multiprocessing with the same folder 
    structure as running multiprocessing
    """

    multiprocessing_input = [(os.path.join(watershed_folder, sub_folder), autoroute_executable_location, stream_network_shapefile,
                              land_use_raster, manning_n_table, dem_extension, river_id, slope_id, default_manning_n)
                             for sub_folder in os.listdir(watershed_folder) \
                             if os.path.isdir(os.path.join(watershed_folder, sub_folder))]

    pool = multiprocessing.Pool()

    pool.imap_unordered(prepare_autoroute_multiprocess_worker,
                        multiprocessing_input,
                        chunksize=1)

    pool.close()
    pool.join()

"""
if __name__ == "__main__":
    autoroute_prepare_multiprocess(watershed_folder='/Users/rdchlads/autorapid/autoroute-io/input/upperchocta',
                                   autoroute_executable_location='/Users/rdchlads/scripts/AutoRoute/source_code/autoroute',
                                   stream_network_shapefile='/Users/rdchlads/autorapid/gis_files/upperchocta/uc_flowlines_sl.shp',
                                   #land_use_raster="",
                                   #manning_n_table="",
                                   #dem_extension='img',
                                   #river_id='COMID',
                                   slope_id='elevslope',
                                   #default_manning_n=0.035,
                                   )
"""
