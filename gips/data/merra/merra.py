#!/usr/bin/env python
################################################################################
#    GIPS: Geospatial Image Processing System
#
#    AUTHOR: Matthew Hanson
#    EMAIL:  matt.a.hanson@gmail.com
#
#    Copyright (C) 2014 Applied Geosolutions
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program. If not, see <http://www.gnu.org/licenses/>
################################################################################

from __future__ import print_function

import os
import re
import datetime
import time

import urllib, urllib2
import requests

import signal

import numpy as np
from netCDF4 import Dataset

from osgeo import gdal

import gippy
from gips.data.core import Repository, Asset, Data
from gips.utils import VerboseOut, basename, open_vector
from gips import utils


# TODO: delete the line below
from pdb import set_trace


#MISSING = 9.999999870e+14

class Timeout():
    """Timeout class using ALARM signal."""

    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()


def write_raster(fname, data, proj, geo, meta, bandnames, nodata):
    driver = gdal.GetDriverByName('GTiff')
    try:
        (nband, ny, nx) = data.shape
    except:
        # TODO error-handling-fix: leave as-is but report the error
        nband = 1
        (ny, nx) = data.shape
        data = data.reshape(1, ny, nx)
    # create data type
    gdal.GDT_UInt8 = gdal.GDT_Byte
    np_dtype = str(data.dtype)
    typestr = 'gdal.GDT_' + np_dtype.title().replace('Ui', 'UI')
    dtype = eval(typestr)
    tfh = driver.Create(fname, nx, ny, nband, dtype, [])
    tfh.SetGeoTransform(geo)
    tfh.SetMetadata(meta)
    tfh.SetProjection(proj)
    assert len(bandnames) == nband
    for i in range(nband):
        band = tfh.GetRasterBand(i+1)
        assert len(bandnames) == nband, "wrong number of band names"
        band.SetDescription(bandnames[i])        
        band.SetNoDataValue(nodata)
        band.WriteArray(data[i])
    tfh = None


class merraRepository(Repository):
    name = 'merra'
    description = 'Modern Era Retrospective-Analysis for Research and Applications (weather and climate)'
    _tile_attribute = 'tileid'

    @classmethod
    def tile_bounds(cls, tile):
        """ Get the bounds of the tile (in same units as tiles vector) """
        vector = open_vector(cls.get_setting('tiles'))
        features = vector.where('tileid', tile)
        if len(features) != 1:
            raise Exception('there should be a single tile with id %s' % tile)
        extent = features[0].Extent()
        return [extent.x0(), extent.y0(), extent.x1(), extent.y1()]


