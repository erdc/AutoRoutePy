# -*- coding: utf-8 -*-
from glob import glob
import os
from osgeo import ogr, osr
from shutil import copy

#------------------------------------------------------------------------------
#AutoRoute Post Processing Functions
#------------------------------------------------------------------------------

def merge_shapefiles(directory, out_shapefile_name, reproject=False, remove_old=False):
    """
    Merges all shapefiles in a directory
    Options to reproject and remove old files
    """
    print "Merging Shapefiles ..."
    fileList = glob(os.path.join(directory, "*.shp"))

    out_driver = ogr.GetDriverByName( 'ESRI Shapefile' )
    if os.path.exists(out_shapefile_name):
        out_driver.DeleteDataSource(out_shapefile_name)
    out_ds = out_driver.CreateDataSource(out_shapefile_name)
    out_layer = out_ds.CreateLayer(out_shapefile_name, geom_type=ogr.wkbPolygon)
    
    if reproject:
        out_spatial_reference = osr.SpatialReference()
        out_spatial_reference.ImportFromEPSG(4326) #gcs_wgs_1984
    #create projection file
    projection_file = glob(os.path.join(directory, "*.prj"))[0]
    copy(projection_file, "%s.prj" % os.path.splitext(out_shapefile_name)[0])
    
    for file_path in fileList:
        ds = ogr.Open(file_path)
        lyr = ds.GetLayer()

        if reproject:
            in_spatial_ref = lyr.GetSpatialRef()
            coordinate_trans = osr.CoordinateTransformation(in_spatial_ref, 
                                                            out_spatial_reference)

        out_layer_definition = out_layer.GetLayerDefn()
        for in_feat in lyr:
            geom = in_feat.GetGeometryRef().Clone()
            if reproject:
                geom.Transform(coordinate_trans)
            out_feat = ogr.Feature(out_layer_definition)
            out_feat.SetGeometry(geom)
            out_layer.CreateFeature(out_feat)
            out_layer.SyncToDisk()
            out_feat.Destroy()
            in_feat.Destroy()
            
        ds.Destroy() #close the shapefile
        if remove_old:
            out_driver.DeleteDataSource(file_path)
            
    #close the output shapefile
    out_ds.Destroy()
                
def rename_shapefiles(directory, out_shapefile_basename, startswith=""):
    """
    Renames all shapefiles in a directory
    """

    print "Renaming Shapefiles ..."
    fileList = glob(os.path.join(directory, "%s*.shp" % startswith))
    for file_name in fileList:
        extension = os.path.splitext(file_name)[1]
        os.rename(file_name, os.path.join(directory, "%s%s" % (out_shapefile_basename, extension)))
        
            