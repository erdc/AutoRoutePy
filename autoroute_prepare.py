# -*- coding: utf-8 -*-
from osgeo import gdal, ogr

#------------------------------------------------------------------------------
#Main Dataset Manager Class
#------------------------------------------------------------------------------
class AutoRoutePrepare(object):
    """
    This class is designed to prepare the input for AutoRoute
    Input: Elevation DEM, Stream Shapefile 
    """

    def __init__(self, elevation_dem_path, stream_shapefile_path):
        """
        Initialize the class with variables given by the user
        """
        self.elevation_dem_path = elevation_dem_path
        self.stream_shapefile_path = stream_shapefile_path
    

    def rasterize_streamflow_shapefle(self, streamid_raster_path, stream_id):
        """
        Convert stream shapefile to raster with stream ids
        """
        print "Converting stream shapefile to raster ..."
        # Open the data source
        stream_shapefile = ogr.Open(self.stream_shapefile_path)
        source_layer = stream_shapefile.GetLayer(0)
        # Create the destination data source
        template_raster = gdal.Open(self.elevation_dem_path)
        template_raster_band = template_raster.GetRasterBand(1)
        target_driver = gdal.GetDriverByName('GTiff')
        if target_driver is None:
            raise ValueError("Can't find GTiff Driver")
        target_ds = target_driver.Create(streamid_raster_path, template_raster_band.XSize,
                                         template_raster_band.YSize, 1, gdal.GDT_Int32)
        
        target_ds.SetGeoTransform(template_raster.GetGeoTransform())
        target_ds.SetProjection(template_raster.GetProjection())
        band = target_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999)

        # Rasterize
        err = gdal.RasterizeLayer(target_ds, [1], source_layer, options=["ATTRIBUTE=%s" % stream_id])
        if err != 0:
            raise Exception("error rasterizing layer: %s" % err)

    def create_streamid_rasterindex_file(self, streamid_raster_path, 
                                         output_streamid_rasterindex_file):
        """
        Create file linking stream ID to raster index
        Ex.
        StreamID, RasterIndex
        555, 1
        555, 7
        556, 1
        ...
        """
        streamid_raster = gdal.Open(streamid_raster_path)
        streamid_raster_band = streamid_raster.GetRasterBand(1)
        cols = streamid_raster_band.XSize
        rows = streamid_raster_band.YSize
        data = streamid_raster_band.ReadAsArray(0, 0, cols, rows)
        ouput_file = open(output_streamid_rasterindex_file, 'wb')
        for i in range(0, rows):
            for j in range(0, cols):
                if data[i,j] >= 0:
                    ouput_file.write("%s %s\n" % (int(data[i,j]), i*cols+j))
        ouput_file.close()
                    
                    

    def generate_streamflow_raster(self):
        """
        Generate StreamFlow raster
        """
        print "Generating Streamflow Raster ..."
            
if __name__ == "__main__":
    arp = AutoRoutePrepare('/Users/rdchlads/autorapid/prepare_input/Test_Basin/DEM/dem_n44w091_Clip.asc',
                           '/Users/rdchlads/autorapid/prepare_input/Test_Basin/RiverNetwork/Mississippi_NHDFLowline_Thinn1_5.shp')
    """                       
    arp.rasterize_streamflow_shapefle('/Users/rdchlads/autorapid/prepare_input/Test_Basin/streamflow_raster.tif',
                                      'RIVID')
    """
    arp.create_streamid_rasterindex_file('/Users/rdchlads/autorapid/prepare_input/Test_Basin/streamflow_raster.tif',
                                         '/Users/rdchlads/autorapid/prepare_input/Test_Basin/streamid_rasterindex.csv')