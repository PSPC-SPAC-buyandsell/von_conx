#!/bin/bash

#
# Copyright 2017-2018 Government of Canada - Public Services and Procurement Canada - buyandsell.gc.ca
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

export HOST_IP=${HOST_IP:-0.0.0.0}
export HOST_PORT=${HOST_PORT}
export RUST_LOG=${RUST_LOG:-error}
export TEST_POOL_IP=${TEST_POOL_IP:-10.0.0.2}
export AGENT_PROFILE=${AGENT_PROFILE}
export WAIT_FOR_TA_SEC=${WAIT_FOR_TA_SEC:-0}
export TA_NETLOC=${TA_NETLOC:-'trust-anchor:8990'}

cd "${HOME}"/src
CMD="$@"
if [ -z "${CMD}" ]
then
    CMD="python -m sanic app.app --host=${HOST_IP} --port=${HOST_PORT}"
fi

while [ "${WAIT_FOR_TA_SEC}" -gt 0 ]
do
    echo "Sleeping up to ${WAIT_FOR_TA_SEC} seconds in case trust anchor is spinning up and agent needs it ..."
    sleep 1
    ((WAIT_FOR_TA_SEC--))
    DID_TA_JSON=$(wget -q -O - "http://${TA_NETLOC}/api/v0/did")
    [ -n "${DID_TA_JSON}" ] && break
done

exec ${CMD}
