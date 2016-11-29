#!/usr/bin/env python

#from install_cas_client import install_cas_client
#install_cas_client()

from install_basic_client import install_basic_client

#install_basic_client(user='bobbyhbraswell', passwd='Coffeedog_2', use_netrc=False)

URI = "urs.earthdata.nasa.gov"
USER = "bobbyhbraswell"
PASSWD = "Coffeedog_2"

install_basic_client(uri=URI, user=USER, passwd=PASSWD, use_netrc=False)

from pydap.client import open_url


loc = "http://goldsmr4.gesdisc.eosdis.nasa.gov:80/opendap/MERRA2/M2T1NXSLV.5.12.4/1996/10/MERRA2_200.tavg1_2d_slv_Nx.19961003.nc4"

#loc0 = "http://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/2010/01/MERRA2_300.tavg1_2d_slv_Nx.20100101.nc4"
#loc1 = "http://bobbyhbraswell:Coffeedog_2@goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/2010/01/MERRA2_300.tavg1_2d_slv_Nx.20100101.nc4"


asset = "T2M"

dataset = open_url(loc)


var = dataset[asset]

print var.shape

print var[0,10:12,10:12]




