# AutoRoutePy
python-based interface for AutoRoute

##Prereqs
- AutoRoute (GDAL Branch). See: https://github.com/erdc-cm/AutoRoute/tree/cgdal
- NetCDF4. See step 2 in installation instructions: https://github.com/erdc-cm/RAPIDpy
- (Optional) HTCondor & condorpy. See: https://github.com/erdc-cm/spt_ecmwf_autorapid_process

##Installation
```
$ git clone https://github.com/erdc-cm/AutoRoute-py.git
$ cd AutoRoutePy
```
To install:
```
python setup.py install
```
To develop:
```
python setup.py develop
```

##Prepare Inputs for AutoRoute
To begin, initialize the AutoRoutePrepare class with the location of the AutoRoute
exetutable, the path to your elevation raster, and the path to your stream network
shapefile.

```python
from AutoRoute.autoroute_prepare import AutoRoutePrepare
import os

autoroute_executable_location = '/home/alan/work/scripts/AutoRoute/source_code/autoroute'
input_dir = '/home/alan/work/autoroute-io/input/philippines-luzon/15'

arp = AutoRoutePrepare(autoroute_executable_location,
                       os.path.join(input_dir, 'elevation.dt2'),
                       '/path/to/DrainageLine.shp')
```

Next, to connect the elevation DEM to the stream network, you need to rasterize the
stream network based on the elevation DEM.

```python
out_rasterized_streamfile = os.path.join(input_dir, 'rasterized_streamfile.tif')

arp.rasterize_stream_shapefile(out_rasterized_streamfile,
                               stream_id='HydroID') #the attribute name of the stream ID used for RAPID
```

Then, create your stream info file and add stream direction and slope to it.

```python
stream_info_file = os.path.join(input_dir,'stream_info.txt')

arp.generate_stream_info_file_with_direction(out_rasterized_streamfile,
                                             stream_info_file,
                                             search_radius=1) #distance to search for stream direction in meters

arp.append_slope_to_stream_info_file(stream_info_file,
                                     'HydroID', #the attribute name of the stream ID used for RAPID
                                     'Avg_Slope') #the attribute name of the stream slope
```

###(Optional) Prepare Manning's N Raster
Based on a land use raster and a land use table, you can generate a Manning’s N raster to use with AutoRoute.

WARNING: The land use raster must be in the same projection as your elevation raster! 
If it is not in the same projection, either reproject using a GIS tool or use this
script.
```
from AutoRoute.reproject_raster import reproject_lu_raster

dem_raster = '/autoroute-io/input/TuscaloosaCounty/n33w088/elevation.img'
land_use_raster = '/autoroute_prepare/TuscaloosaCounty/NLCD2011_LC_N33W087.tif'
reprojected_land_use_raster = '/autoroute_prepare/TuscaloosaCounty/NLCD2011_LC_N33W087_repr.tif'

reproject_lu_raster(dem_raster, land_use_raster, reprojected_land_use_raster)
```
Once your land use raster is in the correct projection, use this process to generate the
manning n raster.

```python
from AutoRoute.autoroute_prepare import AutoRoutePrepare
import os

autoroute_executable_location = '/home/alan/work/scripts/AutoRoute/source_code/autoroute'
input_dir = '/home/alan/work/autoroute-io/input/philippines-luzon/15'

arp = AutoRoutePrepare(autoroute_executable_location,
                       os.path.join(input_dir, 'elevation.dt2'))
#Method to generate manning_n file from DEM, Land Use Raster, and Manning N Table with new AutoRoute
arp.generate_manning_n_raster(land_use_raster='/path/to/land_use/AutoRAPID_LULC.tif',
                              input_manning_n_table='/path/to/Manning_N_Values/AR_Manning_n_for_NLCD_LOW.txt',
                              output_manning_n_raster=os.path.join(main_dir, 'manning_n.tif'),
                              default_manning_n=0.035) #value for manning's n to be used in raster if no value found in table
```

###Prepare multiple inputs programmatically
Here is an example applying the principles above to programmatically loop
through your folders and prepare all of you input. This requires each elevation DEM
file to be inside of its own folder.

```python
from AutoRoutePy.autoroute_prepare import AutoRoutePrepare
from glob import glob
import os

autoroute_executable_location = '/AutoRoute/source_code/autoroute'
main_folder='/autoroute-io/input/TuscaloosaCounty/*'
dem_extension = 'img'
river_id = 'COMID'
slope_id = 'sslope'
stream_network_shapefile = '/gis_files/NHD_Flowlines_03W/NHDFlowLine_03W.shp'

for direc in glob(main_folder):
    local_dir = os.path.join(main_folder, direc)
    
    out_rasterized_streamfile = os.path.join(local_dir,'rasterized_streamfile.tif')
    stream_info_file = os.path.join(local_dir,'stream_info.txt')
    arp = AutoRoutePrepare(autoroute_executable_location,
                           glob(os.path.join(local_dir, '*.{0}'.format(dem_extension)))[0],
                           stream_network_shapefile)
    arp.rasterize_stream_shapefile(out_rasterized_streamfile, river_id)

    arp.generate_stream_info_file_with_direction(out_rasterized_streamfile,
                                                 stream_info_file,
                                                 search_radius=1)

    arp.append_slope_to_stream_info_file(stream_info_file, river_id, slope_id)

    """This section is optional, uncomment to use (WARNING: See "Prepare Manning's N Raster" section for
    projection info)

    #Method to generate manning_n file from DEM, Land Use Raster, and Manning N Table with new AutoRoute
    arp.generate_manning_n_raster(land_use_raster='/LandCover/NLCD2011_LC_N33W087_repr.tif',
                                  input_manning_n_table='/AutoRoute/manning_n_tables/AR_Manning_n_for_NLCD_LOW.txt',
                                  output_manning_n_raster=os.path.join(local_dir, 'manning_n.tif'),
                                  default_manning_n=0.035)
    """
```

