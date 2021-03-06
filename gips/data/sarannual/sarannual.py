#!/usr/bin/env python
################################################################################
#    GIPS: Geospatial Image Processing System
#
#    AUTHOR: Matthew Hanson
#    EMAIL:  matt.a.hanson@gmail.com
#
#    Copyright (C) 2014-2018 Applied Geosolutions
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
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

import os
import datetime

import gippy
from gips.data.core import Repository, Asset, Data
from gips.utils import RemoveFiles, VerboseOut
from gips import utils


class sarannualRepository(Repository):
    name = 'SARAnnual'
    description = 'Synthetic Aperture Radar PALSAR Mosaics'
    _datedir = '%Y'

    @classmethod
    def feature2tile(cls, feature):
        """ Get tile designation from a geospatial feature (i.e. a row) """
        fldindex_lat = feature.GetFieldIndex("lat")
        fldindex_lon = feature.GetFieldIndex("lon")
        lat = int(feature.GetField(fldindex_lat) + 0.5)
        lon = int(feature.GetField(fldindex_lon) - 0.5)
        if lat < 0:
            lat_h = 'S'
        else:
            lat_h = 'N'
        if lon < 0:
            lon_h = 'W'
        else:
            lon_h = 'E'
        tile = lat_h + str(abs(lat)).zfill(2) + lon_h + str(abs(lon)).zfill(3)
        return tile


class sarannualAsset(Asset):
    Repository = sarannualRepository
    _sensors = {
        #'AFBS': 'PALSAR FineBeam Single Polarization',
        'PALSAR': {'description': 'PALSAR Mosaic (FineBeam Dual Polarization)'},
        #'AWB1': 'PALSAR WideBeam (ScanSAR Short Mode)',
        #'JFBS': 'JERS-1 FineBeam Single Polarization'
    }
    _assets = {
        'MOS': {
            'startdate': datetime.date(1, 1, 1),
            'latency': 0,
            'pattern': r'^.{7}_.{2}_MOS\.tar\.gz$'
        },
        'FNF': {
            'startdate': datetime.date(1, 1, 1),
            'latency': 0,
            'pattern': r'^.{7}_.{2}_FNF\.tar\.gz$'
        },
    }

    _defaultresolution = [0.00044444444, 0.00044444444]

    def __init__(self, filename):
        """ Inspect a single file and get some basic info """
        super(sarannualAsset, self).__init__(filename)
        bname = os.path.basename(filename)
        self.asset = bname[11:14]
        self.tile = bname[0:7]
        self.sensor = 'PALSAR'
        self.date = datetime.datetime.strptime(bname[8:10], '%y')
        self.rootname = bname[0:10]

    def extract(self, filenames=[]):
        """ Extract filesnames from asset """
        files = super(sarannualAsset, self).extract(filenames)
        datafiles = {}
        for f in files:
            bname = os.path.basename(f)
            if f[-3:] != 'hdr':
                bandname = bname[len(self.rootname) + 1:]
                datafiles[bandname] = f
        return datafiles


class sarannualData(Data):
    """ Tile of data """
    name = 'SARAnnual'
    version = '0.9.0'
    Asset = sarannualAsset

    _pattern = '*'
    _products = {
        'sign': {
            'description': 'Sigma nought (radar backscatter coefficient)',
            'assets': ['MOS'],
        },
        'fnf': {
            'description': 'Forest/NonForest Mask',
            'assets': ['FNF'],
        }
    }

    def meta(self, tile):
        """ Get metadata for this tile """
        return {'CF': -83.0}

    def find_files(self):
        """ Search path for valid files """
        filenames = super(sarannualData, self).find_files()
        filenames[:] = [f for f in filenames if os.path.splitext(f)[1] != '.hdr']
        return filenames

    def process(self, *args, **kwargs):
        """ Process all requested products for this tile """
        products = super(sarannualData, self).process(*args, **kwargs)
        if len(products) == 0:
            return

        self.basename = self.basename + '_' + self.sensor_set[0]
        for key, val in products.requested.items():
            fname = os.path.join(self.path, self.basename + '_' + key)
            # Verify that asset exists
            a_type = self._products[val[0]]['assets'][0]
            a_obj = self.assets.get(a_type)
            if a_obj is None:
                utils.verbose_out("Asset {} doesn't exist for tile {}".format(a_type, self.id), 3)
                continue
            datafiles = None
            with utils.error_handler("Error extracting files from asset {}".format(a_obj.filename),
                                     continuable=True):
                datafiles = a_obj.extract()
            if datafiles is None:
                continue

            if val[0] == 'sign':
                bands = [datafiles[b] for b in ["sl_HH", "sl_HV"] if b in datafiles]
                if len(bands) > 0:
                    img = gippy.GeoImage(bands)
                    img.SetNoData(0)
                    mask = gippy.GeoImage(datafiles['mask'], False)
                    img.AddMask(mask[0] == 255)
                    imgout = gippy.GeoImage(fname, img, gippy.GDT_Float32)
                    imgout.SetNoData(-32768)
                    for b in range(0, imgout.NumBands()):
                        imgout.SetBandName(img[b].Description(), b + 1)
                        (img[b].pow(2).log10() * 10 - 83.0).Process(imgout[b])
                    fname = imgout.Filename()
                    img = None
                    imgout = None
                    [RemoveFiles([f], ['.hdr', '.aux.xml']) for k, f in datafiles.items() if k != 'hdr']
            if val[0] == 'fnf':
                if 'C' in datafiles:
                    # rename both files to product name
                    os.rename(datafiles['C'], fname)
                    os.rename(datafiles['C'] + '.hdr', fname + '.hdr')
                    img = gippy.GeoImage(fname)
                    img.SetNoData(0)
                    img = None
            self.AddFile(self.sensor_set[0], key, fname)
