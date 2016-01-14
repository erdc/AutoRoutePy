# AutoRoute-py
python-based interface for AutoRoute

##Prereqs
- AutoRoute (GDAL Branch). See: https://github.com/erdc-cm/AutoRoute/tree/gdal
- NetCDF4. See step 2 in installation instructions: https://github.com/erdc-cm/RAPIDpy
- (Optional) HTCondor & condorpy. See: https://github.com/erdc-cm/spt_ecmwf_autorapid_process

##Installation
```
$ git clone https://github.com/erdc-cm/AutoRoute-py.git
$ cd AutoRoute-py
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

###Prepare multiple inputs programmatically
Here is an example applying the principles above to programmatically loop
through your folders and prepare all of you input. This requires each elevation DEM
file to be inside of its own folder.

```python
from AutoRoute.autoroute_prepare import AutoRoutePrepare
from glob import glob
import os

main_folder='/home/alan/work/autoroute-io/input/philippines-luzon/*'
dem_extension = 'dt2'
river_id = 'HydroID'
slope_id = 'Avg_Slope'
stream_network_shapefile = '/AutoRAPID/gis_files/phillipines-luzon/DrainageLine.shp'

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
```

##(Optional) Prepare Manning's N Raster
Based on a land use raster and a land use table, you can generate a Manning’s N raster to use with AutoRoute.

```python
from AutoRoute.autoroute_prepare import AutoRoutePrepare
import os

autoroute_executable_location = '/home/alan/work/scripts/AutoRoute/source_code/autoroute'
input_dir = '/home/alan/work/autoroute-io/input/philippines-luzon/15'

arp = AutoRoutePrepare(autoroute_executable_location,
                       os.path.join(input_dir, 'elevation.dt2'))
#Method to generate manning_n file from DEM, Land Use Raster, and Manning N Table with new AutoRoute
arp.generate_manning_n_raster(land_use_raster='/path/to/land_use/AutoRAPID_LULC.tif'),
                              input_manning_n_table='/path/to/Manning_N_Values/AR_Manning_n_for_NLCD_LOW.txt'),
                              output_manning_n_raster=os.path.join(main_dir, 'manning_n.tif'),
                              default_manning_n=0.035) #value for manning's n to be used in raster if no value found in table
```




