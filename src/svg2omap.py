#!/usr/bin/env python3
#
# Copyright 2022, Roland Hansson https://github.com/rhansson
#
# See LICENSE
# 
from __future__ import print_function
import sys, os, errno, time, math
if sys.version_info[0] < 3:
    print("This program requires Python ver 3 or higher")
    sys.exit(1)
import argparse
from xml.dom import minidom

# https://numpy.org/
# version 1.19.1
import numpy as np

# https://github.com/mathandy/svgpathtools
# version: 1.5.1
from svgpathtools import svg2paths2
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc

# https://pypi.org/project/geojson/
# version: 2.5.0
from geojson import Point, LineString, Polygon, Feature, FeatureCollection, dump

# https://pyproj4.github.io/pyproj/stable/
# version: 3.4.0
from pyproj import CRS


#------------------------------------------------------------------------------

class MyCustomException(Exception):
    pass


class Converter(object):
    '''Manages conversion from SVG to geojson'''

    # Default attributes
    rotation = 0
    epsg = None
    skip_list = []
    map_units = 'm'  # UTM
    page_units = 'cm'
    unpcm = 1
    width = 1
    height = 1
    dpi = 300
    unpin = 1 / 2.54
    declination = 0
    grivation = 0
    mapscale = 1
    epsg = None
    ref_x = 0
    ref_y = 0

    def __init__(self, infile, outfile, mapfile, width, height, page_units, dpi, rotation, epsg, skip_list):
        if not os.path.exists(infile):
            raise FileNotFoundError("File not found: " + infile)
        self.infile = infile
        
        if not outfile:
            fn = os.path.splitext(infile)[0]
            self.outfile = fn + ".geojson"
        else:
            self.outfile = outfile
        
        if mapfile:
            if not os.path.exists(mapfile):
                raise FileNotFoundError("File not found: " + mapfile)
        self.mapfile = mapfile
        
        if width:
            self.width = width
        if height:
            self.height = height
        if width == 0 or height == 0 or dpi == 0:
            raise MyCustomException("INVALID argument: value = 0")
        
        if page_units:
            self.page_units = page_units
            if page_units.lower() == 'mm':
                self.unpin = 1 / 25.4
                self.unpcm = 10
            elif page_units.lower() == 'in':
                self.unpin = 1
                self.unpcm = 1 / 2.54
            elif page_units.lower() == 'pt':
                self.unpin = 1 / 72
                self.unpcm = (1 / 2.54) / (1 / 72) 
            # else: 'cm' 

        if dpi:
            self.dpi = dpi

        if rotation:
            if rotation > -360 and rotation <= 360:
                self.rotation = rotation

        if epsg:
            if epsg > 0:
                self.epsg = str(epsg)

        if skip_list:
            print(skip_list)
            self.skip_list = [int(item) for item in skip_list.split(',')]
            print(self.skip_list)
        


    def get_epsg(self, spec, south=False):
        epsg = None
        if south:
            spec = spec + " +south"
        #crs = CRS.from_proj4("+proj=utm +zone=11 +north +datum=WGS84") #+lat=34.26233857 +lon=-117.04257955")
        crs = CRS.from_proj4(spec)
        #log_debug("crs:", crs)
        epsg = crs.to_epsg()    
        return str(epsg)


    def parse_map(self):
        '''
        <?xml version="1.0" encoding="UTF-8"?>
        <map xmlns="http://openorienteering.org/apps/mapper/xml/v2" version="9">
        <notes></notes>
        <georeferencing scale="10000" grid_scale_factor="0.9996" auxiliary_scale_factor="1" declination="11.53" grivation="11.55">
            <projected_crs id="UTM"><spec language="PROJ.4">+proj=utm +datum=WGS84 +zone=11
                </spec><parameter>11 N</parameter><ref_point x="496080" y="3791245.000104"/>
            </projected_crs>
            <geographic_crs id="Geographic coordinates"><spec language="PROJ.4">+proj=latlong +datum=WGS84
                </spec><ref_point_deg lat="34.26233857" lon="-117.04257955"/>
            </geographic_crs>
        </georeferencing>
        '''
        doc = minidom.parse(self.mapfile)
        if doc.getElementsByTagName('georeferencing') is None:
            print("Notice: No georeferencing specified in map file - using input coordinates!")
            return False
        
        tag_georef = doc.getElementsByTagName('georeferencing')[0]
        mapscale = tag_georef.getAttribute('scale')
        self.mapscale = float(mapscale)
        declination = tag_georef.getAttribute('declination')
        if not declination:
            declination = 0
        self.declination = float(declination)
        grivation = tag_georef.getAttribute('grivation') 
        print("\nMap Scale: ", self.mapscale, "\nDeclination: ", self.declination, " (Grivation: ", grivation, ")")

        tag_projcrs = doc.getElementsByTagName('projected_crs')[0]
        prjid = tag_projcrs.getAttribute('id')
        if prjid.lower() == 'local':
            print("Notice: No coordinate system specified in map file - using Local coordinates!")

        if tag_projcrs.getElementsByTagName('ref_point'):
            tag_refpoint = tag_projcrs.getElementsByTagName('ref_point')[0]
            ref_x = tag_refpoint.getAttribute('x')
            self.ref_x = float(ref_x)
            ref_y = tag_refpoint.getAttribute('y')
            self.ref_y = float(ref_y)
            print("\nRef: " "\nX: ", ref_x, "\nY: ", ref_y)
        
        if tag_projcrs.getElementsByTagName('spec'):
            tag_spec = tag_projcrs.getElementsByTagName('spec')[0]
            language = tag_spec.getAttribute('language')
            proj4spec = tag_spec.firstChild.nodeValue.strip()
            print("Coordinate system: ", proj4spec.replace('\n',''))

            tag_parameter = tag_projcrs.getElementsByTagName('parameter')[0]
            param = tag_parameter.firstChild.nodeValue.strip()  # always zone?
        else:
            proj4spec = None

        if doc.getElementsByTagName('geographic_crs'):
            tag_geocrs = doc.getElementsByTagName('geographic_crs')[0]
            crsid = tag_geocrs.getAttribute('id')
            tag_refpointdeg = tag_geocrs.getElementsByTagName('ref_point_deg')[0]
            lat = tag_refpointdeg.getAttribute('lat')
            lon = tag_refpointdeg.getAttribute('lon')
            print("Id: ", crsid, "\nLat: ", lat, "\nLon: ", lon)

            lat = float(lat)
            isSouth = False
            if lat < 0: # or param "S"
                isSouth = True

        # Get EPSG code
        if proj4spec and not self.epsg:
            self.epsg = self.get_epsg(proj4spec, isSouth)
            log_debug("EPSG:", self.epsg)


    def has_point(self, xyt, points):
        ''' returns # of times xy coord in points list '''
        n = 0
        for p in points:
            if xyt == p:
                n+=1
        return n


    def add_curvepts(self, path, points, step):
        ''' adds coords along curve '''
        for x in np.arange(0, 1, step):
            pt = path.point(x)
            if pt:
                x = np.real(pt)
                y = np.imag(pt)
                xyt = tuple((x,y))
                if self.has_point(xyt, points) < 1: 
                    points.append(xyt)
        if x < 1:  # last segment (outside of step interval)
            pt = path.point(1)
            if pt:
                x = np.real(pt)
                y = np.imag(pt)
                xyt = tuple((x,y))
                if self.has_point(xyt, points) < 2:
                    points.append(xyt)
        return len(points)


    def svg2geojson(self):
        paths, attributes, svg_attributes = svg2paths2(self.infile)
        #log_debug(svg_attributes)
        path = paths[0]
        path_attribs = attributes[0]
        #log_debug(path)
        #log_debug(path_attribs)
        
        xmin, xmax, ymin, ymax = None, None, None, None
        points = []
        num_paths = 0
        try:
            # Get graphic dimensions
            for p in paths:
                p_xmin, p_xmax , p_ymin, p_ymax = p.bbox()
                #log_debug("p bnd: ",p_xmin, p_ymin, p_xmax, p_ymax)
                if xmin is None or p_xmin < xmin:
                    xmin = p_xmin
                if xmax is None or p_xmax > xmax:
                    xmax = p_xmax
                if ymin is None or p_ymin < ymin:
                    ymin = p_ymin
                if ymax is None or p_ymax > ymax:
                    ymax = p_ymax
                num_paths+=1
        except ValueError:
            raise ValueError("Unable to parse SVG - Try releasing compound paths")

        log_debug("#paths: ", num_paths)
        log_debug("bnd: ",xmin, ymin, xmax, ymax)

        # Determine scaling of page to map units
        width_px = xmax - xmin
        height_px = ymax - ymin
        log_debug("width px: ", width_px)
        log_debug("height px: ", height_px)
        page_d = self.width
        page_d1 = page_d
        isWidth = True
        if self.height >= page_d:
            isWidth = False
            page_d = self.height
        if self.map_units.lower() == 'm':
            page_d1 = page_d
            page_d = page_d / (100 * self.unpcm)  # cm->m
        map_d = page_d / (1 / self.mapscale)
        print(page_d1, self.page_units, "->", map_d, "map units")
        
        if isWidth:
            sx = map_d / width_px
            sy = sx  # *** assume uniform scaling
            pxpin = width_px / (self.width * self.unpin)
        else:
            sy = map_d / height_px
            sx = sy
            pxpin = height_px / (self.height * self.unpin)
        log_debug("pxpin: ", pxpin)
        
        # Determine center coord
        cx = xmin+(width_px/2)
        cy = ymin+(height_px/2)
        pt_cen = np.complex(cx, cy)

        features = []
        i = 0
        print("Converting ", end='')
        for p in paths:
            log_debug("path i: ", i)
            time.sleep(0.1)
            print(".", end="", flush=True)
            stroke = ''
            fill = ''
            #log_debug(attributes[i])
            if 'style' in attributes[i]:
                style = attributes[i]['style']  # CSS
                log_debug("style:", style)
                if 'stroke:' in style:
                    stroke = style.split('stroke:')[1].split(';')[0]
                if 'fill:' in style:
                    fill = style.split('fill:')[1].split(';')[0]

            # Rotate CCW
            if self.rotation != 0:
                rotation = self.rotation
            else:
                rotation = self.declination
            if rotation != 0: 
                p = p.rotated(rotation, pt_cen) 
            
            # Scale 
            p = p.scaled(sx, sy, origin=pt_cen)

            # Determine resolution for interpolation of curves to lines
            # Notice this is in scaled coords
            p_xmin, p_xmax , p_ymin, p_ymax = p.bbox()
            width_px = p_xmax - p_xmin
            height_px = p_ymax - p_ymin 
            if width_px >= height_px:  # use longest side
                side = width_px
            else:
                side = height_px
            dots = (side / pxpin) * self.dpi
            log_debug("side px: ", side, "dots: ", dots)
            
            # magic number derived to fit different size curves
            if side > 0 or dots > 0:
                xx = math.sqrt(side/dots)*20
                if xx == 0:
                    xx = 1
                dpi_adjust = math.sqrt(side) / math.sqrt(xx)
                step = (side / (dots * side)) * dpi_adjust
                log_debug("dpi_adjust", dpi_adjust, "step", step)
            else:
                step = 0
            if step < 0.001:
                print("* Notice: reducing step (",i,")", step,"-> 0.001")
                step = 0.001
            
            points = []
            points_utm = []
            npts = 0
            for n in range(len(p)):
                #log_debug("n: ",n)
                isCurve = False

                if i in self.skip_list:
                    print("* Notice: skipping i:", i)
                    break
                
                # Get path type
                #log_debug(p)
                '''
                Path(Arc(start=(-70.1
                Path(Line(start=(677.3
                Path(CubicBezier(start=(-196.0
                Path(QuadraticBezier(start=(-28.3
                '''
                p_str = str(p)
                if len(p_str) > 0:
                    p_type = p_str.split('Path(')[1].split('(start=')[0]
                else:
                    p_type = "?"

                if p_type == 'Line':
                    pt1 = p[n].start
                    pt2 = p[n].end
                    #log_debug(n,": ",pt1,",",pt2)
                    x1 = np.real(pt1)
                    y1 = np.imag(pt1)
                    xyt = tuple((x1,y1))
                    if self.has_point(xyt, points) < 1:  # add only non redundant points
                        points.append(xyt)
                    x2 = np.real(pt2)
                    y2 = np.imag(pt2)
                    xyt = tuple((x2,y2))
                    if self.has_point(xyt, points) < 2:
                        points.append(xyt)
                elif p_type == 'Arc' or p_type == 'CubicBezier' or p_type == 'QuadraticBezier':
                    ###if isinstance(p[n], Line): print("line segment: ",i, n)
                    isCurve = True
                    m = self.add_curvepts(p, points, step)
                else:
                    print("\n* NOTICE: Unknown path type *")

            npts = len(points) - npts
            log_debug("#points: ",npts)

            if npts > 1:
                
                # Invert Y-axis
                points = [(p[0], ymax - p[1]) for p in points]
                
                # Shift origin to projected crs (UTM)
                points_shift = []
                for p in points:
                    points_shift.append(tuple((p[0]+self.ref_x, p[1]+self.ref_y)))
                points_utm.extend(points_shift)

                # Create geojson feature
                geom = LineString(points_utm)
                features.append(Feature(geometry=geom, properties={"id":i, "npts":npts, "stroke":stroke, "fill":fill}))
            
            i+=1
        print('\n.')
        return features
    

