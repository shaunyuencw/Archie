# Production service portal technical specification

SYNTHETIC — DEMONSTRATION ONLY

Version 1.0 · Fixed fixture date 21 September 2026

A proposed internal service-request portal for employees and the service desk. This small example separates physical client devices, application services and protected data. It is a fictional review draft, not an approved production design.

## Purpose and placement

[P01] The Production service portal has three trust tiers: Client · user devices; Z1 · application services; and Z2 · protected data. Every item below is a proposed part of this fictional design. Zone placement describes intended trust separation, not proof of firewall configuration. The model groups responsibility as User access, Portal services and Protected data.

[P02] Client contains one physical Employee workstation and one physical Service desk workstation. They are user devices only. No application server or database is placed in Client.

[P03] Z1 contains one virtual Portal web service and two virtual Request application instances operating active-active. Both services run on the two physical Application hosts in Z1. The host pair is specified as active-active; its hardware capacity is not yet sized. One virtual Zone firewall also runs on an Application host; firewall failover is undecided.

[P04] Z2 contains two physical Request database servers operating active-passive. The database stores requests and application audit records. No Client device may connect directly to the database.

## Interfaces

[P05] Each workstation initiates an HTTPS session to Portal web service on TCP 443 for service requests or service-desk actions. These are application sessions, not infrastructure administration sessions.

[P06] Portal web service initiates HTTPS sessions to Request application on TCP 443. Request application initiates PostgreSQL sessions to Request database on TCP 5432. Zone firewall is the explicit enforcement reference for the Z1-to-Z2 database interface; its intended rule permits only the application service identity to that database service and denies other cross-tier traffic.

## Operations and open decisions

[P07] The application is internal and has no required internet-hosted dependency. Data remains on premises. Application database and audit records are the only stores defined here; backups, audit retention, IP addresses, VLAN numbers, hardware capacity and infrastructure administration remain undecided.

[P08] A service availability requirement exists, but its end-to-end strategy is not yet approved: the application and database have the stated redundancy, while the web service and virtual firewall remain single instances. The service owner must choose a recovery target and resolve these remaining failure points before production acceptance.