class merraAsset(Asset):
    Repository = merraRepository

    _sensors = {
        'merra': {
            'description': 'Modern Era Retrospective-analysis for Research and Applications',
        }
    }

    _bandnames = ['%02d30GMT' % i for i in range(24)]

    _asset_re_pattern = "MERRA2_\d\d\d\.{name}\.%04d%02d%02d.nc4"
    _asset_pattern = "MERRA2_???.{name}.????????.nc4"

    _assets = {
        # MERRA2 SLV
        ## TS (Surface skin temperature)
        ## T2M (Temperature at 2 m above the displacement height)
        ## T10M (Temperature at 10 m above the displacement height)
        ## PS (Time averaged surface pressure in Pa)
        ## QV2M (Specific humidity at 2 m above the displacement height in kg kg-1)
        'SLV': {
            'shortname': 'M2T1NXSLV',
            'description': '2d,1-Hourly,Time-Averaged,Single-Level,Assimilation,Single-Level Diagnostics V5.12.4',
            'url': 'http://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXSLV.5.12.4',
            'pattern': _asset_pattern.format(name='tavg1_2d_slv_Nx'),
            're_pattern': _asset_re_pattern.format(name='tavg1_2d_slv_Nx'),
            'startdate': datetime.date(1980, 1, 1),
            'latency': 60,
        },
        # MERRA2 FLX
        ## PRECTOT (Total Precipitation in kg m-2 s-1)'
        ## SPEED (3-dimensional wind speed for surface fluxes in m s-1)'
        'FLX': {
            'shortname': 'M2T1NXFLX',
            'description': '2d,1-Hourly,Time-Averaged,Single-Level,Assimilation,Surface Flux Diagnostics V5.12.4',
            'url': 'http://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXFLX.5.12.4',
            'pattern': _asset_pattern.format(name='tavg1_2d_flx_Nx'),
            're_pattern': _asset_re_pattern.format(name='tavg1_2d_flx_Nx'),
            'startdate': datetime.date(1980, 1, 1),
            'latency': 60,
        },
        # MERRA2 RAD
        ## SWGDN: Surface incident shortwave flux (W m-2)
        'RAD': {
            'shortname': 'M2T1NXRAD',
            'description': '2d,1-Hourly,Time-Averaged,Single-Level,Assimilation,Radiation Diagnostics V5.12.4',
            'url': 'http://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXRAD.5.12.4',
            'pattern': _asset_pattern.format(name='tavg1_2d_rad_Nx'),
            're_pattern': _asset_re_pattern.format(name='tavg1_2d_rad_Nx'),
            'startdate': datetime.date(1980, 1, 1),
            'latency': 60,
        }   
    }


        # MERRA2 CONST
        # http://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2_MONTHLY/M2C0NXASM.5.12.4/1980/MERRA2_101.const_2d_asm_Nx.00000000.nc4
        #'FRLAND': {
        #    'description': 'Land Fraction',
        #    'pattern': 'MERRA_FRLAND_*.tif',
        #    'url': 'http://goldsmr4.sci.gsfc.nasa.gov:80/opendap/MERRA2_MONTHLY/M2C0NXASM.5.12.4',
        #    'source': 'MERRA2_%s.const_2d_asm_Nx.%04d%02d%02d.nc4',
        #    'startdate': datetime.date(1980, 1, 1),
        #    'latency': 0,
        #    'bandnames': ['FRLAND']
        #}
        #'PROFILE': {
        #     'description': 'Atmospheric Profile',
        #     'pattern': 'MAI6NVANA_PROFILE_*.tif',
        #     'url': 'http://goldsmr5.sci.gsfc.nasa.gov/opendap/MERRA2/M2I6NVANA.5.12.4',
        #     'source': 'MERRA2_%s.inst6_3d_ana_Nv.%04d%02d%02d.nc4',
        #     'startdate': datetime.date(1980, 1, 1),
        #     'latency': 60,
        #     'bandnames': ['0000GMT', '0600GMT', '1200GMT', '1800GMT']
        #},
        # 'PROFILEP': {
        #     'description': 'Atmospheric Profile',
        #     'pattern': 'MAI6NVANA_PROFILE_*.tif',
        #     'url': 'http://goldsmr3.sci.gsfc.nasa.gov:80/opendap/MERRA/MAI6NPANA.5.2.0',
        #     'source': 'MERRA%s.prod.assim.inst6_3d_ana_Np.%04d%02d%02d.hdf',
        #     'startdate': datetime.date(1980, 1, 1),
        #     'latency': 60,
        #     'bandnames': ['0000GMT', '0600GMT', '1200GMT', '1800GMT']
        # },

        
    def __init__(self, filename):
        """ Inspect a single file and get some metadata """
        super(merraAsset, self).__init__(filename)
        self.sensor = 'merra'
        self.tile = 'h01v01'
        parts = basename(filename).split('.')

        #print(filename)
        #print(parts)
        #print(parts[1].split('_'))

        self.asset = parts[1].split('_')[2].upper()
        self.version = int(parts[0].split('_')[1])
        self.date = datetime.datetime.strptime(parts[2], '%Y%m%d').date()

    # url: http://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXSLV.5.12.4
    # pattern: "MERRA2_???.tavg1_2d_slv_Nx.%04d%02d%02d.nc4"
    # fully: http://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXSLV.5.12.4/1983/06/MERRA2_100.tavg1_2d_slv_Nx.19830601.nc4
    # basename: MERRA2_100.tavg1_2d_slv_Nx.19830601

    @classmethod
    def fetch(cls, asset, tile, date):

        year, month, day = date.timetuple()[:3]

        username = cls.Repository.get_setting('username')
        password = cls.Repository.get_setting('password')

        mainurl = "%s/%04d/%02d/" % (cls._assets[asset]['url'], year, month)

        pattern = cls._assets[asset]['re_pattern'] % (year, month, day)
        cpattern = re.compile(pattern)
        
        err_msg = "Error downloading"
        with utils.error_handler(err_msg):
            listing = urllib.urlopen(mainurl).readlines()
        
        success = False
        for item in listing:
            # screen-scrape the content of the page and extract the full name of the needed file
            # (this step is needed because part of the filename, the creation timestamp, is
            # effectively random)
            if cpattern.search(item):
                if 'xml' in item:
                    continue
                name = cpattern.findall(item)[0]
                url = ''.join([mainurl, '/', name])
                outpath = os.path.join(cls.Repository.path('stage'), name)

                with utils.error_handler("Asset fetch error", continuable=True):

                    kw = {'timeout': 20}
                    kw['auth'] = (username, password)
                    response = requests.get(url, **kw)

                    if response.status_code != requests.codes.ok:
                        print('Download of', name, 'failed:', response.status_code, response.reason,
                              '\nFull URL:', url, file=sys.stderr)
                        return # might as well stop b/c the rest will probably fail too

                    with open(outpath, 'wb') as fd:
                        for chunk in response.iter_content():
                            fd.write(chunk)

                    utils.verbose_out('Retrieved %s' % name, 2)
                    success = True

        if not success:
            VerboseOut('Unable to find remote match for %s at %s' % (pattern, mainurl), 4)
        print("success!")

    def updated(self, newasset):
        '''
        Compare the version for this to that of newasset.
        Return true if newasset version is greater.
        '''
        return (self.sensor == newasset.sensor and
                self.tile == newasset.tile and
                self.date == newasset.date and
                self.version < newasset.version)


