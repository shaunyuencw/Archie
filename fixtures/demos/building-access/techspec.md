# Building access event system technical specification

SYNTHETIC — DEMONSTRATION ONLY

Version 1.0 · Fixed fixture date 21 September 2026

A simple physical access event viewer. Door hardware remains client equipment; the application and protected event store occupy separate tiers. Event delivery is deliberately unspecified.

## Purpose and placement

[B01] The proposed Building access event system has three tiers. Client · user devices contains four physical Door controllers and one physical Security operator workstation. Z1 · application services contains one virtual Access event service. Z2 · protected data contains one virtual Access event database. Host hardware, IP addresses and VLAN numbers are not yet specified.

## Interfaces

[B02] Security operator workstation initiates HTTPS on TCP 443 to Access event service. The service initiates PostgreSQL on TCP 5432 to Access event database. Door controllers exchange access events with Access event service, but push versus polling, session initiator, protocol and port have not been decided. Do not infer those facts from an arrow.

## Operations and open decisions

[B03] This scope is event viewing only. It does not include remote unlock commands, facial recognition, cameras or video analysis. Personal access-event records remain on premises. Cross-tier enforcement, database retention, auditing and backups require explicit review.

[B04] No production availability commitment or redundant instance count is supplied. The owner must choose an availability design and event-delivery approach. Continue with a labelled draft and the stated single service/database instances while these decisions remain open.
