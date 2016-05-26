from osgeo import gdal

def reproject_lu_raster(dem_raster, land_use_raster, reprojected_land_use_raster):
    """
    This reprojects the land use raster to the same projection as the dem_raster
    """
    # Open source dataset
    src_ds = gdal.Open(land_use_raster)
    template_ds = gdal.Open(dem_raster)

    error_threshold = 0.125  # error threshold --> use same value as in gdalwarp
    resampling = gdal.GRA_NearestNeighbour

    # Call AutoCreateWarpedVRT() to fetch default values for target raster dimensions and geotransform
    tmp_ds = gdal.AutoCreateWarpedVRT( src_ds,
                                       None, # src_wkt : left to default value --> will use the one from source
                                       template_ds.GetProjection(),
                                       resampling,
                                       error_threshold )

    # Create the final warped raster
    dst_ds = gdal.GetDriverByName('GTiff').CreateCopy(reprojected_land_use_raster, tmp_ds)
    dst_ds = None
    src_ds = None

"""
if __name__ == "__main__":
    dem_raster = '/home/chluser/work/autoroute-io/input/TuscaloosaCounty/n33w088/elevation.img'
    land_use_raster = '/home/chluser/work/autoroute_prepare/TuscaloosaCounty/LandCover/NLCD2011_LC_N33W087.tif'
    reprojected_land_use_raster = '/home/chluser/work/autoroute_prepare/TuscaloosaCounty/LandCover/NLCD2011_LC_N33W087_repr.tif'
    reproject_lu_raster(dem_raster, land_use_raster, reprojected_land_use_raster)
"""
