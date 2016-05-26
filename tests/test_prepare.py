# -*- coding: utf-8 -*-
##
##  test_prepare.py
##  AutoRoutePy
##
##  Created by Alan D. Snow 2015.
##  Copyright © 2015 Alan D Snow. All rights reserved.
##

from filecmp import cmp as fcmp
from nose.tools import ok_
import numpy.testing as npt
import os
from osgeo import gdal
from shutil import copy

from AutoRoutePy.prepare import AutoRoutePrepare

def test_rasterize_stream_shapefile():
    """
    Checks AutoRoute input file generation with invalid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    output_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 1: RASTERIZE STREAM SHAPEFILE"
    arp = AutoRoutePrepare("autoroute_exe_path_dummy",
                           os.path.join(original_data_path, 'elevation.asc'),
                           "dummy_stream_info_path",
                           os.path.join(original_data_path, 'drainage_line.shp'))
    
    out_rasterized_streamfile = os.path.join(output_data_path, 'rasterized_streamfile.tif')
    arp.rasterize_stream_shapefile(out_rasterized_streamfile, 'COMID')
    
    original_rasterized_streamfile = os.path.join(original_data_path, 'rasterized_streamfile_solution.tif')
    
    #compare data in rasters
    def get_raster_data_array(raster_path):
        """
        Retreives all data from raster
        """
        streamid_raster = gdal.Open(raster_path)
        streamid_raster_band = streamid_raster.GetRasterBand(1)
        cols = streamid_raster_band.XSize
        rows = streamid_raster_band.YSize
        return streamid_raster_band.ReadAsArray(0, 0, cols, rows)
        
    print "TESTING RASTER DATA ..."
    npt.assert_almost_equal(get_raster_data_array(original_rasterized_streamfile),
                            get_raster_data_array(out_rasterized_streamfile))

    try:
        os.remove(out_rasterized_streamfile)
    except OSError:
        pass

def test_append_slope_to_stream_info_file():
    """
    Checks adding slope to stream info file
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    output_data_path = os.path.join(main_tests_folder, 'output')

    original_stream_info_file = os.path.join(original_data_path, 'stream_info.txt')
    stream_info_file = os.path.join(output_data_path, 'stream_info.txt')
    copy(original_stream_info_file, stream_info_file)
    
    print "TEST 2: TEST ADDING SLOPE TO STREAM INFO FILE"
    arp = AutoRoutePrepare("autoroute_exe_path_dummy",
                           os.path.join(original_data_path, 'elevation.asc'),
                           stream_info_file,
                           os.path.join(original_data_path, 'drainage_line.shp'))

    arp.append_slope_to_stream_info_file()
                                         
    ok_(fcmp(os.path.join(original_data_path, 'stream_info_solution.txt'), stream_info_file))
    
    try:
        os.remove(stream_info_file)
    except OSError:
        pass


        
if __name__ == '__main__':
    import nose
    nose.main()