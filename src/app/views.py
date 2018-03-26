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

from app import app
from app.cache import mem_cache
from app.service.eventloop import do
from indy.error import IndyError
from von_agent.error import VonAgentError
from sanic import response

import json
import logging


logger = logging.getLogger(__name__)


@app.route('/api/v0/did', methods=['GET'])
async def did(request):
    logger.debug('Processing GET {}'.format(request.url))
    ag = await mem_cache.get('agent')
    rv_json = await ag.process_get_did()
    return response.json(json.loads(rv_json))

@app.route('/api/v0/txn/<seq_no:int>', methods=['GET'])
async def txn(request, seq_no):
    logger.debug('Processing GET {}'.format(request.url))
    ag = await mem_cache.get('agent')
    rv_json = await ag.process_get_txn(seq_no)
    return response.json(json.loads(rv_json))

@app.route('/api/v0/<msg_type:[-a-zA-Z]*>', methods=['POST'])
async def process_post(request, msg_type):
    logger.debug('Processing POST {}, request body {}'.format(request.url, request.body))
    ag = await mem_cache.get('agent')
    try:
        form = request.json
        rv_json = await ag.process_post(form)
        return response.json(json.loads(rv_json))
    except Exception as e:
        logger.exception('Exception on {}: {}'.format(request.path, e))
        # import traceback
        # traceback.print_exc()
        return response.json(
            {
                'error-code': int(e.error_code) if isinstance(e, (IndyError, VonAgentError)) else 400,
                'message': str(e)
            },
            status=400)
    finally:
        await mem_cache.set('agent', ag)  #  in case agent state changes over process_post