##Running AutoRoute
This provides a simple example for running a single AutoRoute process. There are many different configurations for
running AutoRoute. AutoRoutePy allows you to change the parameters in the python code by name or through a 
AUTOROUTE_INPUT_FILE.txt.

```python
from AutoRoutePy.autoroute import AutoRoute
from AutoRoutePy.helper_functions import case_insensitive_file_search

autoroute_executable_location = '/home/alan/work/scripts/AutoRoute/source_code/autoroute'
autoroute_input_path = '/home/alan/work/autoroute-io/input/philippines-luzon/15'
autoroute_output_path = '/home/alan/work/autoroute-io/output/philippines-luzon/15'
out_shapefile_name = os.path.join(autoroute_output_path, 'flood_map_shp.tif')

auto_mng = AutoRoute(autoroute_executable_location,
                     dem_raster_file_path=case_insensitive_file_search(autoroute_input_path, r'elevation\.tiff'),
                     stream_info_file_path=case_insensitive_file_search(autoroute_input_path, r'stream_info\.txt'),
                     out_flood_map_raster_path=os.path.join(autoroute_output_path, 'flood_map.tif')
                    )

#this functiona allows you to update your parameters for AutoRoute            
auto_mng.update_parameters(out_flood_map_shapefile_path=out_shapefile_name)

#this runs autoroute. However, the input file is not required.
auto_mng.run_autoroute(autoroute_input_file=case_insensitive_file_search(autoroute_input_path, 
                                                                         r'AUTOROUTE_INPUT_FILE\.txt'))
```

##Running AutoRoute using Multiprocessing
There are several options to run AutoRoute using multiprocessing. In this example, you will learn how to run
this process with multiprocessing and HTCondor. Also, you will learn how to use the return period file to 
run this process as well as the output of a RAPID (rapid-hub.org) simulation.

In multiprocessing mode, you have to have your folders organizes inside the input directory such that each
elevation DEM tile has its own folder.


###Example 1: Using return period file with multiprocessing.
In addition to highlighting the usage of return period data and multiprocessing, this example shows
how you can use the defaults to generate the flood map shapefile and delete the flood map raster.

```python
from AutoRoutePy.run_autoroute_multicore import run_autoroute_multicore

autoroute_executable_location = '/home/alan/work/scripts/AutoRoute/source_code/autoroute'
autoroute_watershed_input_directory = '/home/alan/work/autoroute-io/input/philippines-luzon'
autoroute_watershed_output_directory = '/home/alan/work/autoroute-io/output/philippines-luzon' 
condor_log_dir = '/home/alan/work/condor_logs'

#run based on return period data
return_period_file = '/home/alan/work/rapid-io/output/philippines-luzon/return_periods.nc'
run_autoroute_multicore(autoroute_executable_location, #location of AutoRoute executable
                        autoroute_input_directory=autoroute_watershed_directory_path, #path to AutoRoute input directory
                        autoroute_output_directory=master_watershed_autoroute_output_directory, #path to AutoRoute output directory
                        return_period='return_period_20', # return period name in return period file
                        return_period_file=return_period_file, # return period file generated from RAPID historical run
                        mode="multiprocess", #multiprocess or htcondor
                        condor_log_directory=condor_init_dir,
                        #delete_flood_raster=True, #delete flood raster generated (default is True)
                        #generate_floodmap_shapefile=True, #generate a flood map shapefile (default is True)
                        wait_for_all_processes_to_finish=True #this will wait for all processes to finish
                        )

```

###Example 2: Using RAPID Qout file with HTCondor.
This example also demonstrates how to run AutoRoute without generating the floodmap shapefile and 
only producing the flood map raster.

```python
from AutoRoutePy.run_autoroute_multicore import run_autoroute_multicore

autoroute_executable_location = '/home/alan/work/scripts/AutoRoute/source_code/autoroute'
autoroute_watershed_input_directory = '/home/alan/work/autoroute-io/input/philippines-luzon'
autoroute_watershed_output_directory = '/home/alan/work/autoroute-io/output/philippines-luzon' 
condor_log_dir = '/home/alan/work/condor_logs'

#run based on return period data
rapid_output_file = '/home/alan/work/rapid-io/output/philippines-luzon/Qout_lis_1980to2014.nc'
run_autoroute_multicore(autoroute_executable_location, #location of AutoRoute executable
                        autoroute_input_directory=autoroute_watershed_directory_path, #path to AutoRoute input directory
                        autoroute_output_directory=master_watershed_autoroute_output_directory, #path to AutoRoute output directory
                        rapid_output_file=rapid_output_file, #RAPID Qout file from simulation
                        mode="htcondor", #multiprocess or htcondor
                        condor_log_directory=condor_init_dir,
                        delete_flood_raster=False, #delete flood raster generated (default is True)
                        generate_floodmap_shapefile=False, #generate a flood map shapefile (default is True)
                        wait_for_all_processes_to_finish=True #this will wait for all processes to finish
)

```
