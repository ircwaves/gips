
import datetime

import gippy


from gips.datahandler import torque

def t_submit_normal_case(mocker):
    gippy.Options.SetVerbose(4) # for good debugging info during the test run

    m_popen = mocker.patch.object(torque, "Popen")
    m_proc = m_popen()
    m_proc.returncode = 0

    fetch_args = ('modis', 'MCD43A2', 'h12v04', datetime.date(2012, 12, 1))
    m_proc.communicate.return_value = (mocker.MagicMock(), mocker.MagicMock())

    submission_outcome = torque.submit('fetch', [fetch_args])
    m_proc.stdin.write.assert_called_once()
    # check for a key string in the submitted script
    assert ("worker.fetch('modis', 'MCD43A2', 'h12v04', datetime.date(2012, 12, 1))" in
            m_proc.stdin.write.call_args[0][0])
    m_proc.communicate.assert_called_once_with()
