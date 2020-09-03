# Scope

## Stakeholders:
- discipline nodes
- engineering node operations
- PDS DOI working group


## Need: Discipline nodes need to mint DOIs for their data products.

## Goal:
- Engineering Node provides a service to mint DOI
- The required manual operation is minimized
- The submission from discipline node to the DOI provider (OSTI) are fully traceable

## Objectives:
- The system enable reserve, create, update and deactivate a DOI thourgh OSTI API interface
- user oriented command lines or API are provided to implement all the necessary actions
- Recording of the transactions is automated


## Concept of operations:

A Digital Object Identifier (DOI) is a permanent URL maintained by a partner (dataCite) which redirect on a landing page describing the resource and connected to it.

The user (discipline node, engineering node operator) perform reserve,draft,release,deactivate operations on the system.

Draft, reserve and release can be run multiple time.

The system perform the reserve, draft, release, deactivate operations on OSTI system for a DOI or a batch of DOIs


## Interfaces are:
- discipline node user
- OSTI and dataCite, initially DOI are recorded by submission to OSTI (see https://www.osti.gov/iad2/docs)
- engineering node operator
- deployment platform (on-prem JPL)