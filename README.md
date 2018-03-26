# von_conx
As part of the technology demonstrator project using Hyperledger indy to explore the use of the distributed ledger with PSPC Supplier Registration Information (SRI), the design specifies agents with service wrapper APIs to facilitate interoperability. This package uses django to implement the service wrapper API code implenting VON connector layer.

The current state of the project aims to fulfil a demonstration use case enabling collaboration between the SRI and the British Columbia government's The Org Book project, underpinning its Verified Organization Network (VON).

The demonstration defines the following agents:
  - the Trust Anchor agent as:
    - a schema originator
    - the agent registrar on the distributed ledger
  - the BC Registrar agent as:
    - a schema originator for its own claims
    - an issuer of claims
  - the BC Org Book agent as, for claims that the BC Registrar issues:
    - a W3C claims holder
    - an indy-sdk prover
  - the SRI agent as:
    - a schema originator for its own claims
    - an issuer of claims
    - a verifier of claims, whether itself or the BC Registrar agent issued them
  - the PSPC Org Book as, for claims that the SRI agent issues:
    - a W3C claims holder
    - an indy-sdk prover.

The von_conx package implements a reference VON connector implementation using Sanic on docker-compose with:
  - containers for the indy pool and for each agent
  - two docker networks:
    - one for the indy pool on 10.0.0.0/24
    - one for all agents on 10.0.1.0/24.

## Documentation
The design document is available from the `von_base` repository (<https://github.com/PSPC-SPAC-buyandsell/von_base.git>) at `doc/agent-design.doc`. It discusses in detail the packages comprising the technology demonstrator project:
  - `von_base`
  - `von_agent`
  - `von_conx`

including instructions for installation, configuration, and operation.
