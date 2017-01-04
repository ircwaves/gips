"""Torque-based backend for the GIPS work scheduler."""

# originally copied from:
# https://raw.githubusercontent.com/jdherman/hpc-submission-scripts/master/submit-pbs-loop.py

from subprocess import Popen, PIPE

from gips import utils

pbs_directives = [
    # for meaning of directives see
    #   http://docs.adaptivecomputing.com/torque/4-0-2/Content/topics/commands/qsub.htm
    '-N gips_job',
    '-A gips_no_contract_specified:gips_no_task_specified',
    '-k oe',
    '-j oe',
    '-V',
    '-l walltime=1:00:00',
]

import_block = """
import os
import datetime
import gippy
from gips.inventory import dbinv, orm
from gips.datahandler import worker
"""

setup_block = """
os.environ['GIPS_ORM'] = 'true'
gippy.Options.SetVerbose(4) # substantial verbosity for diagnostic purposes
orm.setup()
"""

def generate_script(operation, args_batch):
    """Produce torque script from given worker function and arguments."""
    lines = []
    lines.append('#!' + utils.settings().REMOTE_PYTHON) # shebang
    lines += ['#PBS ' + d for d in pbs_directives]      # #PBS directives
    lines.append(import_block)  # python imports, std lib, 3rd party, and gips
    lines.append(setup_block)   # config & setup code

    lines.append("print 'starting on `{}` job, sample arguments:'".format(operation))
    # TODO: this is risky. if args_batch has quotes in it, generates syntax error
    #       i switched to double quotes because repr seems to generate singles in most cases
    lines.append('print "{}"'.format(repr(args_batch[0])))

    # star of the show, the actual command
    for args in args_batch:
        lines.append("worker.{}{}".format(operation, tuple(args)))

    return '\n'.join(lines) # stitch into single string & return


def submit(operation, args_ioi, batch_size=None, nproc=1):
    """Submit jobs to the configured Torque system.

    Return value is a list of tuples, one for each batch:
        (exit status of qsub, qsub's stdout, qsub's stderr)

    operation:  Defines which function will be performed, and must be one of
        'fetch', 'process', or 'export_and_aggregate'.
    args_ioi:  An iterable of iterables; each inner iterable gives the
        arguments to one call to the chosen function.
    batch_size:  The work is divided among torque jobs; each job receives
        batch_size function calls to perform in a loop.  Leave None for one job
        that works the whole batch.
    nproc: number of processors to request
    """
    if operation not in ('query', 'fetch', 'process', 'export_and_aggregate'):
        err_msg = ("'{}' is an invalid operation (valid operations are 'query', "
                   "'fetch', 'process', 'export_and_aggregate')".format(operation))
        raise ValueError(err_msg)

    if batch_size is None:
        chunks = [args_ioi]
    else:
        chunks = list(utils.grouper(args_ioi, batch_size))

    # clean last chunk:  needed due to izip_longest padding chunks with Nones:
    chunks.append([i for i in chunks.pop() if i is not None])

    outcomes = []

    qsub_cmd = ['qsub']
    if utils.settings().TORQUE_QUEUE:
        qsub_cmd.append('-q' + utils.settings().TORQUE_QUEUE)
    qsub_cmd.append('-lnodes=1:ppn={}'.format(nproc))
    
    for chunk in chunks:
        msg_prefix = "Error submitting job for '{}' operation".format(operation)
        with utils.error_handler(msg_prefix, continuable=True):
            job_script = generate_script(operation, chunk)

            # open a pipe to the qsub command, then write job_string to it
            proc = Popen(qsub_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
            proc.stdin.write(job_script)
            out, err = proc.communicate()
            outcomes.append((proc.returncode, out, err))
            if proc.returncode != 0:
                raise ValueError("Expected qsub to exit 0 but got {}".format(proc.returncode),
                                 proc.returncode, out, err)

    return outcomes
