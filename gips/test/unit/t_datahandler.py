import datetime

import pytest

from gips.inventory.dbinv import models
from gips.inventory import dbinv
from gips.datahandler import worker


@pytest.mark.django_db
def t_query(mocker):
    # setup & mocks
    m_query_service = mocker.patch.object(worker.api, "query_service")
    catalog_entry = models.DataVariable.objects.create()
    job = models.Job.objects.create(variable=catalog_entry, status='initializing',
                                    spatial=0, temporal=0)
    # call
    worker.query(job.pk)
    # assertions
    job.refresh_from_db()
    assert job.status == 'in-progress'
    m_query_service.assert_called_once()


@pytest.mark.django_db()
def t_fetch(mocker):
    """Unit test for worker.fetch."""
    # setup & mocks
    m_AssetClass = mocker.patch.object(worker.utils, "import_data_class")().Asset
    m_AssetClass.fetch.return_value = ['some_file.hdf']
    m_asset = mocker.Mock()
    m_asset.sensor = 'dontcare'
    m_asset.archived_filename = 'whatever.hdf'
    m_AssetClass._archivefile.return_value = [m_asset]
    key_kwargs = dict(driver='modis',
                      asset ='MCD43A2',
                      tile  ='h12v04',
                      date  =datetime.date(2012, 12, 1))
    fetch_args = tuple(key_kwargs[k] for k in ('driver', 'asset', 'tile', 'date'))
    api_kwargs = dict(sensor='dontcare',
                      name  ='unspecified',
                      status='scheduled',
                      **key_kwargs)
    dbinv.update_or_add_asset(**api_kwargs) # set the asset to 'scheduled' status

    # call
    returned_asset = worker.fetch(*fetch_args)

    # assertions
    queried_asset = models.Asset.objects.get(**key_kwargs)
    assert ('whatever.hdf' == returned_asset.name == queried_asset.name
            and 'complete' == returned_asset.status == queried_asset.status)


@pytest.mark.django_db()
def t_process(mocker):
    """Simple unit test for worker.process."""
    # mock & setup
    m_data_obj = mocker.patch.object(worker.utils, "import_data_class")()()
    key_kwargs = dict(driver ='modis',
                      product='quality',
                      tile   ='h12v04',
                      date   =datetime.date(2012, 12, 1))
    process_args = tuple(key_kwargs[k] for k in ('driver', 'product', 'tile', 'date'))
    api_kwargs = dict(sensor='dontcare',
                      name  ='unspecified',
                      status='scheduled',
                      **key_kwargs)
    dbinv.update_or_add_product(**api_kwargs) # set the prod to 'scheduled' status

    # test
    worker.process(*process_args)

    # assertion
    m_data_obj.process.assert_called_once()


@pytest.mark.django_db
def t_worker_export_and_aggregate(mocker):
    # setup & mocks
    m_export    = mocker.patch.object(worker, '_export')
    m_aggregate = mocker.patch.object(worker, '_aggregate')
    m_makedirs  = mocker.patch.object(worker.os, 'makedirs')
    m_rmtree    = mocker.patch.object(worker.shutil, 'rmtree')
    catalog_entry = models.DataVariable.objects.create()
    job = models.Job.objects.create(variable=catalog_entry, status='pp-scheduled',
                                    spatial=0, temporal=0)
    # call
    worker.export_and_aggregate(job.pk, {})
    # assertions
    job.refresh_from_db()
    assert job.status == 'complete'
    for m in m_export, m_aggregate, m_makedirs, m_rmtree:
        m.assert_called_once() # TODO check arguments
