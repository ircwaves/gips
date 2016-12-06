#!/usr/bin/env python
import argparse
import sys
import os
import gips
# Setup django
#proj_path = "/home/remery/Projects/GipsAlg/gips/gips/inventory"
#sys.path.append(proj_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gips.inventory.orm.settings")
#os.chdir(proj_path)
import django
django.setup()
from gips.inventory.dbinv.models import Result, DataVariable, Vector
from gips import settings
sys.path.append(settings.GIPSBIN_PATH)
from zonalsummary import ZonalSummary


def make_result(result, g_dv, g_site, source):
    key = result[0]
    bands = result[1]

    date = key[0]
    fid = int(key[2])

    for band in bands.keys():
        stats = bands[band]

        minimum = float(stats[0]) if stats[0] != 'nan' else None
        maximum = float(stats[1]) if stats[1] != 'nan' else None
        mean = float(stats[2]) if stats[2] != 'nan' else None
        sd = float(stats[3]) if stats[3] != 'nan' else None
        skew = float(stats[4]) if stats[4] != 'nan' else None
        count = float(stats[5]) if stats[5] != 'nan' else None

        try:
            vector = Vector.objects.get(source=source, fid=fid)
        except:
            error = '''Could not find Vector without 
                    src/fid {}/{}'''.format(source, fid)
            print error
            vector = None

        r = Result(
            date=date,
            fid=fid,
            minimum=minimum,
            maximum=maximum,
            mean=mean,
            sd=sd,
            skew=skew,
            count=count,
            product=g_dv,
            site=g_site,
            vector=vector
        )
        r.save()


def get_product(prod):
    try:
        dv = DataVariable.objects.get(name=prod)
    except django.core.exceptions.ObjectDoesNotExist:
        print 'Product with name "{}" does not exist'.format(prod)
        exit(1)
    
    return dv


def main():
    path = os.path.dirname(os.path.abspath(__file__))
    desc = '''A wrapper for the ZonalSummary tool which creates Result objects
    from the output.'''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-s',
        '--site',
        required=True,
        help='GeoKit site requesting data'
    )
    parser.add_argument(
        '-p',
        '--product',
        required=True,
    )
    parser.add_argument(
        '-d',
        '--projdir',
        required=True,
        help='Gips inventory directory',
        default=path

    )
    parser.add_argument(
        '-r',
        '--source',
        help='Source of shapes',
        required=True
    )

    init_args = parser.parse_args()
    projdir = init_args.projdir
    g_site = init_args.site
    g_dv = get_product(init_args.product)
    a = ZonalSummary(projdir=projdir)

    source = init_args.source

    proj_name = os.path.basename(os.path.dirname(projdir))

    args = {
        'stats': ['min', 'max', 'mean', 'sd', 'skew', 'count'],
        'shapefile': None,
        'outdir': None,
        'rasterpaths': None,
        'bands': [g_dv.band_number],
        'percentiles': [],
        'filter': None,
        'passthrough': False,
        'products': [g_dv.product],
        'nodata': None,
        'raster_dates': [],
        #TODO: Make this configurable
        'processes': 1,
        'outfile': None,
        'alltouch': False,
        'continue': False,

    }

    results = a.run(**args)
    for r in results:
        make_result(r, g_dv, g_site, source)
        return

if __name__ == "__main__":
    main()