class merraData(Data):
    """ A tile of data (all assets and products) """
    name = 'merra'
    version = '1.0.0'
    Asset = merraAsset

    _geotransform = (-180.3125, 0.625, 0.0, 90.25, 0.0, -0.5)
    _projection = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
    
    _products = {

        #'FRLAND': {
        #    'description': 'Land Fraction (static map)',
        #    'assets': ['FRLAND']
        #},

        'tave': {
            'description': 'Ave daily air temperature data (K)',
            'assets': ['SLV'],
            'layers': ['T2M'],
            'bands': ['tave']
        },
        'tmin': {
            'description': 'Min daily air temperature data',
            'assets': ['SLV'],
            'layers': ['T2M'],
            'bands': ['tmin']
        },
        'tmax': {
            'description': 'Max daily air temperature data',
            'assets': ['SLV'],
            'layers': ['T2M'],
            'bands': ['tmax']
        },

        #'patm': {
        #    'description': 'Surface atmospheric pressure (mb)',
        #    'assets': ['PS']
        #},
        #'rhum': {
        #    'description': 'Relative humidity (%)',
        #    'assets': ['QV2M', 'PS', 'T2M']
        #},


        'prcp': {
            'description': 'Daily total precipitation (mm day-1)',
            'assets': ['FLX'],
            'layers': ['PRECTOT'],
            'bands': ['prcp']
        },

        #'wind': {
        #    'description': 'Daily mean wind speed (m s-1)',
        #    'assets': ['SPEED']
        #},
        #'shum': {
        #    'description': 'Relative humidity (kg kg-1)',
        #    'assets': ['QV2M']
        #},
        #'srad': {
        #    'description': 'Incident solar radiation (W m-2)',
        #    'assets': ['SWGDN']
        #},

        # BELOW NOT NEEDED?
        #'_temps': {
        #    'description': 'Air temperature data',
        #    'assets': ['TS', 'T2M', 'T10M']
        #},
        #'daily_weather': {
        #    'description': 'Climate forcing data, e.g. for DNDC',
        #    'assets': ['T2M', 'PRECTOT']
        #},
        #'profile': {
        #    'description': 'Atmospheric Profile',
        #    'assets': ['PROFILE'],
        #}

    }


    # @classmethod
    # def process_composites(cls, inventory, products, **kwargs):
    #     for product in products:
    #         cpath = os.path.join(cls.Asset.Repository.path('composites'), 'ltad')
    #         path = os.path.join(cpath, 'ltad')
    #         # Calculate AOT long-term multi-year averages (lta) for given day
    #         if product == 'ltad':
    #             for day in range(inventory.start_day, inventory.end_day + 1):
    #                 dates = [d for d in inventory.dates if int(d.strftime('%j')) == day]
    #                 filenames = [inventory[d].tiles[''].products['aod'] for d in dates]
    #                 fout = path + '%s.tif' % str(day).zfill(3)
    #                 cls.process_mean(filenames, fout)
    #         # Calculate single average per pixel (all days and years)
    #         if product == 'lta':
    #             filenames = glob.glob(path + '*.tif')
    #             if len(filenames) > 0:
    #                 fout = os.path.join(cls.Asset.Repository.path('composites'), 'lta.tif')
    #                 cls.process_mean(filenames, fout)
    #             else:
    #                 raise Exception('No daily LTA files exist!')

    # TODO: move this into Landsat or atmos module to support the wtemp pro
    #@classmethod
    #def lonlat2xy(cls, lon, lat):
    #    """ Convert from lon-lat to x-y in array """
    #    x = int(round((lon - cls._origin[0]) / cls._defaultresolution[0]))
    #    y = int(round((lat - cls._origin[1]) / cls._defaultresolution[1]))
    #    return (x, y)
    #
    #@classmethod
    #def profile(cls, lon, lat, dtime):
    #    """ Retrieve atmospheric profile directly from merra data via OpenDap """
    #    dataset = cls.Asset.opendap_fetch('PROFILE', dtime)
    #    (x, y) = cls.Asset.lonlat2xy(lon, lat)
    #    # TODO - I know these are hours (0, 6, 12, 18), but it's still an assumption
    #    times = [datetime.datetime.combine(dtime.date(), datetime.time(int(d / 60.0))) for d in dataset['time'][:]]
    #    unixtime = time.mktime(dtime.timetuple())
    #    timediff = numpy.array([unixtime - time.mktime(t.timetuple()) for t in times])
    #    timeind = numpy.abs(timediff).argmin()
    #    p = dataset['PS'][timeind, y, x].squeeze()
    #    pthick = dataset['DELP'][timeind, :, y, x].squeeze()[::-1]
    #    pressure = []
    #    for pt in pthick:
    #        pressure.append(p)
    #        p = p - pt
    #    pressure = numpy.array(pressure)
    #    inds = numpy.where(pressure > 0)
    #    data = {
    #        # Pa -> mbar
    #        'pressure': numpy.array(pressure)[inds] / 100.0,
    #        # Kelvin -> Celsius
    #        'temp': dataset['T'][timeind, :, y, x].squeeze()[::-1][inds] - 273.15,
    #        # kg/kg -> g/kg (Mass mixing ratio)
    #        'humidity': dataset['QV'][timeind, :, y, x].squeeze()[::-1][inds] * 1000,
    #        'ozone': dataset['O3'][timeind, :, y, x].squeeze()[::-1][inds] * 1000,
    #    }
    #    return data

    
    def getlonlat(self):
        """ return the center coordinates of the MERRA tile 
            used only by product temp_modis
        """
        hcoord = int(self.id[1:3])
        vcoord = int(self.id[4:])
        lon = -180. + (hcoord - 1) * 12. + 6.
        lat = 90. - vcoord * 10. - 5.
        return lon, lat

    def gmtoffset(self):
        """ return the approximate difference between local time and GMT
            used only by product temp_modis
        """
        lon = self.getlonlat()[0]
        houroffset = lon * (12. / 180.)
        return houroffset

    def write_reduced(self, prod, fun, fout, meta):
        """ apply a function to reduce to a daily value """
        assetname = self._products[prod]['assets'][0]
        layername = self._products[prod]['layers'][0]
        bandnames = self._products[prod]['bands']
        assetfile = self.assets[assetname].filename     

        ncroot = Dataset(assetfile)
        var = ncroot.variables[layername]

        missing = float(var.missing_value)
        scale = var.scale_factor
        assert scale == 1.0, "Handle non-unity scale functions"
        
        data = fun(var[:])
        data = np.flipud(data)

        geo = self._geotransform
        proj = self._projection                
        print('writing', fout)
        write_raster(fout, data, proj, geo, meta, bandnames, missing)

        
    def process(self, *args, **kwargs):
        """ create products """
        products = super(merraData, self).process(*args, **kwargs)
        if len(products) == 0:
            return
        bname = os.path.join(self.path, self.basename)
        sensor = "merra"

        for key, val in products.requested.items():
            fout = "%s_%s_%s.tif" % (bname, sensor, key)
            meta = {}
            VERSION = "1.0"
            meta['VERSION'] = VERSION
                
            if val[0] == "tave":
                fun = lambda x: x.mean(axis=0) - 273.15
                self.write_reduced(val[0], fun, fout, meta)

            elif val[0] == "tmin":
                fun = lambda x: x.min(axis=0) - 273.15
                self.write_reduced(val[0], fun, fout, meta)

            elif val[0] == "tmax":
                fun = lambda x: x.max(axis=0) - 273.15
                self.write_reduced(val[0], fun, fout, meta)

            elif val[0] == "prcp":
                fun = lambda x: x.mean(axis=0)*36.*24.*1000.
                self.write_reduced(val[0], fun, fout, meta)

                
            """
            if val[0] == "prcp":
                img = gippy.GeoImage(assets[0])
                imgout = gippy.GeoImage(fout, img, img.DataType(), 1)
                phourly = numpy.ma.MaskedArray(img.Read().squeeze())
                phourly.mask = (phourly == MISSING)
                prcp = phourly.mean(axis=0)
                prcp = prcp * 36. * 24. * 1000
                prcp[prcp.mask] = MISSING
                imgout[0].Write(numpy.array(prcp))
                imgout.SetBandName(val[0], 1)
                imgout.SetUnits('mm d-1')
                imgout.SetNoData(MISSING)

            if val[0] == "wind":
                img = gippy.GeoImage(assets[0])
                imgout = gippy.GeoImage(fout, img, img.DataType(), 1)
                hourly = numpy.ma.MaskedArray(img.Read().squeeze())
                hourly.mask = (hourly == MISSING)
                daily = hourly.mean(axis=0)
                # daily = daily * 1.0
                daily[daily.mask] = MISSING
                imgout[0].Write(numpy.array(daily))
                imgout.SetBandName(val[0], 1)
                imgout.SetUnits('m s-1')
                imgout.SetNoData(MISSING)

            if val[0] == "srad":
                img = gippy.GeoImage(assets[0])
                imgout = gippy.GeoImage(fout, img, img.DataType(), 1)
                hourly = numpy.ma.MaskedArray(img.Read().squeeze())
                hourly.mask = (hourly == MISSING)
                daily = hourly.mean(axis=0)
                # daily = daily * 1.0
                daily[daily.mask] = MISSING
                imgout[0].Write(numpy.array(daily))
                imgout.SetBandName(val[0], 1)
                imgout.SetUnits('W m-2')
                imgout.SetNoData(MISSING)

            if val[0] == "shum":
                img = gippy.GeoImage(assets[0])
                imgout = gippy.GeoImage(fout, img, img.DataType(), 1)
                hourly = numpy.ma.MaskedArray(img.Read().squeeze())
                hourly.mask = (hourly == MISSING)
                daily = hourly.mean(axis=0)
                # daily = daily * 1.0
                daily[daily.mask] = MISSING
                imgout[0].Write(numpy.array(daily))
                imgout.SetBandName(val[0], 1)
                imgout.SetUnits('kg kg-1')
                imgout.SetNoData(MISSING)

            if val[0] == "patm":
                img = gippy.GeoImage(assets[0])
                imgout = gippy.GeoImage(fout, img, img.DataType(), 1)
                hourly = numpy.ma.MaskedArray(img.Read().squeeze())
                hourly.mask = (hourly == MISSING)
                daily = hourly.mean(axis=0)
                daily = daily / 100.
                daily[daily.mask] = MISSING
                imgout[0].Write(numpy.array(daily))
                imgout.SetBandName(val[0], 1)
                imgout.SetUnits('mb')
                imgout.SetNoData(MISSING)

            if val[0] == "rhum":
                # based on 'QV2M', 'PS', 'T2M
                # qair2rh <- function(qair, temp, press = 1013.25){
                #     es <-  6.112 * exp((17.67 * temp)/(temp + 243.5))
                #     e <- qair * press / (0.378 * qair + 0.622)
                #     rh <- e / es
                #     rh[rh > 1] <- 1
                #     rh[rh < 0] <- 0
                #     return(rh)
                img = gippy.GeoImage(assets[0])
                qv2m = numpy.ma.MaskedArray(img.Read().squeeze()) # kg kg-1
                qv2m.mask = (qv2m == MISSING)
                img = gippy.GeoImage(assets[1])
                ps = numpy.ma.MaskedArray(img.Read().squeeze()) # Pa
                ps.mask = (ps == MISSING)
                img = gippy.GeoImage(assets[2])
                t2m = numpy.ma.MaskedArray(img.Read().squeeze()) # K
                t2m.mask = (t2m == MISSING)
                temp = t2m - 273.15
                press = ps/100.
                qair = qv2m
                es = 6.112*numpy.exp((17.67*temp)/(temp + 243.5))
                e = qair*press/(0.378*qair + 0.622)
                rh = 100. * (e/es)
                rh[rh > 100.] = 100.
                rh[rh < 0.] = 0.
                daily = rh.mean(axis=0)
                daily[daily.mask] = MISSING
                imgout = gippy.GeoImage(fout, img, img.DataType(), 1)
                imgout[0].Write(numpy.array(daily))
                imgout.SetBandName(val[0], 1)
                imgout.SetUnits('%')
                imgout.SetNoData(MISSING)

            if val[0] == "temp_modis":
                img = gippy.GeoImage(assets[0])
                imgout = gippy.GeoImage(fout, img, img.DataType(), 4)
                # Aqua AM, Terra AM, Aqua PM, Terra PM
                localtimes = [1.5, 10.5, 13.5, 22.5]
                strtimes = ['0130LT', '1030LT', '1330LT', '2230LT']
                hroffset = self.gmtoffset()
                # TODO: loop across the scene in latitude
                # calculate local time for each latitude column
                print 'localtimes', localtimes
                for itime, localtime in enumerate(localtimes):
                    print itime
                    picktime = localtime - hroffset
                    pickhour = int(picktime)
                    if pickhour < 0:
                        # next day local time
                        pickday = +1
                    elif pickhour > 24:
                        # previous day local time
                        pickday = -1
                    else:
                        # same day local time
                        pickday = 0
                    pickidx = pickhour % 24
                    print "localtime", localtime
                    print "picktime", picktime
                    print "pickhour", pickhour
                    print "pickday", pickday
                    print "pickidx", pickidx
                    img[pickidx].Process(imgout[itime])
                    obsdate = self.date + datetime.timedelta(pickday)
                    descr = " ".join([strtimes[itime], obsdate.isoformat()])
                    imgout.SetBandName(descr, itime + 1)

            #elif val[0] == 'profile':
            #    pass

            """

            # add product to inventory
            #self.AddFile(sensor, key, imgout.Filename())
            self.AddFile(sensor, key, fout)

