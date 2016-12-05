import logging

import pytest
import envoy

from .util import *

logger = logging.getLogger(__name__)

pytestmark = sys # skip everything unless --sys

# changing this will require changes in expected/
STD_ARGS = ('merra', '-s', NH_SHP_PATH, '-d', '2012-12-01,2012-12-10', '-v', '4')

driver = 'merra'

@pytest.fixture
def setup_merra_data(pytestconfig):
    """Use gips_inventory to ensure presence of PRISM data in the data repo."""
    if not pytestconfig.getoption('setup_repo'):
        logger.debug("Skipping repo setup per lack of option.")
        return
    logger.info("Downloading MERRA data . . .")
    cmd_str = 'gips_inventory ' + ' '.join(STD_ARGS) + ' --fetch'
    outcome = envoy.run(cmd_str)
    logger.info("MERRA data download complete.")
    if outcome.status_code != 0:
        raise RuntimeError("MERRA data setup via `gips_inventory` failed",
                           outcome.std_out, outcome.std_err, outcome)


def t_inventory(setup_merra_data, repo_env, expected):
    """Test `gips_inventory merra` and confirm recorded output is given."""
    actual = repo_env.run('gips_inventory', *STD_ARGS)
    assert expected == actual


def t_process(setup_merra_data, repo_env, expected):
    """Test gips_process on prism data."""
    process_actual = repo_env.run('gips_process', *STD_ARGS)
    inventory_actual = envoy.run('gips_inventory ' + ' '.join(STD_ARGS))
    assert expected == process_actual and inventory_actual.std_out == expected._inv_stdout

# TODO convert the rest of this test script
"""
#!/bin/bash

[ -z "$GIPSTESTPATH" ] && GIPSTESTPATH="."

ARGS="-s $GIPSTESTPATH/NHseacoast.shp -d 2012-12-01,2012-12-10 -v 4"

gips_info Merra 

# mosaic
gips_project merra $ARGS --res 100 100 --outdir merra_project --notld
gips_stats merra_project/*

# mosaic without warping
gips_project merra $ARGS --outdir merra_project_nowarp --notld
gips_stats merra_project_nowarp

# warp tiles
gips_tiles merra $ARGS --outdir merra_warped_tiles --notld
gips_stats merra_warped_tiles/*

# copy tiles
#gips_tiles merra -t h12v04 -d 2012-12-01,2012-12-10 -v 4 --outdir modis_tiles --notld
#gips_stats modis_tiles
"""
