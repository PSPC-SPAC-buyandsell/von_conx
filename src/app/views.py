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


import json
import logging

from app import app
from app.cache import mem_cache
from app.model import is_native, offers, openapi_model
from app.service.eventloop import do
from indy.error import IndyError
from os import environ
from von_agent.agents import AgentRegistrar, Origin, Issuer, HolderProver, Verifier
from von_agent.error import VonAgentError
from sanic import response
from sanic_openapi import doc, openapi_blueprint, swagger_blueprint


logger = logging.getLogger(__name__)


app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)
app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'von_conx'
app.config.API_TERMS_OF_SERVICE = 'For demonstration of von_agent API'
app.config.API_PRODUCES_CONTENT_TYPES = ['application/json']
app.config.API_CONTACT_EMAIL = 'stephen.klump@becker-carroll.com'
app.config.API_LICENSE_URL = 'http://www.apache.org/licenses/LICENSE-2.0'

agent = do(mem_cache.get('agent'))
profile = environ.get('AGENT_PROFILE', 'trust-anchor')


@app.get('/api/v0/did')
@doc.summary("Returns the agent's JSON-encoded DID")
@doc.produces(str)
@doc.tag('{} as Base Agent'.format(profile))
async def did(request):
    logger.debug('Processing GET {}'.format(request.url))
    ag = await mem_cache.get('agent')
    rv_json = await ag.process_get_did()
    return response.json(json.loads(rv_json))


@app.get('/api/v0/txn/<seq_no:int>')
@doc.summary('Returns the ledger transaction on the input sequence number, or empty production {} for none')
@doc.produces(dict)
@doc.tag('{} as Base Agent'.format(profile))
async def txn(request, seq_no):
    logger.debug('Processing GET {}'.format(request.url))
    ag = await mem_cache.get('agent')
    rv_json = await ag.process_get_txn(seq_no)
    return response.json(json.loads(rv_json))


def cond_deco(deco, cond):
    def rd(f):
        return deco(f) if cond else f
    return rd


async def _process_post(request):
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


