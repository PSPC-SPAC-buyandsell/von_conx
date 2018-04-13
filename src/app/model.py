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


import re

from sanic_openapi import doc
from von_agent.agents import AgentRegistrar, Origin, Issuer, HolderProver, Verifier
from von_agent.proto.validate import PROTO_MSG_JSON_SCHEMA
from von_agent.util import ppjson


def slug2pascal(slug):
    hump = lambda pat: pat.group(1).upper()
    rv = re.sub(r'^([a-z])', hump, slug)
    rv = re.sub(r'-([a-z])', hump, rv)
    return rv


def proxy_did_required(agent, msg_type):
    rv = True
    if msg_type in ('agent-nym-lookup', 'agent-endpoint-lookup', 'agent-endpoint-send', 'schema-lookup'):
        rv = False
    elif msg_type == 'agent-nym-send' and isinstance(agent, AgentRegistrar):
        rv = False
    elif msg_type == 'schema-send' and isinstance(agent, Origin):
        rv = False
    elif msg_type in ('claim-def-send', 'claim-offer-create', 'claim-create') and isinstance(agent, Issuer):
        rv = False
    elif msg_type in (
            'claim-offer-store',
            'claim-request',
            'proof-request',
            'proof-request-by-referent',
            'claim-store') and isinstance(agent, HolderProver):
        rv = False
    elif msg_type == 'verification-request' and isinstance(agent, Verifier):
        rv = False

    return rv


def json_schema_obj2model_obj(agent, msg_type, obj):
    rv = {}
    # print('\n\n-- key: {}, obj {}'.format(k, ppjson(obj)))
    required = obj.get('required', [])
    if 'properties' in obj:
        for p in obj['properties']:
            if p == 'proxy-did':
                rv[p] = doc.String(description=p, required=proxy_did_required(agent, msg_type))
            elif obj['properties'][p]['type'] == 'string':
                rv[p] = doc.String(description=p, required=(p in required))
            elif obj['properties'][p]['type'] == 'integer':
                rv[p] = doc.Integer(description=p, required=(p in required))
            elif obj['properties'][p]['type'] == 'array':
                sample_items = []  # sanic_openapi 0.4.0 chokes on empty items
                if obj['properties'][p]['items']['type'] == 'string':
                    sample_items.append(doc.String(description=p, required=(p in required)))
                elif obj['properties'][p]['items']['type'] == 'integer':
                    sample_items.append(doc.Integer(description=p, required=(p in required)))
                elif obj['properties'][p]['items']['type'] == 'object':
                    sample_items.append({k: k for k in obj['properties'][p]['items']['properties']})
                else:
                    sample_items.append('sample')
                rv[p] = doc.List(description=p, items=sample_items, required=(p in required))
            elif obj['properties'][p]['type'] == 'object':
                rv[p] = json_schema_obj2model_obj(agent, msg_type, obj['properties'][p])
    else:
        rv = doc.Dictionary(description='', required=True)
    # print('\n-->> returning {}'.format(rv))
    return rv


def is_native(agent, msg_type):
    rv = False
    if offers(agent, msg_type):
        rv = not proxy_did_required(agent, msg_type)
    return rv


def offers(agent, msg_type):
    rv = False
    if msg_type in ('master-secret-set', 'claims-reset'):
        rv = isinstance(agent, HolderProver)
    elif 'proxy-did' in PROTO_MSG_JSON_SCHEMA[msg_type]['properties']['data'].get('properties', []):
        rv = True
    return rv


def openapi_model(agent, msg_type):
    if not offers(agent, msg_type):
        return None

    return type(
        slug2pascal(msg_type),
        (),
        {
            'type': doc.String(description=msg_type, required=True, choices=[msg_type]),
            'data': json_schema_obj2model_obj(agent, msg_type, PROTO_MSG_JSON_SCHEMA[msg_type]['properties']['data'])
        })
