"""
Copyright 2017-2018 Government of Canada - Public Services and Procurement Canada - buyandsell.gc.ca

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from app.cache import mem_cache
from app.service.eventloop import do
from configparser import ConfigParser
from io import StringIO
from os import environ, makedirs
from os.path import abspath, dirname, expandvars, isfile, join as pjoin

import logging
import logging.config

_inis = [
    pjoin(dirname(abspath(__file__)), 'config', 'config.ini'),
    pjoin(dirname(abspath(__file__)), 'config', 'agent-profile', '{}.ini'.format(environ.get('AGENT_PROFILE'))),
]

def init_logging():
    dir_log = pjoin(dirname(abspath(__file__)), 'log')
    makedirs(dir_log, exist_ok=True)
    path_log = pjoin(dir_log, environ.get('AGENT_PROFILE') + '.log')

    LOG_FORMAT='%(asctime)-15s | %(levelname)-8s | %(name)-12s | %(message)s'
    logging.basicConfig(filename=path_log, level=logging.INFO, format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('von_conx').setLevel(logging.INFO)
    logging.getLogger('von_agent').setLevel(logging.INFO)
    logging.getLogger('indy').setLevel(logging.ERROR)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)

def init_config():
    init_logging()

    global _inis
    if not do(mem_cache.get('config')):
        if all(isfile(ini) for ini in _inis):
            parser = ConfigParser()
            for ini in _inis:
                with open(ini, 'r') as ini_file:
                    ini_text = expandvars(ini_file.read())
                    parser.readfp(StringIO(ini_text))
            do(mem_cache.set(
                'config',
                {s: dict(parser[s].items()) for s in parser.sections()}))
        else:
            raise FileNotFoundError('Configuration file missing; check {}'.format(_inis))

    '''
    e.g.,
    {
        "Pool": {
            "genesis.txn.path": "/.../von_connector/service_wrapper_project/wrapper_api/config/bootstrap/genesis.txn"
        },
        "Agent": {
            "role": "Trust-Anchor",
            "host": "127.0.0.1",
            "seed": "000000000000000000000000Trustee1",
            "port": "8000"
        },
        "Trust Anchor": {
            "host": "127.0.0.1",
            "port": "8000"
            ...: ...
        }
    }
    '''

    return do(mem_cache.get('config'))