@app.post('/api/v0/agent-nym-lookup')
@doc.summary('Lookup agent nym on ledger by DID')
@doc.consumes(openapi_model(agent, 'agent-nym-lookup'), location='body')
@doc.produces(dict)
@doc.tag('{} as Base Agent'.format(profile))
async def process_post_agent_nym_lookup(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/agent-nym-send'), offers(agent, 'agent-nym-send'))
@cond_deco(doc.summary('Send agent nym to ledger'), offers(agent, 'agent-nym-send'))
@cond_deco(doc.consumes(openapi_model(agent, 'agent-nym-send'), location='body'), offers(agent, 'agent-nym-send'))
@cond_deco(doc.produces(dict), offers(agent, 'agent-nym-send'))
@cond_deco(
    doc.tag('{} as Trust Anchor{}'.format(profile, '' if is_native(agent, 'agent-nym-send') else ' by Proxy')),
    offers(agent, 'agent-nym-send'))
async def process_post_agent_nym_send(request):
    return await _process_post(request)



@app.post('/api/v0/agent-endpoint-lookup')
@doc.summary('Lookup agent endpoint on ledger by DID')
@doc.consumes(openapi_model(agent, 'agent-endpoint-lookup'), location='body')
@doc.produces(dict)
@doc.tag('{} as Base Agent'.format(profile))
async def process_post_agent_endpoint_lookup(request):
    return await _process_post(request)



@app.post('/api/v0/agent-endpoint-send')
@doc.summary('Send agent endpoint to ledger')
@doc.consumes(openapi_model(agent, 'agent-endpoint-send'), location='body')
@doc.produces(dict)
@doc.tag('{} as Base Agent'.format(profile))
async def process_post_agent_endpoint_send(request):
    return await _process_post(request)


@app.post('/api/v0/schema-lookup')
@doc.summary('Lookup schema on ledger')
@doc.consumes(openapi_model(agent, 'schema-lookup'), location='body')
@doc.produces(dict)
@doc.tag('{} as Base Agent'.format(profile))
async def process_post_schema_lookup(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/schema-send'), offers(agent, 'schema-send'))
@cond_deco(doc.summary('Send schema to ledger'), offers(agent, 'schema-send'))
@cond_deco(doc.consumes(openapi_model(agent, 'schema-send'), location='body'), offers(agent, 'schema-send'))
@cond_deco(doc.produces(dict), offers(agent, 'schema-send'))
@cond_deco(
    doc.tag('{} as Origin{}'.format(profile, '' if is_native(agent, 'schema-send') else ' by Proxy')),
    offers(agent, 'schema-send'))
async def process_post_schema_send(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claim-def-send'), offers(agent, 'claim-def-send'))
@cond_deco(doc.summary('Send claim definition to ledger'), offers(agent, 'claim-def-send'))
@cond_deco(doc.consumes(openapi_model(agent, 'claim-def-send'), location='body'), offers(agent, 'claim-def-send'))
@cond_deco(doc.produces(dict), offers(agent, 'claim-def-send'))
@cond_deco(
    doc.tag('{} as Issuer{}'.format(profile, '' if is_native(agent, 'claim-def-send') else ' by Proxy')),
    offers(agent, 'claim-def-send'))
async def process_post_claim_def_send(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/master-secret-set'), offers(agent, 'master-secret-set'))
@cond_deco(doc.summary('Set master secret (lable)'), offers(agent, 'master-secret-set'))
@cond_deco(doc.consumes(openapi_model(agent, 'master-secret-set'), location='body'), offers(agent, 'master-secret-set'))
@cond_deco(doc.produces(dict), offers(agent, 'master-secret-set'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(profile, '' if is_native(agent, 'master-secret-set') else ' by Proxy')),
    offers(agent, 'master-secret-set'))
async def process_post_master_secret_set(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claim-offer-create'), offers(agent, 'claim-offer-create'))
@cond_deco(doc.summary('Create claim offer for holder-prover'), offers(agent, 'claim-offer-create'))
@cond_deco(
    doc.consumes(openapi_model(agent, 'claim-offer-create'), location='body'),
    offers(agent, 'claim-offer-create'))
@cond_deco(doc.produces(dict), offers(agent, 'claim-offer-create'))
@cond_deco(
    doc.tag('{} as Issuer{}'.format(profile, '' if is_native(agent, 'claim-offer-create') else ' by Proxy')),
    offers(agent, 'claim-offer-create'))
async def process_post_claim_offer_create(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claim-offer-store'), offers(agent, 'claim-offer-store'))
@cond_deco(doc.summary('Store claim offer'), offers(agent, 'claim-offer-store'))
@cond_deco(doc.consumes(openapi_model(agent, 'claim-offer-store'), location='body'), offers(agent, 'claim-offer-store'))
@cond_deco(doc.produces(dict), offers(agent, 'claim-offer-store'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(profile, '' if is_native(agent, 'claim-offer-store') else ' by Proxy')),
    offers(agent, 'claim-offer-store'))
async def process_post_claim_offer_store(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claim-create'), offers(agent, 'claim-create'))
@cond_deco(doc.summary('Create claim'), offers(agent, 'claim-create'))
@cond_deco(doc.consumes(openapi_model(agent, 'claim-create'), location='body'), offers(agent, 'claim-create'))
@cond_deco(doc.produces(dict), offers(agent, 'claim-create'))
@cond_deco(
    doc.tag('{} as Issuer{}'.format(profile, '' if is_native(agent, 'claim-create') else ' by Proxy')),
    offers(agent, 'claim-create'))
async def process_post_claim_create(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claim-store'), offers(agent, 'claim-store'))
@cond_deco(doc.summary('Store claim'), offers(agent, 'claim-store'))
@cond_deco(doc.consumes(openapi_model(agent, 'claim-store'), location='body'), offers(agent, 'claim-store'))
@cond_deco(doc.produces(dict), offers(agent, 'claim-store'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(profile, '' if is_native(agent, 'claim-store') else ' by Proxy')),
    offers(agent, 'claim-store'))
async def process_post_claim_store(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claim-request'), offers(agent, 'claim-request'))
@cond_deco(doc.summary('Request claim'), offers(agent, 'claim-request'))
@cond_deco(doc.consumes(openapi_model(agent, 'claim-request'), location='body'), offers(agent, 'claim-request'))
@cond_deco(doc.produces(dict), offers(agent, 'claim-request'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(profile, '' if is_native(agent, 'claim-request') else ' by Proxy')),
    offers(agent, 'claim-request'))
async def process_post_claim_request(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/claims-reset'), offers(agent, 'claims-reset'))
@cond_deco(doc.summary('Reset wallet'), offers(agent, 'claims-reset'))
@cond_deco(doc.consumes(openapi_model(agent, 'claims-reset'), location='body'), offers(agent, 'claims-reset'))
@cond_deco(doc.produces(dict), offers(agent, 'claims-reset'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(profile, '' if is_native(agent, 'claims-reset') else ' by Proxy')),
    offers(agent, 'claims-reset'))
async def process_post_claims_reset(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/proof-request'), offers(agent, 'proof-request'))
@cond_deco(doc.summary('Request proof'), offers('agent', 'proof-request'))
@cond_deco(doc.consumes(openapi_model(agent, 'proof-request'), location='body'), offers('agent', 'proof-request'))
@cond_deco(doc.produces(dict), offers('agent', 'proof-request'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(profile, '' if is_native(agent, 'proof-request') else ' by Proxy')),
    offers('agent', 'proof-request'))
async def process_post_proof_request(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/proof-request-by-referent'), offers(agent, 'proof-request-by-referent'))
@cond_deco(doc.summary('Request proof by referent'), offers(agent, 'proof-request-by-referent'))
@cond_deco(
    doc.consumes(openapi_model(agent, 'proof-request-by-referent'), location='body'),
    offers(agent, 'proof-request-by-referent'))
@cond_deco(doc.produces(dict), offers(agent, 'proof-request-by-referent'))
@cond_deco(
    doc.tag('{} as Holder-Prover{}'.format(
        profile,
        '' if is_native(agent, 'proof-request-by-referent') else ' by Proxy')),
    offers(agent, 'proof-request-by-referent'))
async def process_post_proof_request_by_referent(request):
    return await _process_post(request)


@cond_deco(app.post('/api/v0/verification-request'), offers(agent, 'verification-request'))
@cond_deco(doc.summary('Request verification'), offers(agent, 'verification-request'))
@cond_deco(
    doc.consumes(openapi_model(agent, 'verification-request'), location='body'),
    offers(agent, 'verification-request'))
@cond_deco(doc.produces(dict), offers(agent, 'verification-request'))
@cond_deco(
    doc.tag('{} as Verifier{}'.format(profile, '' if is_native(agent, 'verification-request') else ' by Proxy')),
    offers(agent, 'verification-request'))
async def process_post_verification_request(request):
    return await _process_post(request)
