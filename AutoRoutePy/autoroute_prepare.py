# -*- coding: utf-8 -*-
import csv
import netCDF4 as NET
import numpy as np
import os
from osgeo import gdal, ogr, osr

#------------------------------------------------------------------------------
#Main Dataset Manager Class
#------------------------------------------------------------------------------
class AutoRoutePrepare(object):
    """
    This class is designed to prepare the input for AutoRoute
    Input: Elevation DEM, Stream Shapefile 
    """

    def __init__(self, elevation_dem_path, stream_shapefile_path=""):
        """
        Initialize the class with variables given by the user
        """
        self.elevation_dem_path = elevation_dem_path
        self.stream_shapefile_path = stream_shapefile_path
    
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

    def rasterize_stream_shapefle(self, streamid_raster_path, stream_id, input_dtype=gdal.GDT_Int32):
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

    def create_streamid_rasterindex_file(self, streamid_raster_path, 
                                         output_streamid_rasterindex_file):
        """
        Create file linking stream ID to raster index
        Ex.
        StreamID, row, col 
        555, 1, 2
        555, 7, 6
        556, 1, 1
        ...
        """
        print "Generating streamID rasterIndex file ..."
        streamid_raster = gdal.Open(streamid_raster_path)
        streamid_raster_band = streamid_raster.GetRasterBand(1)
        cols = streamid_raster_band.XSize
        rows = streamid_raster_band.YSize
        data = streamid_raster_band.ReadAsArray(0, 0, cols, rows)
        with open(output_streamid_rasterindex_file, 'wb') as outfile:
            writer = csv.writer(outfile)
            for i in range(0, rows):
                for j in range(0, cols):
                    if data[i,j] >= 0:
                        writer.writerow([int(data[i,j]), i , j])
                    
    def csv_to_list(self, csv_file, delimiter=','):
        """
        Reads in a CSV file and returns the contents as list,
        where every row is stored as a sublist, and each element
        in the sublist represents 1 cell in the table.
     
        """
        with open(csv_file, 'rb') as csv_con:
            reader = csv.reader(csv_con, delimiter=delimiter)
            return list(reader)

    def get_reordered_subset_streamid_index_list_from_netcdf(self, reach_id_list, prediction_file):
        """
        Gets the subset reordered_streamid_list from the netcdf file
        """
        data_nc = NET.Dataset(prediction_file, mode="r")
        com_ids = data_nc.variables['COMID'][:]
        data_nc.close()
        netcdf_reach_indices_list = []
        for reach_id in reach_id_list:
            #get where streamids are in netcdf file
            netcdf_reach_indices_list.append(np.where(com_ids==reach_id)[0][0])
     
        return np.array(netcdf_reach_indices_list)                  

    def generate_streamflow_raster_from_ecmwf_rapid_output(self, streamid_rasterindex_file, 
                                                           prediction_folder, out_streamflow_raster,
                                                           method_x, method_y):
        """
        Generate StreamFlow raster
        Create AutoRAPID INPUT from ECMWF predicitons
     
        method_x = the first axis - it produces the max, min, mean, mean_plus_std, mean_minus_std hydrograph data for the 52 ensembles
        method_y = the second axis - it calculates the max, min, mean, mean_plus_std, mean_minus_std value from method_x
        """
     
        print "Generating Streamflow Raster ..."
        #get list of streamidS
        streamid_rasterindex_table = self.csv_to_list(streamid_rasterindex_file)
        streamid_list_full = np.array([int(row[0]) for row in streamid_rasterindex_table])
        streamid_list_unique = np.unique(streamid_list_full)
     
        #Get list of prediciton files
     
        prediction_files = sorted([os.path.join(prediction_folder,f) for f in os.listdir(prediction_folder) \
                                  if not os.path.isdir(os.path.join(prediction_folder, f)) and f.lower().endswith('.nc')],
                                  reverse=True)
     
     
        print "Finding streamid indices ..."
        reordered_streamid_index_list = self.get_reordered_subset_streamid_index_list_from_netcdf(streamid_list_unique, 
                                                                                                  prediction_files[0])
        data_nc = NET.Dataset(prediction_files[0], mode="r")
        time_length = len(data_nc.variables['time'][:])
        data_nc.close()

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
                data_nc = NET.Dataset(prediction_file, mode="r")
                qout_dimensions = data_nc.variables['Qout'].dimensions
                if qout_dimensions[0].lower() == 'time' and qout_dimensions[1].lower() == 'comid':
                    data_values_2d_array = data_nc.variables['Qout'][:, reordered_streamid_index_list].transpose()
                elif qout_dimensions[0].lower() == 'comid' and qout_dimensions[1].lower() == 'time':
                    data_values_2d_array = data_nc.variables['Qout'][reordered_streamid_index_list, :]
                else:
                    print "Invalid ECMWF forecast file", prediction_file
                    data_nc.close()
    
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
     
        print "Analyzing data ..."
        streamflow_raster = self.generate_raster_from_dem(out_streamflow_raster, dtype=gdal.GDT_Float32)
        streamflow_raster_band = streamflow_raster.GetRasterBand(1)
        streamflow_raster_array = np.full((streamflow_raster_band.YSize, streamflow_raster_band.XSize), -9999, dtype=np.float32)
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
            grid_index_table_indices = np.where(streamid_list_full==streamid)[0]
            for grid_index_table_index in grid_index_table_indices:
                row = int(streamid_rasterindex_table[grid_index_table_index][1])
                col = int(streamid_rasterindex_table[grid_index_table_index][2])
                try:
                    streamflow_raster_array[row][col] = data_val
                except IndexError:
                    print row, col, data_val
                    raise

        print "Writing data to streamflow raster ..."
        streamflow_raster_band.WriteArray(streamflow_raster_array)
    
    def generate_streamflow_raster_from_rapid_output(self, streamid_rasterindex_file, 
                                                     rapid_output_file, 
                                                     out_streamflow_raster):
        """
        Generate StreamFlow raster
        Create AutoRAPID INPUT from single RAPID output
     
        """
     
        print "Generating Streamflow Raster ..."
        #get list of streamidS
        streamid_rasterindex_table = self.csv_to_list(streamid_rasterindex_file)
        streamid_list_full = np.array([int(row[0]) for row in streamid_rasterindex_table])
        streamid_list_unique = np.unique(streamid_list_full)
     
        #Get list of prediciton files
     
        print "Finding streamid indices ..."
        reordered_streamid_index_list = self.get_reordered_subset_streamid_index_list_from_netcdf(streamid_list_unique, 
                                                                                                  rapid_output_file)

        print "Extracting Data ..."
        #get information from datasets
        data_nc = NET.Dataset(rapid_output_file, mode="r")
        qout_dimensions = data_nc.variables['Qout'].dimensions
        qout_2d_array = []
        if qout_dimensions[0].lower() == 'time' and qout_dimensions[1].lower() == 'comid':
            qout_2d_array = data_nc.variables['Qout'][:,reordered_streamid_index_list].transpose()
        elif qout_dimensions[1].lower() == 'time' and qout_dimensions[0].lower() == 'comid':
            qout_2d_array = data_nc.variables['Qout'][reordered_streamid_index_list, :]
        else:
            data_nc.close()
            raise Exception("Invalid RAPID qout file {}".format(rapid_output_file))
            
        data_nc.close()
     
        print "Analyzing data ..."
        streamflow_raster = self.generate_raster_from_dem(out_streamflow_raster, dtype=gdal.GDT_Float32)
        streamflow_raster_band = streamflow_raster.GetRasterBand(1)
        streamflow_raster_array = np.full((streamflow_raster_band.YSize, streamflow_raster_band.XSize), -9999, dtype=np.float32)
        
        for streamid_index, streamid in enumerate(streamid_list_unique):
            #get peak/max
            peak_flow = np.amax(qout_2d_array[streamid_index])
     
            #get where streamids are in the lookup grid id table
            grid_index_table_indices = np.where(streamid_list_full==streamid)[0]
            for grid_index_table_index in grid_index_table_indices:
                row = int(streamid_rasterindex_table[grid_index_table_index][1])
                col = int(streamid_rasterindex_table[grid_index_table_index][2])
                try:
                    streamflow_raster_array[row][col] = peak_flow
                except IndexError:
                    print row, col, peak_flow
                    raise

        print "Writing data to streamflow raster ..."
        streamflow_raster_band.WriteArray(streamflow_raster_array)

    def generate_streamflow_raster_from_return_period_file(self, streamid_rasterindex_file, 
                                                           out_streamflow_raster,
                                                           return_period_file, 
                                                           return_period):
        """
        Generates return period raster from return period file
        """
        print "Extracting Return Period Data ..."
        return_period_nc = NET.Dataset(return_period_file, mode="r")
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
        streamid_rasterindex_table = self.csv_to_list(streamid_rasterindex_file)
        streamid_list_full = np.array([int(row[0]) for row in streamid_rasterindex_table])
        streamid_list_unique = np.unique(streamid_list_full)
        print "Analyzing data ..."
        streamflow_raster = self.generate_raster_from_dem(out_streamflow_raster, dtype=gdal.GDT_Float32)
        streamflow_raster_band = streamflow_raster.GetRasterBand(1)
        streamflow_raster_array = np.full((streamflow_raster_band.YSize, streamflow_raster_band.XSize), -9999, dtype=np.float32)
        
        for streamid in streamid_list_unique:
            try:
                #get where streamids are in netcdf file
                streamid_index = np.where(return_period_comids==streamid)[0][0]
            except Exception:
                print "streamid", streamid, "not found in list. Skipping ..."
                raise
                
            grid_index_table_indices = np.where(streamid_list_full==streamid)[0]
            for grid_index_table_index in grid_index_table_indices:
                row = int(streamid_rasterindex_table[grid_index_table_index][1])
                col = int(streamid_rasterindex_table[grid_index_table_index][2])
                try:
                    streamflow_raster_array[row][col] = return_period_data[streamid_index]
                except IndexError:
                    print row, col, return_period_data[streamid_index]
                    raise

 
        print "Writing data to streamflow raster ..."
        streamflow_raster_band.WriteArray(streamflow_raster_array)

            
