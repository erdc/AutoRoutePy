# AutoRoutePy
Python scripting interface for the AutoRoute progam. Has ability to Prepare input from RAPID output (www.rapid-hub.org).

[![DOI](https://zenodo.org/badge/19918/erdc-cm/AutoRoutePy.svg)](https://zenodo.org/badge/latestdoi/19918/erdc-cm/AutoRoutePy)

[![Build Status](https://travis-ci.org/erdc-cm/AutoRoutePy.svg?branch=master)](https://travis-ci.org/erdc-cm/AutoRoutePy)

[![License (3-Clause BSD)](https://img.shields.io/badge/license-BSD%203--Clause-yellow.svg)](https://github.com/erdc-cm/AutoRoutePy/blob/master/LICENSE)

##Prereqs
- AutoRoute (GDAL Branch). See: https://github.com/erdc-cm/AutoRoute/tree/cgdal
- RAPIDpy. See: https://github.com/erdc-cm/RAPIDpy
- (Optional) HTCondor & condorpy. See: https://github.com/erdc-cm/spt_ecmwf_autorapid_process

##Installation

```
$ git clone https://github.com/erdc-cm/AutoRoutePy.git
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

###1. Prepare multiple inputs using multiprocessing.
Here is an example for using multiprocessing to prepare input for AutoRoute. This requires each elevation DEM
file to be inside of its own folder within the main watershed folder.

WARNING: The land use raster must be in the same projection as your elevation raster! If it is not in the same projection, either reproject using a GIS tool or use the *reproject_lu_raster* function (from RAPIDpy.prepare import reproject_lu_raster).

####Step 1: Import the function
```python
from AutoRoutePy.prepare import prepare_autoroute_multiprocess
```
####Step 2: Run using multiprocessing

#####Mode 1: Basic - just elevation DEM and stream network (NO STREAMFLOW)
```python
prepare_autoroute_multiprocess(watershed_folder='/autoroute-io/input/watershed_directory',
                               autoroute_executable_location='/AutoRoute/src/autoroute',
                               stream_network_shapefile='/path/to/river_network.shp',
                               log_directory="/path/to/logs", #path to multiprocessing logs
                               #dem_extension='img', #default is img
                               #river_id='COMID', #default is COMID
                               #slope_id='SLOPE', #default is SLOPE
                               #default_manning_n=0.035, #default is 0.035
                               #num_cpus=1 #number of cpus to use in process (default is all)
                               )
```

#####Mode 2: Basic+Land Use (NO STREAMFLOW)
WARNING: The land use raster must be in the same projection as your elevation raster! 
If it is not in the same projection, either reproject using a GIS tool or use this
script.

```python
from AutoRoutePy.prepare import reproject_lu_raster

dem_raster = '/autoroute-io/input/watershed-directory/sub_area-directory/elevation.img'
land_use_raster = '/autoroute_prepare/watershed-directory/NLCD2011_LC.tif'
reprojected_land_use_raster = '/autoroute_prepare/watershed-directory/NLCD2011_LC_repr.tif'

reproject_lu_raster(dem_raster, land_use_raster, reprojected_land_use_raster)
```
Once your land use raster is in the correct projection, use this process to generate the
manning n raster.

```python
land_use_to_mannning_n_table = '/AutoRoute/mannings_n_tabes/AR_Manning_n_for_NLCD_LOW.txt'

prepare_autoroute_multiprocess(watershed_folder='/autoroute-io/input/watershed_directory',
                               autoroute_executable_location='/AutoRoute/src/autoroute',
                               stream_network_shapefile='/path/to/river_network.shp',
                               log_directory="/path/to/logs", #path to multiprocessing logs
                               land_use_raster=reprojected_land_use_raster,
                               manning_n_table=land_use_to_mannning_n_table,
                               #dem_extension='img', #default is img
                               #river_id='COMID', #default is COMID
                               #slope_id='SLOPE', #default is SLOPE
                               #default_manning_n=0.035, #default is 0.035
                               #num_cpus=1 #number of cpus to use in process (default is all)
                               )
```

#####Mode 3: Streamflow
Note: You can run with or without land use as shown in Mode 1 & Mode 2. This is the same for Mode 3, however
only the basic mode will be shown here.

#####Mode 3.1: Streamflow from RAPID output
In this mode it will search for the peak from the entire simulation unless bounds are given from the date_peak_search_start or from the date_peak_search_end.
```python
from datetime import datetime
prepare_autoroute_multiprocess(watershed_folder='/autoroute-io/input/watershed_directory',
                               autoroute_executable_location='/AutoRoute/src/autoroute',
                               stream_network_shapefile='/path/to/river_network.shp',
                               log_directory="/path/to/logs", #path to multiprocessing logs
                               #dem_extension='img', #default is img
                               #river_id='COMID', #default is COMID
                               #slope_id='SLOPE', #default is SLOPE
                               #default_manning_n=0.035, #default is 0.035
                               rapid_output_file="/path/to/Qout.nc", #path to RAPID output file to be used
                               #date_peak_search_start=datetime(1990, 1, 1), #optional
                               #date_peak_search_end=datetime(1990, 3, 5), #optional
                               #num_cpus=1 #number of cpus to use in process (default is all)
                               )
```

#####Mode 3.2: Streamflow from return period file
```python
from datetime import datetime
prepare_autoroute_multiprocess(watershed_folder='/autoroute-io/input/watershed_directory',
                               autoroute_executable_location='/AutoRoute/src/autoroute',
                               stream_network_shapefile='/path/to/river_network.shp',
                               log_directory="/path/to/logs", #path to multiprocessing logs
                               #dem_extension='img', #default is img
                               #river_id='COMID', #default is COMID
                               #slope_id='SLOPE', #default is SLOPE
                               #default_manning_n=0.035, #default is 0.035
                               #valid return_periods -> 'max_flow','return_period_20','return_period_10','return_period_2'
                               return_period="return_period_20", 
                               return_period_file="/path/to/return_period.nc", 
                               #num_cpus=1 #number of cpus to use in process (default is all)
                               )
```

###2. Prepare single folder inputs
You can prepare inputs for a single folder with this function. 

This behaves the same as *autoroute_prepare_multiprocess* so you can refer to that section for instructions. However there are minor differences:
 
1) The input is the sub folder (has DEM inside);
2) No option for number of cpus as it only runs on one CPU;
3) No log directory as is prints to the console

```python
from AutoRoutePy.prepare import prepare_autoroute_single_folder
prepare_autoroute_single_folder(sub_folder='/autoroute-io/input/watershed_directory/sub_folder',
                                autoroute_executable_location='/AutoRoute/src/autoroute',
                                stream_network_shapefile='/path/to/river_network.shp',
                                #land_use_raster="",
                                #manning_n_table="",
                                #dem_extension='img',
                                #river_id='COMID',
                                #slope_id='SLOPE',
                                #default_manning_n=0.035,
                                #return_period="", # return period name in return period file
                                #return_period_file="", # return period file generated from RAPID historical run
                                #rapid_output_file="", #path to RAPID output file to be used
                                #date_peak_search_start=None, #datetime of start of search for peakflow
                                #date_peak_search_end=None, #datetime of end of search for peakflow
				 )
```

###3. Prepare infividual inputs
This is the modt fine grained method. To begin, initialize the AutoRoutePrepare class with the location of the AutoRoute
exetutable, the path to your elevation raster, and the path to your stream network
shapefile.

```python
from AutoRoutePy.prepare import AutoRoutePrepare
import os

autoroute_executable_location = '/AutoRoute/src/autoroute'
input_dir = '/autoroute-io/input/watershed-directory/sub_area-directory'
stream_info_file = os.path.join(input_dir,'stream_info.txt')
river_network_file = '/path/to/river_network.shp'


arp = AutoRoutePrepare(autoroute_executable_location,
                       os.path.join(input_dir, 'elevation.dt2'),
                       stream_info_file,
                       river_network_file)
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
arp.generate_stream_info_file_with_direction(out_rasterized_streamfile,
                                             search_radius=1) #distance to search for stream direction in meters

arp.append_slope_to_stream_info_file('HydroID', #the attribute name of the stream ID used for RAPID
                                     'Avg_Slope') #the attribute name of the stream slope
```

###(Optional) Prepare Manning's N Raster
Based on a land use raster and a land use table, you can generate a Manning’s N raster to use with AutoRoute.

WARNING: The land use raster must be in the same projection as your elevation raster! 
If it is not in the same projection, either reproject using a GIS tool or use this
script.

```python
from AutoRoutePy.reproject_raster import reproject_lu_raster

dem_raster = '/autoroute-io/input/watershed-directory/sub_area-directory/elevation.img'
land_use_raster = '/autoroute_prepare/watershed-directory/NLCD2011_LC.tif'
reprojected_land_use_raster = '/autoroute_prepare/watershed-directory/NLCD2011_LC_repr.tif'

reproject_lu_raster(dem_raster, land_use_raster, reprojected_land_use_raster)
```
Once your land use raster is in the correct projection, use this process to generate the
manning n raster.

```python
from AutoRoutePy.prepare import AutoRoutePrepare
import os

autoroute_executable_location = '/AutoRoute/src/autoroute'
input_dir = '/autoroute-io/input/watershed-directorysub_area-directory'
reprojected_land_use_raster = '/autoroute_prepare/watershed-directory/NLCD2011_LC_repr.tif'
land_use_to_mannning_n_table = '/AutoRoute/mannings_n_tabes/AR_Manning_n_for_NLCD_LOW.txt'

arp = AutoRoutePrepare(autoroute_executable_location,
                       os.path.join(input_dir, 'elevation.dt2'))
#Method to generate manning_n file from DEM, Land Use Raster, and Manning N Table with new AutoRoute
arp.generate_manning_n_raster(land_use_raster=reprojected_land_use_raster,
                              input_manning_n_table=land_use_to_mannning_n_table,
                              output_manning_n_raster=os.path.join(main_dir, 'manning_n.tif'),
                              default_manning_n=0.035)
```

###Adding Streamflow to AutoRoute Simulation
This is the code that starts the process off:
```python
from AutoRoutePy.prepare import AutoRoutePrepare
import os

input_dir = '/autoroute-io/input/watershed-directorysub_area-directory'
reprojected_land_use_raster = '/autoroute_prepare/watershed-directory/NLCD2011_LC_repr.tif'
river_network_file = '/path/to/river_network.shp'

arp = AutoRoutePrepare("", #autoroute_executable_location, - don't need for this step
                       "", #dem path - don't need for this step
                       os.path.join(input_dir, 'stream_info.txt')
                       river_network_file)
```
From there, you have three options:
####Create AutoRoute input from single RAPID output
This function grabs the peak within the specified time period.
If no time period is specified, it searches the whole dataset.
```python
from datetime import datetime
rapid_output_file = '/path/to/Qout_file.nc'


#OPTION 1: Search for Peak with Date Search
#NOTE: Date search will only work with CF compliant RAPID files
date_peak_search_start = datetime(1980,5,1)
date_peak_search_end = datetime(1980,8,30)

arp.append_streamflow_from_rapid_output(rapid_output_file,
                                        date_peak_search_start, #optional
                                        date_peak_search_end) #optional

#OPTION 2: Search for Peak in Entire Time Series
arp.append_streamflow_from_rapid_output(rapid_output_file)

```
####Create AutoRoute input from return period file
If you created a return period file from https://github.com/erdc-cm/spt_lsm_autorapid_process,
you can add the peak flows from each return period to the stream_info.txt.

NOTE: Valid return period options: return_period_20, return_period_10, return_period_2, max_flow

```python
return_period_file = "/path/to/return_periods.nc"
return_period = "return_period_20"
arp.append_streamflow_from_return_period_file(return_period_file, 
                                              return_period)
```
####Create AutoRoute input from shapefile field
If you already have a shapefile with the flow associated with each river segment,
you can use that as a method for input into the stream_info.txt file.

```python
stream_id_field = "HydroID"
streamflow_field = "StreamFlow"

arp.append_streamflow_from_stream_shapefile(stream_id_field, 
                                            streamflow_field)
```


##Running AutoRoute
###Method 1: Running AutoRoute using Multiprocessing
There are several options to run AutoRoute using multiprocessing. In this example, you will learn how to run
this process with multiprocessing and HTCondor. Also, you will learn how to use the return period file to 
run this process as well as the output of a RAPID (rapid-hub.org) simulation.

In multiprocessing mode, you have to have your folders organizes inside the input directory such that each
elevation DEM tile has its own folder.


####Example 1: Using pregenerated inputs with multiprocessing.
In addition to highlighting the usage of return period data and multiprocessing, this example shows
how you can use the defaults to generate the flood map shapefile and delete the flood map raster.

```python
from AutoRoutePy.run import run_autoroute_multiprocess

autoroute_executable_location = '/AutoRoute/src/autoroute'
autoroute_watershed_input_directory = '/autoroute-io/input/watershed-directory'
autoroute_watershed_output_directory = '/autoroute-io/output/watershed-directory' 
log_dir = '/logs'

#run based on return period data
run_autoroute_multiprocess(autoroute_executable_location, #location of AutoRoute executable
                           autoroute_input_directory=autoroute_watershed_input_directory, #path to AutoRoute input directory
                           autoroute_output_directory=autoroute_watershed_output_directory, #path to AutoRoute output directory
                           log_directory=log_dir,
                           mode="multiprocess", #multiprocess or htcondor
                           delete_flood_raster=False, #delete flood raster generated (default is True)
                           generate_floodmap_shapefile=False, #generate a flood map shapefile (default is True)
                           wait_for_all_processes_to_finish=True #this will wait for all processes to finish
                           )

```

####Example 2: Using return period file with multiprocessing.
In addition to highlighting the usage of return period data and multiprocessing, this example shows
how you can use the defaults to generate the flood map shapefile and delete the flood map raster.

```python
from AutoRoutePy.run import run_autoroute_multiprocess

autoroute_executable_location = '/AutoRoute/src/autoroute'
autoroute_watershed_input_directory = '/autoroute-io/input/watershed-directory'
autoroute_watershed_output_directory = '/autoroute-io/output/watershed-directory' 
log_dir = '/logs'

#run based on return period data
return_period_file = '/rapid-io/output/watershed-directory/return_periods.nc'
run_autoroute_multiprocess(autoroute_executable_location, #location of AutoRoute executable
                           autoroute_input_directory=autoroute_watershed_input_directory, #path to AutoRoute input directory
                           autoroute_output_directory=autoroute_watershed_output_directory, #path to AutoRoute output directory
                           log_directory=log_dir,
                           return_period='return_period_20', # return period name in return period file
                           return_period_file=return_period_file, # return period file generated from RAPID historical run
                           mode="multiprocess", #multiprocess or htcondor
                           #delete_flood_raster=True, #delete flood raster generated (default is True)
                           #generate_floodmap_shapefile=True, #generate a flood map shapefile (default is True)
                           wait_for_all_processes_to_finish=True #this will wait for all processes to finish
                           )

```


####Example 3: Using RAPID Qout file with HTCondor.
This example also demonstrates how to run AutoRoute without generating the floodmap shapefile and 
only producing the flood map raster.

```python
from datetime import datetime
from AutoRoutePy.run import run_autoroute_multiprocess

autoroute_executable_location = '/AutoRoute/src/autoroute'
autoroute_watershed_input_directory = '/autoroute-io/input/watershed-directory'
autoroute_watershed_output_directory = '/autoroute-io/output/watershed-directory' 
condor_log_dir = '/condor_logs'

#run based on return period data
rapid_output_file = '/rapid-io/output/watershed-directory/Qout_lis_1980to2014.nc'
run_autoroute_multiprocess(autoroute_executable_location, #location of AutoRoute executable
                           autoroute_input_directory=autoroute_watershed_input_directory, #path to AutoRoute input directory
                           autoroute_output_directory=autoroute_watershed_output_directory, #path to AutoRoute output directory
                           log_directory=condor_init_dir,
                           rapid_output_file=rapid_output_file, #RAPID Qout file from simulation
                           #date_peak_search_start=datetime(1990, 1, 1), #optional
                           #date_peak_search_end=datetime(1990, 3, 5), #optional
                           mode="htcondor", #multiprocess or htcondor
                           delete_flood_raster=False, #delete flood raster generated (default is True)
                           generate_floodmap_shapefile=False, #generate a flood map shapefile (default is True)
                           wait_for_all_processes_to_finish=True #this will wait for all processes to finish
                           )

```
###Method 2. Running single AutoRoute process
This provides a simple example for running a single AutoRoute process. There are many different configurations for
running AutoRoute. AutoRoutePy allows you to change the parameters in the python code by name or through a 
AUTOROUTE_INPUT_FILE.txt.

```python
from AutoRoutePy import AutoRoute
from AutoRoutePy.utilities import case_insensitive_file_search

autoroute_executable_location = '/AutoRoute/src/autoroute'
autoroute_input_path = '/autoroute-io/input/watershed-directory/sub_area-directory'
autoroute_output_path = '/autoroute-io/output/watershed-directory/sub_area-directory'
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


