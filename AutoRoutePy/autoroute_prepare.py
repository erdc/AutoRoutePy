# -*- coding: utf-8 -*-
##
##  autoroute_prepare.py
##  AutoRoutePy
##
##  Created by Alan D. Snow 2015.
##  Copyright © 2015 Alan D Snow. All rights reserved.
##
import csv
import datetime
from netCDF4 import Dataset
import numpy as np
import os
from osgeo import gdal, ogr, osr
from RAPIDpy.dataset import RAPIDDataset
from subprocess import Popen, PIPE

#------------------------------------------------------------------------------
#Main Dataset Manager Class
#------------------------------------------------------------------------------
class AutoRoutePrepare(object):
    """
    This class is designed to prepare the input for AutoRoute
    Input: Elevation DEM, Stream Shapefile 
    """

    def __init__(self, autoroute_executable_location, elevation_dem_path, stream_shapefile_path=""):
        """
        Initialize the class with variables given by the user
        """
        self.autoroute_executable_location = autoroute_executable_location
        self.elevation_dem_path = elevation_dem_path
        self.stream_shapefile_path = stream_shapefile_path
    
    def csv_to_list(self, csv_file, delimiter=','):
        """
        Reads in a CSV file and returns the contents as list,
        where every row is stored as a sublist, and each element
        in the sublist represents 1 cell in the table.
     
        """
        with open(csv_file, 'rb') as csv_con:
            reader = csv.reader(csv_con, delimiter=delimiter)
            return list(reader)

    def generate_raster_from_dem(self, raster_path, dtype=gdal.GDT_Int32):
        """
        Create an empty raster based on the DEM file
        """
        # Create the destination data source
        template_raster = gdal.Open(self.elevation_dem_path)
        template_raster_band = template_raster.GetRasterBand(1)
        target_driver = gdal.GetDriverByName('GTiff')
        if target_driver is None:
            raise ValueError("Can't find GTiff Driver")
        target_ds = target_driver.Create(raster_path, template_raster_band.XSize,
                                         template_raster_band.YSize, 1, dtype)
        
        target_ds.SetGeoTransform(template_raster.GetGeoTransform())
        out_projection = osr.SpatialReference()
        out_projection.ImportFromWkt(template_raster.GetProjectionRef())
        target_ds.SetProjection(out_projection.ExportToWkt())
        band = target_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999)

        return target_ds

    def rasterize_stream_shapefile(self, streamid_raster_path, stream_id, input_dtype=gdal.GDT_Int32):
        """
        Convert stream shapefile to raster with stream ids/slope
        """
        print "Converting stream shapefile to raster ..."
        # Open the data source
        stream_shapefile = ogr.Open(self.stream_shapefile_path)
        source_layer = stream_shapefile.GetLayer(0)

        target_ds = self.generate_raster_from_dem(streamid_raster_path, dtype=input_dtype)
        # Rasterize
        err = gdal.RasterizeLayer(target_ds, [1], source_layer, options=["ATTRIBUTE=%s" % stream_id])
        if err != 0:
            raise Exception("error rasterizing layer: %s" % err)

    def generate_stream_info_file_with_direction(self, stream_raster_file_name,
                                                 stream_info_file,
                                                 search_radius):
        """
        Generate stream info input file for AutoRoute starter with stream direction
        """
                
        time_start = datetime.datetime.utcnow()
                        

        #run AutoRoute
        print "Running AutoRoute prepare ..."
        process = Popen([self.autoroute_executable_location,
                         stream_raster_file_name,
                         stream_info_file,
                         str(search_radius)],
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if err:
            print err
            raise
        else:
            print 'AutoRoute output:'
            for line in out.split('\n'):
                print line

        print "Time to run: %s" % (datetime.datetime.utcnow()-time_start)


    def generate_manning_n_raster(self, land_use_raster,
                                  input_manning_n_table,
                                  output_manning_n_raster,
                                  default_manning_n):
        """
        Generate stream info input file for AutoRoute starter with stream direction
        """
                
        time_start = datetime.datetime.utcnow()
                        

        #run AutoRoute
        print "Running AutoRoute prepare ..."
        process = Popen([self.autoroute_executable_location,
                         land_use_raster,
                         self.elevation_dem_path,
                         input_manning_n_table,
                         output_manning_n_raster,
                         str(default_manning_n)],
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if err:
            print err
            raise
        else:
            print 'AutoRoute output:'
            for line in out.split('\n'):
                print line

        print "Time to run: %s" % (datetime.datetime.utcnow()-time_start)

    def append_slope_to_stream_info_file(self, stream_info_file, stream_id_field="COMID", slope_field="slope"):
        """
        Add the slope attribute to the stream direction file
        """
        def GetExtent(gt,cols,rows):
            ''' Return list of corner coordinates from a geotransform
            
            @type gt:   C{tuple/list}
            @param gt: geotransform
            @type cols:   C{int}
            @param cols: number of columns in the dataset
            @type rows:   C{int}
            @param rows: number of rows in the dataset
            @rtype:    C{[float,...,float]}
            @return:   coordinates of each corner
            '''
            ext=[]
            xarr=[0,cols]
            yarr=[0,rows]
            
            for px in xarr:
                for py in yarr:
                    x=gt[0]+(px*gt[1])+(py*gt[2])
                    y=gt[3]+(px*gt[4])+(py*gt[5])
                    ext.append([x,y])
                    #print x,y
                yarr.reverse()
            return ext

        def ReprojectCoords(coords,src_srs,tgt_srs):
            ''' Reproject a list of x,y coordinates.
                
                @type geom:     C{tuple/list}
                @param geom:    List of [[x,y],...[x,y]] coordinates
                @type src_srs:  C{osr.SpatialReference}
                @param src_srs: OSR SpatialReference object
                @type tgt_srs:  C{osr.SpatialReference}
                @param tgt_srs: OSR SpatialReference object
                @rtype:         C{tuple/list}
                @return:        List of transformed [[x,y],...[x,y]] coordinates
                '''
            trans_coords=[]
            transform = osr.CoordinateTransformation( src_srs, tgt_srs)
            for x,y in coords:
                x,y,z = transform.TransformPoint(x,y)
                trans_coords.append([x,y])
            return trans_coords

        stream_shapefile = ogr.Open(self.stream_shapefile_path)
        stream_shp_layer = stream_shapefile.GetLayer()

        #get extent from elevation raster to filter data
        try:
            print "Attempting to filter ..."
            elevation_raster = gdal.Open(self.elevation_dem_path)

            gt=elevation_raster.GetGeoTransform()
            cols = elevation_raster.RasterXSize
            rows = elevation_raster.RasterYSize
            raster_ext = GetExtent(gt,cols,rows)

            src_srs=osr.SpatialReference()
            src_srs.ImportFromWkt(elevation_raster.GetProjection())
            tgt_srs = stream_shp_layer.GetSpatialRef()

            raster_ext = ReprojectCoords(raster_ext,src_srs,tgt_srs)
            
            #read in the shapefile and get the data for slope
            string_rast_ext = ["{0} {1}".format(x,y) for x,y in raster_ext]
            wkt = "POLYGON (({0},{1}))".format(",".join(string_rast_ext), string_rast_ext[0])
            stream_shp_layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))
        except Exception as ex:
            print ex
            print "Skipping filter. This may take longer ..."
            pass

        print "Writing output to file ..."
        stream_info_table = self.csv_to_list(stream_info_file, " ")[1:]
        #Columns: DEM_1D_Index Row Col StreamID StreamDirection
        stream_id_list = np.array([row[3] for row in stream_info_table], dtype=np.int32)
        with open(stream_info_file, 'wb') as outfile:
            writer = csv.writer(outfile, delimiter=" ")
            writer.writerow(["DEM_1D_Index", "Row", "Col", "StreamID", "StreamDirection", "Slope"])
            for feature in stream_shp_layer:
                #find all raster indices associates with the comid
                raster_index_list = np.where(stream_id_list==int(feature.GetField(stream_id_field)))[0]
                #add slope associated with comid    
                slope = feature.GetField(slope_field)
                for raster_index in raster_index_list:
                    writer.writerow(stream_info_table[raster_index][:5] + [slope] + stream_info_table[raster_index][6:])


    def append_streamflow_from_ecmwf_rapid_output(self, stream_info_file,
                                                  prediction_folder,
                                                  method_x, method_y):
        """
        Generate StreamFlow raster
        Create AutoRAPID INPUT from ECMWF predicitons
     
        method_x = the first axis - it produces the max, min, mean, mean_plus_std, mean_minus_std hydrograph data for the 52 ensembles
        method_y = the second axis - it calculates the max, min, mean, mean_plus_std, mean_minus_std value from method_x
        """
     
        print "Generating Streamflow Raster ..."
        #get list of streamidS
        stream_info_table = self.csv_to_list(stream_info_file, " ")[1:]

        #Columns: DEM_1D_Index Row Col StreamID StreamDirection
        streamid_list_full = np.array([row[3] for row in stream_info_table], dtype=np.int32)
        streamid_list_unique = np.unique(streamid_list_full)
        if not streamid_list_unique:
            raise Exception("ERROR: No stream id values found in stream info file.")
        
        #Get list of prediciton files
        prediction_files = sorted([os.path.join(prediction_folder,f) for f in os.listdir(prediction_folder) \
                                  if not os.path.isdir(os.path.join(prediction_folder, f)) and f.lower().endswith('.nc')],
                                  reverse=True)
     
     
        print "Finding streamid indices ..."
        with RAPIDDataset(prediction_files[0]) as data_nc:
            reordered_streamid_index_list = data_nc.get_subset_riverid_index_list(streamid_list_unique)

        first_half_size = 40
        if time_length == 41 or time_length == 61:
            first_half_size = 41
        elif time_length == 85 or time_length == 125:
            #run at full resolution for all
            first_half_size = 65
        
        print "Extracting Data ..."
        reach_prediciton_array_first_half = np.zeros((len(streamid_list_unique),len(prediction_files),first_half_size))
        reach_prediciton_array_second_half = np.zeros((len(streamid_list_unique),len(prediction_files),20))
        #get information from datasets
        for file_index, prediction_file in enumerate(prediction_files):
            data_values_2d_array = []
            try:
                ensemble_index = int(os.path.basename(prediction_file)[:-3].split("_")[-1])
                #Get hydrograph data from ECMWF Ensemble
                with RAPIDDataset(prediction_file) as data_nc:
                    data_values_2d_array = data_nc.get_qout_index(reordered_streamid_index_list)
    
            except Exception, e:
                print e
                #pass
            #add data to main arrays and order in order of interim comids
            if len(data_values_2d_array) > 0:
                for comid_index in range(len(streamid_list_unique)):
                    if(ensemble_index < 52):
                        reach_prediciton_array_first_half[comid_index][file_index] = data_values_2d_array[comid_index][:first_half_size]
                        reach_prediciton_array_second_half[comid_index][file_index] = data_values_2d_array[comid_index][first_half_size:]
                    if(ensemble_index == 52):
                        if first_half_size == 65:
                            #convert to 3hr-6hr
                            streamflow_1hr = data_values_2d_array[comid_index][:90:3]
                            # get the time series of 3 hr/6 hr data
                            streamflow_3hr_6hr = data_values_2d_array[comid_index][90:]
                            # concatenate all time series
                            reach_prediciton_array_first_half[comid_index][file_index] = np.concatenate([streamflow_1hr, streamflow_3hr_6hr])
                        elif time_length == 125:
                            #convert to 6hr
                            streamflow_1hr = data_values_2d_array[comid_index][:90:6]
                            # calculate time series of 6 hr data from 3 hr data
                            streamflow_3hr = data_values_2d_array[comid_index][90:109:2]
                            # get the time series of 6 hr data
                            streamflow_6hr = data_values_2d_array[comid_index][109:]
                            # concatenate all time series
                            reach_prediciton_array_first_half[comid_index][file_index] = np.concatenate([streamflow_1hr, streamflow_3hr, streamflow_6hr])
                        else:
                            reach_prediciton_array_first_half[comid_index][file_index] = data_values_2d_array[comid_index][:]
     
        print "Analyzing data and writing output ..."
        with open(stream_info_file, 'wb') as outfile:
            writer = csv.writer(outfile, delimiter=" ")
            writer.writerow(["DEM_1D_Index", "Row", "Col", "StreamID", "StreamDirection", "Slope", "Flow"])

            for streamid_index, streamid in enumerate(streamid_list_unique):
                #perform analysis on datasets
                all_data_first = reach_prediciton_array_first_half[streamid_index]
                all_data_second = reach_prediciton_array_second_half[streamid_index]
         
                series = []
         
                if "mean" in method_x:
                    #get mean
                    mean_data_first = np.mean(all_data_first, axis=0)
                    mean_data_second = np.mean(all_data_second, axis=0)
                    series = np.concatenate([mean_data_first,mean_data_second])
                    if "std" in method_x:
                        #get std dev
                        std_dev_first = np.std(all_data_first, axis=0)
                        std_dev_second = np.std(all_data_second, axis=0)
                        std_dev = np.concatenate([std_dev_first,std_dev_second])
                        if method_x == "mean_plus_std":
                            #mean plus std
                            series += std_dev
                        elif method_x == "mean_minus_std":
                            #mean minus std
                            series -= std_dev
         
                elif method_x == "max":
                    #get max
                    max_data_first = np.amax(all_data_first, axis=0)
                    max_data_second = np.amax(all_data_second, axis=0)
                    series = np.concatenate([max_data_first,max_data_second])
                elif method_x == "min":
                    #get min
                    min_data_first = np.amin(all_data_first, axis=0)
                    min_data_second = np.amin(all_data_second, axis=0)
                    series = np.concatenate([min_data_first,min_data_second])
         
                data_val = 0
                if "mean" in method_y:
                    #get mean
                    data_val = np.mean(series)
                    if "std" in method_y:
                        #get std dev
                        std_dev = np.std(series)
                        if method_y == "mean_plus_std":
                            #mean plus std
                            data_val += std_dev
                        elif method_y == "mean_minus_std":
                            #mean minus std
                            data_val -= std_dev
         
                elif method_y == "max":
                    #get max
                    data_val = np.amax(series)
                elif method_y == "min":
                    #get min
                    data_val = np.amin(series)
         
                #get where streamids are in the lookup grid id table
                raster_index_list = np.where(streamid_list_full==streamid)[0]
                for raster_index in raster_index_list:
                    writer.writerow(stream_info_table[raster_index][:6] + [data_val])

    
    def append_streamflow_from_rapid_output(self, stream_info_file, 
                                            rapid_output_file,
                                            date_peak_search_start=None,
                                            date_peak_search_end=None):
        """
        Generate StreamFlow raster
        Create AutoRAPID INPUT from single RAPID output
        """
        print "Appending streamflow for:", stream_info_file
        #get information from datasets
        #get list of streamids
        stream_info_table = self.csv_to_list(stream_info_file, " ")[1:]
        #Columns: DEM_1D_Index Row Col StreamID StreamDirection
        streamid_list_full = np.array([row[3] for row in stream_info_table], dtype=np.int32)
        streamid_list_unique = np.unique(streamid_list_full)
        
        temp_stream_info_file = "{0}_temp.txt".format(os.path.splitext(stream_info_file)[0])
        print "Analyzing data and appending to list ..."
        with open(temp_stream_info_file, 'wb') as outfile:
            writer = csv.writer(outfile, delimiter=" ")
            writer.writerow(["DEM_1D_Index", "Row", "Col", "StreamID", "StreamDirection", "Slope", "Flow"])
            
            with RAPIDDataset(rapid_output_file) as data_nc:
                
                time_range = data_nc.get_time_index_range(date_peak_search_start=date_peak_search_start,
                                                          date_peak_search_end=date_peak_search_end)
                #perform operation in max chunk size of 4,000
                max_chunk_size = 8*365*5*4000 #5 years of 3hr data (8/day) with 4000 comids at a time
                time_length = 8*365*5 #assume 5 years of 3hr data
                if time_range:
                    time_length = len(time_range)
                else:
                    time_length = data_nc.size_time

                streamid_list_length = len(streamid_list_unique)
                step_size = min(max(1, max_chunk_size/time_length), streamid_list_length)
                for list_index_start in xrange(0, streamid_list_length, step_size):
                    list_index_end = min(list_index_start+step_size, streamid_list_length)
                    print "River ID subset range {0} to {1} of {2} ...".format(list_index_start,
                                                                               list_index_end,
                                                                               streamid_list_length)
                    print "Extracting data ..."
                    streamid_list_subset = streamid_list_unique[list_index_start:list_index_end]
                    data_nc.get_qout(streamid_list_subset,
                                     date_peak_search_start,
                                     date_peak_search_end)
                    
                    print "Calculating peakflow and writing to file ..."
                    for streamid_index, streamid in enumerate(valid_stream_ids):
                        #get where streamids are in the lookup grid id table
                        peak_flow = max(streamflow_array[streamid_index])
                        raster_index_list = np.where(streamid_list_full==streamid)[0]
                        for raster_index in raster_index_list:
                            writer.writerow(stream_info_table[raster_index][:6] + [peak_flow])

                    for missing_streamid in missing_stream_ids:
                        #set flow to zero for missing stream ids
                        raster_index_list = np.where(streamid_list_full==missing_streamid)[0]
                        for raster_index in raster_index_list:
                            writer.writerow(stream_info_table[raster_index][:6] + [0])


         
        os.remove(stream_info_file)
        os.rename(temp_stream_info_file, stream_info_file)

        print "Appending streamflow complete for:", stream_info_file


    def append_streamflow_from_return_period_file(self, stream_info_file, 
                                                  return_period_file, 
                                                  return_period):
        """
        Generates return period raster from return period file
        """
        print "Extracting Return Period Data ..."
        return_period_nc = Dataset(return_period_file, mode="r")
        if return_period == "return_period_20": 
            return_period_data = return_period_nc.variables['return_period_20'][:]
        elif return_period == "return_period_10": 
            return_period_data = return_period_nc.variables['return_period_10'][:]
        elif return_period == "return_period_2": 
            return_period_data = return_period_nc.variables['return_period_2'][:]
        else:
            raise Exception("Invalid return period definition.")

        return_period_comids = return_period_nc.variables['COMID'][:]
        return_period_nc.close()
        
        #get where streamids are in the lookup grid id table
        stream_info_table = self.csv_to_list(stream_info_file, " ")[1:]
        streamid_list_full = np.array([row[3] for row in stream_info_table], dtype=np.int32)
        streamid_list_unique = np.unique(streamid_list_full)
        print "Analyzing data and appending to list ..."
        
        with open(stream_info_file, 'wb') as outfile:
            writer = csv.writer(outfile, delimiter=" ")
            writer.writerow(["DEM_1D_Index", "Row", "Col", "StreamID", "StreamDirection", "Slope", "Flow"])
            for streamid in streamid_list_unique:
                try:
                    #get where streamids are in netcdf file
                    streamid_index = np.where(return_period_comids==streamid)[0][0]
                    peak_flow = return_period_data[streamid_index]
                except IndexError:
                    print "ReachID", streamid, "not found in netCDF dataset. Setting value to zero ..."
                    peak_flow = 0
                    pass
                    
                #get where streamids are in the lookup grid id table
                raster_index_list = np.where(streamid_list_full==streamid)[0]
                for raster_index in raster_index_list:
                    writer.writerow(stream_info_table[raster_index][:6] + [peak_flow])