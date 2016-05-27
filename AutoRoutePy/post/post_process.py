# -*- coding: utf-8 -*-
##
##  post_process.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License BSD 3-Clause

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
    if fileList:
        out_driver = ogr.GetDriverByName( 'ESRI Shapefile' )
        if os.path.exists(out_shapefile_name):
            out_driver.DeleteDataSource(out_shapefile_name)
        out_ds = out_driver.CreateDataSource(out_shapefile_name)
        out_layer = out_ds.CreateLayer(out_shapefile_name, geom_type=ogr.wkbPolygon)
        
        out_projection_file_name = "%s.prj" % os.path.splitext(out_shapefile_name)[0]
        if reproject:
            out_spatial_reference = osr.SpatialReference()
            out_spatial_reference.ImportFromEPSG(4326) #gcs_wgs_1984
            out_spatial_reference.MorphToESRI()
            with open(out_projection_file_name, 'w') as prj_file:
                prj_file.write(out_spatial_reference.ExportToWkt())
          
        else:
            #create projection file
            projection_file = glob(os.path.join(directory, "*.prj"))[0]
            copy(projection_file, out_projection_file_name)
        
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
    else:
        print "No files found to merge ..."
                
def rename_shapefiles(directory, out_shapefile_basename, startswith):
    """
    Renames all shapefiles in a directory
    """

    print "Renaming Shapefiles ..."
    fileList = glob(os.path.join(directory, "%s*" % startswith))
    for file_name in fileList:
        extension = os.path.splitext(file_name)[1]
        os.rename(file_name, os.path.join(directory, "%s%s" % (out_shapefile_basename, extension)))
        
            
def get_shapefile_layergroup_bounds(shapefile_paths):
    """
    Gets the extent of all of the shapefiles combined
    """
    lon_min = 99999999
    lon_max = -99999999
    lat_min = 99999999
    lat_max = -99999999
    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    epsg_code = None
    for shapefile_path in shapefile_paths:
        inDataSource = inDriver.Open(shapefile_path, 0)
        inLayer = inDataSource.GetLayer()
        extent = inLayer.GetExtent()
        lon_min = min(lon_min, extent[0])
        lon_max = max(lon_max, extent[1])
        lat_min = min(lat_min, extent[2])
        lat_max = max(lat_max, extent[3])
        spatialRef = inLayer.GetSpatialRef()
        layer_epsg = "EPSG:%s" % spatialRef.GetAttrValue("AUTHORITY", 1)
        if epsg_code==None:
            epsg_code = layer_epsg
        elif layer_epsg != layer_epsg:
            raise Exception("Projection EPSG codes don't match!")
        
    return [str(lon_min), str(lon_max), str(lat_min), str(lat_max), epsg_code]
    
    
