# Warehouse inventory system technical specification

SYNTHETIC — DEMONSTRATION ONLY

Version 1.0 · Fixed fixture date 21 September 2026

A small internal stock-control application with handheld users, an application tier and a protected stock ledger. Its unresolved integration decision is deliberate so a live extraction can ask a useful question.

## Purpose and placement

[I01] The proposed Warehouse inventory system uses Client · user devices for two physical handheld scanners and one physical Supervisor workstation, Z1 · application services for one Inventory web application, and Z2 · protected data for one Inventory database. Application and database are virtual; their physical hosts and hardware sizing are not specified.

## Interfaces

[I02] Scanners and Supervisor workstation initiate HTTPS on TCP 443 to Inventory web application. The application initiates PostgreSQL on TCP 5432 to Inventory database. Client devices have no direct database access. A cross-tier enforcement design has not been supplied and must remain an open item.

## Operations and open decisions

[I03] The ledger records product identifiers, warehouse locations, stock movements and quantities. Video surveillance is outside scope. Stock movement may need to reach an existing finance system, but the finance endpoint, protocol, delivery mode and initiator are not yet agreed. Do not invent that interface before clarification.

[I04] The warehouse has no required public-cloud or internet dependency in this source. A resilient service is requested, but backup frequency, recovery targets and redundancy remain undecided. The stated single instances describe the current draft rather than evidence of adequate availability.
