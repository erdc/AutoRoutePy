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
Next, to connect the elevation DEM to to the stream network, you need to rasterize the
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

arp.append_slope_to_stream_info_file(os.path.join(local_dir,'stream_info.txt'),'HydroID' ,'Avg_Slope')
```