#------------------------------------------------------------------------------
def main(args):
    global DEBUG 
    DEBUG = False
    if args.debug: 
        if args.debug.lower() == 'y': DEBUG = True

    # Create converter object instance
    conv = Converter(args.i, args.o, args.m, args.wd, args.ht, args.u, args.dpi, args.rotation, args.epsg, args.skip_list)

    # Parse OOM mapfile
    if conv.mapfile:
        conv.parse_map()
    else:
        print("Notice: No map file specified - using input coordinates!")

    # Convert SVG to geojson features
    features = conv.svg2geojson()

    # Prepare geosjon
    if conv.epsg:
        crs_epsg = { "type": "name", "properties": { "name": "EPSG:"+conv.epsg } }
        feature_collection = FeatureCollection(features, crs=crs_epsg)
    else:
        feature_collection = FeatureCollection(features)

    # Write geojson file
    print("\nCreating output file: ", conv.outfile)
    with open(conv.outfile, 'w') as f:
       dump(feature_collection,f)
    f.close()


def log_debug(*s):
    if DEBUG: print(s)

def usage():
    return '''
    Example: python3 svg2omap.py -i i_love_orienteering_2.svg -m 'complete map.omap' -wd 3 -dpi 500
    '''

def set_args(p):
    p.add_argument('-i', type=str, required=True,
        help="SVG input file.")
    p.add_argument('-o', type=str, required=False,
        help="Output geojson file (default: input *.geojson).")
    p.add_argument('-m', type=str, required=False,
        help="OOM file identifying map scale, CRS and declination (default: SVG coords).")
    p.add_argument('-wd', type=float, required=False,
        help="Input graphic width (default: SVG coords).")
    p.add_argument('-ht', type=float, required=False,
        help="Input graphic height (default: SVG coords).")
    p.add_argument('-u', choices=['mm', 'cm', 'in', 'pt'], required=False,
        help="Units for height/width (default: cm).")
    p.add_argument('-dpi', type=int, required=False,
        help="Resolution for converting curve paths incl text (default: 300).")
    p.add_argument('-rotation', type=float, required=False,
        help="Rotation counterclockwise (default: map declination).")
    p.add_argument('-epsg', type=int, required=False,
        help="EPSG code (default: map coordinate system).")
    p.add_argument('-skip_list', type=str, required=False,
        help="List of id's to ignore. Ex '0,3,9' (default: None).")
    p.add_argument('-debug', choices=['n', 'y'], required=False,
        help="Print debug statements (default: No).")
    
    
if __name__ == "__main__":

    # Handle input arguments
    p = argparse.ArgumentParser(description="Converts SVG to geojson (for OpenOrienteering Mapper).", epilog=usage())
    set_args(p)
    args = p.parse_args()
    
    main(args)

    sys.exit(0)
