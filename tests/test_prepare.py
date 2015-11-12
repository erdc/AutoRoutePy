from filecmp import cmp as fcmp
from nose.tools import ok_
import numpy.testing as npt
import os
from osgeo import gdal

#local import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from AutoRoutePy.autoroute_prepare import AutoRoutePrepare

def test_rasterize_stream_shapefle():
    """
    Checks AutoRoute input file generation with invalid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    output_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 1: RASTERIZE STREAM SHAPEFILE"
    arp = AutoRoutePrepare(os.path.join(original_data_path, 'elevation.tif'),
                           os.path.join(original_data_path, 'korea_drainageline.shp'))
    
    out_rasterized_streamfile = os.path.join(output_data_path, 'rasterized_streamfile.tif')
    arp.rasterize_stream_shapefle(out_rasterized_streamfile, 'GridID')
    
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

def test_create_streamid_rasterindex_file():
    """
    Checks AutoRoute input file generation with valid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    output_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 2: TEST CREATE STREAMID RASTERINDEX FILE"
    arp = AutoRoutePrepare(os.path.join(original_data_path, 'elevation.tif'))

    out_streamid_rasterindex_file = os.path.join(output_data_path, 'streamid_rasterindex.csv')
    arp.create_streamid_rasterindex_file(os.path.join(original_data_path, 'rasterized_streamfile_solution.tif'),
                                         out_streamid_rasterindex_file)
                                         
    ok_(fcmp(os.path.join(original_data_path, 'streamid_rasterindex_solution.csv'), out_streamid_rasterindex_file))
    
    try:
        os.remove(out_streamid_rasterindex_file)
    except OSError:
        pass


        
if __name__ == '__main__':
    import nose
    nose.main()