if __name__ == "__main__":
    """
    #-------------------------------------------------------------------------
    #PREPARE MULTIPLE INPUT EXAMPLE
    #-------------------------------------------------------------------------
    from glob import glob
    main_folder='/media/alan/Seagate Backup Plus Drive/autoroute-io/philippines-luzon/Phillipines_DEMs/*'
    for direc in glob(main_folder):
        arp = AutoRoutePrepare(glob(os.path.join(main_folder, direc, 'n*.dt2'))[0],
                              '/media/alan/Seagate Backup Plus Drive/autoroute-io/philippines-luzon/DrainageLine.shp')
        arp.rasterize_stream_shapefle(os.path.join(main_folder, direc, 'rasterized_streamfile.tif'),
                                     'HydroID')
        arp.create_streamid_rasterindex_file(os.path.join(main_folder, direc, 'rasterized_streamfile.tif'),
                                             os.path.join(main_folder, direc, 'streamid_rasterindex.csv'))
    """
    """
    #-------------------------------------------------------------------------
    #RUN SINGLE EXAMPLE
    #-------------------------------------------------------------------------
    main_dir = '/media/alan/Seagate Backup Plus Drive/AutoRoute_Small_Test/'
    arp = AutoRoutePrepare(os.path.join(main_dir, 'Spencer', 'sp_dem.asc'),
                           os.path.join(main_dir,'flowlines_comid_slope_partial.shp'))
    arp.rasterize_stream_shapefle(os.path.join(main_dir,'rasterized_streamfile.tif'),
                                  'COMID')
    arp.rasterize_stream_shapefle(os.path.join(main_dir,'slope_raster.tif'),
                                  'slope',
                                  gdal.GDT_Float32)
    arp.create_streamid_rasterindex_file(os.path.join(main_dir,'rasterized_streamfile.tif'),
                                         os.path.join(main_dir,'streamid_rasterindex.csv'))
                                         
    rapid_input_file =  '/home/alan/work/rapid-io/output/korean_peninsula-korea/20151109.0/Qout_korean_peninsula_korea_1.nc'
    arp.generate_streamflow_raster_from_rapid_output(streamid_rasterindex_file='/home/alan/work/autoroute-io/input/korean_peninsula-korea/korea1/streamid_rasterindex.csv', 
                                                     rapid_output_file=rapid_input_file, 
                                                     out_streamflow_raster='/home/alan/work/autoroute-io/input/korean_peninsula-korea/korea1/streamflow_raster.tif')
    """