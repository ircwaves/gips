"""Unit tests for core functions found in gips.core and gips.data.core."""

import sys
from datetime import datetime

import pytest
import mock

import gips
from gips import core
from gips.data import core as data_core
from gips.data.landsat.landsat import landsatRepository, landsatData
from gips.data.landsat import landsat
from gips.inventory import dbinv

def t_repository_find_tiles_normal_case(mocker, orm):
    """Test Repository.find_tiles using landsatRepository as a guinea pig."""
    m_list_tiles = mocker.patch('gips.data.core.dbinv.list_tiles')
    expected = [u'tile1', u'tile2', u'tile3'] # list_tiles returns unicode
    m_list_tiles.return_value = expected
    actual = landsatRepository.find_tiles()
    assert expected == actual


def t_repository_find_tiles_error_case(mocker, orm):
    """Confirm Repository.find_tiles quits on error."""
    m_list_tiles = mocker.patch('gips.data.core.dbinv.list_tiles')
    m_list_tiles.side_effect = RuntimeError('AAAAAAAAAAH!') # intentionally break list_tiles

    with pytest.raises(RuntimeError):
        landsatRepository.find_tiles()


def t_repository_find_dates_normal_case(mocker, orm):
    """Test Repository.find_dates using landsatRepository as a guinea pig."""
    m_list_dates = mocker.patch('gips.data.core.dbinv.list_dates')
    dt = datetime
    expected = [dt(1900, 1, 1), dt(1950, 10, 10), dt(2000, 12, 12)]
    m_list_dates.return_value = expected
    actual = landsatRepository.find_dates('some-tile')
    assert expected == actual


@pytest.mark.skip(reason="Letting exception bubble up for now; if that changes un-skip this test.")
def t_repository_find_dates_error_case(mocker):
    """Confirm Repository.find_dates quits on error."""
    m_list_dates = mocker.patch('gips.data.core.dbinv.list_dates')
    m_list_dates.side_effect = Exception('AAAAAAAAAAH!') # intentionally break list_dates

    # confirm call was still a success via the righ code path
    with pytest.raises(SystemExit):
        landsatRepository.find_dates('some-tile')


@pytest.mark.parametrize('add_to_db', (False, True))
def t_data_add_file(orm, mocker, add_to_db):
    """Basic test for Data.AddFile; calls it once then tests its state."""
    m_uoap = mocker.patch('gips.data.core.dbinv.update_or_add_product')
    t_sensor    = 'test-sensor'
    t_product   = 'test-product'
    t_filename  = 'test-filename.tif'
    lsd = landsatData('test-tile', datetime(1955, 11, 5), search=False)

    lsd.AddFile(t_sensor, t_product, t_filename, add_to_db)

    # alas, cleanest to make multiple assertions for this test
    if add_to_db:
        m_uoap.assert_called_once_with(driver='landsat', product=t_product, sensor=t_sensor,
                                       tile=lsd.id, date=lsd.date, name=t_filename)
    else:
        m_uoap.assert_not_called()
    assert (lsd.filenames == {(t_sensor, t_product): t_filename}
            and lsd.sensors == {t_product: t_sensor})


def t_data_add_file_repeat(orm, mocker):
    """Confirm that calling Data.AddFile twice results in overwrite.

    Thus, confirm it's possible to replace file entries with new versions.
    """
    t_tile      = 'test-tile'
    t_date      = datetime(1955, 11, 5)
    t_sensor    = 'test-sensor'
    t_product   = 'test-product'
    t_filename  = 'test-filename.tif'
    t_new_filename = 'test-new-filename.tif'
    lsd = landsatData(search=False) # heh
    lsd.id = t_tile
    lsd.date = t_date
    lsd.AddFile(t_sensor, t_product, t_filename)
    lsd.AddFile(t_sensor, t_product, t_new_filename) # should overwrite the old one
    # confirm overwrite happens both in the Data object and in the database
    assert (t_new_filename == lsd.filenames[(t_sensor, t_product)] and
            t_new_filename == dbinv.models.Product.objects.get(tile=t_tile, date=t_date).name)


@pytest.mark.parametrize('search', (False, True))
def t_data_init_search(mocker, orm, search):
    """Confirm Data.__init__ searches the FS only when told to.

    Do this by instantiating landsatData."""
    # set up mocks:  prevent it from doing I/O and use for assertions below
    mocker.patch.object(landsatData.Asset, 'discover')
    mocker.patch.object(landsatData, 'ParseAndAddFiles')

    lsd = landsatData(tile='t', date=datetime(9999, 1, 1), search=search) # call-under-test

    # assert normal activity & entry of search block
    assert (lsd.id == 't'
            and lsd.date == datetime(9999, 1, 1)
            and '' not in (lsd.path, lsd.basename)
            and lsd.assets == lsd.filenames == lsd.sensors == {}
            and lsd.ParseAndAddFiles.called == lsd.Asset.discover.called == search)


@pytest.fixture
def df_mocks(mocker):
    """Mocks for testing Data.fetch below."""
    mocker.patch.object(landsatData.Asset, 'discover', return_value=False)
    return mocker.patch.object(landsatData.Asset, 'fetch')

# useful constant for the following tests
df_args = (['rad', 'ndvi', 'bqashadow'], ['012030'], core.TemporalExtent('2012-12-01'))

def t_data_fetch_base_case(df_mocks):
    """Test base case of data.core.Data.fetch.

    It should return data about the fetch on success, and shouldn't
    raise an exception."""
    expected = [
        ('DN', '012030', datetime(2012, 12, 1, 0, 0)),
        ('C1', '012030', datetime(2012, 12, 1, 0, 0)),
        ('C1S3', '012030', datetime(2012, 12, 1, 0, 0)),
    ]
    assert expected == landsatData.fetch(*df_args)


def t_data_fetch_error_case(df_mocks):
    """Test error case of data.core.Data.fetch.

    It should return [], and shouldn't raise an exception."""
    df_mocks.side_effect = RuntimeError('aaah!')
    assert landsatData.fetch(*df_args) == []

def t_Asset_archive_update_case(mocker):
    """Tests Asset.archive with a single file and update=True"""
    # TODO more cases --^
    # note later date processing date -------------vvvvvvvv
    asset_fn          = 'LC08_L1TP_012030_20170801_20170811_01_T1.tar.gz'
    replaced_asset_fn = 'LC08_L1TP_012030_20170801_20171231_01_T1.tar.gz'

    # interpret path as a single file
    mocker.patch.object(data_core.os.path, 'isdir').return_value = False

    # mock _archivefile
    asset_obj          = landsat.landsatAsset(asset_fn)
    replaced_asset_obj = landsat.landsatAsset(replaced_asset_fn)
    m_archivefile = mocker.patch.object(landsat.landsatAsset, '_archivefile')
    # needs to return (asset object, link count, overwritten asset object)
    m_archivefile.return_value = (asset_obj, 1, replaced_asset_obj)

    # prevent exception for file-not-found
    mocker.patch.object(data_core, 'RemoveFiles')

    # setup complete; perform the call
    (actual_assets, actual_replaced_assets) = landsat.landsatAsset.archive(
            asset_fn, update=True)

    assert (actual_assets == [asset_obj] and
            actual_replaced_assets == [replaced_asset_obj])
