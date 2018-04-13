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

from app import cfg
from app.cache import mem_cache
from app.service.bootseq import BootSequence
from app.service.eventloop import do
from os.path import dirname, join
from sanic import Sanic


DIR_STATIC = join(dirname(__file__), 'static')

# initialize app
app = Sanic(strict_slashes=True)
app.static('/static', DIR_STATIC)
app.static('/favicon.ico', join(DIR_STATIC, 'favicon.ico'))
c = cfg.init_config()

@app.listener('before_server_stop')
async def cleanup(app, loop):
    ag = await mem_cache.get('agent')
    if ag is not None:
        await ag.close()

    pool = await mem_cache.get('pool')
    if pool is not None:
        await pool.close()

# start
BootSequence.go()

# load views (which depend on agent role)
from app import views
