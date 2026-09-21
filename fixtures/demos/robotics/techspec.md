# Hybrid robotics trial technical specification

SYNTHETIC — DEMONSTRATION ONLY

Version 1.0 · Fixed fixture date 21 September 2026

A bounded wireless robotics trial that is isolated from a small production operations service. Testbed data may leave through two named interfaces: a narrow production status handoff and an AWS telemetry path. Cloud services are shown explicitly as managed services, not as software secretly placed inside an on-premises zone.

## Purpose and placement

[R01] Production uses Production · Client · user devices, Production · Z1 · application services and Production · Z2 · protected data. Testbed uses separate Testbed · Client · trial devices, Testbed · Z1 · trial services and Testbed · Z2 · trial data. The Production operations and Robotics testbed systems are separate; a shared zone name must never merge their trust boundaries.

[R02] Production Client contains one physical Production operator workstation. Production Z1 contains two virtual Production integration API instances operating active-active. Production Z2 contains two physical Production job database servers operating active-passive. The API and database have no declared shared physical host.

[R03] Testbed Client contains one physical Trial robot, one physical Trial operator tablet and one physical Trial wireless access point. The trial uses its own WPA3-Enterprise wireless network. It does not bridge to the production client LAN. Authentication server details, radio survey and RF coverage remain undecided; an access-point icon does not prove those controls exist.

[R04] Testbed Z1 contains one physical Trial compute host. It runs three single-instance virtual components: Robot controller, Trial integration gateway and Trial virtual firewall. Testbed Z2 contains one virtual Trial data store; its host is not specified. No resilience claim is made for these single-instance trial services.

## AWS telemetry placement

[R05] AWS telemetry is a separate external managed-service system with AWS · Z1 · telemetry ingestion and AWS · Z2 · protected telemetry. One Amazon API Gateway endpoint and one AWS Lambda telemetry function belong to its ingestion tier; one Amazon S3 telemetry bucket belongs to its protected-data tier. These labels are logical trust tiers, not assertions that the regional managed services reside in a private subnet or VPC.

## Interfaces

[R06] Production operator workstation initiates HTTPS on TCP 443 to Production integration API. That API initiates PostgreSQL on TCP 5432 to Production job database. There is no Testbed-to-production-database interface, no cloud-to-robot command interface and no unrestricted lateral production access.

[R07] Trial robot associates with Trial wireless access point using WPA3-Enterprise over IEEE 802.11. Its separate application session initiates MQTT over TLS on TCP 8883 to Robot controller; Trial virtual firewall is the enforcement reference. Trial operator tablet initiates HTTPS on TCP 443 to Robot controller through the same enforcement control. Radio association is not evidence of application session initiation.

[R08] Robot controller initiates PostgreSQL on TCP 5432 to Trial data store through Trial virtual firewall. Trial integration gateway polls Robot controller using HTTPS on TCP 443 to read a bounded status snapshot. Telemetry delivery retries, queueing limits and failure handling are not yet specified.

[R09] The only proposed Testbed-to-Production handoff is Trial integration gateway initiating HTTPS on TCP 443 to Production integration API, through Trial virtual firewall. It pushes only trial ID, job ID, readiness state and timestamp; robot control commands and personal data are excluded. The gateway uses a dedicated trial service identity. Production must validate that identity and schema and may reject the request. This synthetic intended rule is not organisational approval.

[R10] Trial integration gateway initiates HTTPS on TCP 443 to Amazon API Gateway for outbound operational telemetry, through Trial virtual firewall. The telemetry excludes production records and personal data. A dedicated IAM principal signs the requests; key provisioning and rotation remain to be designed. API Gateway invokes the AWS Lambda telemetry function using the AWS-managed Lambda integration, and Lambda writes telemetry objects to Amazon S3 using HTTPS on TCP 443. No reverse command path is defined.

## Operations and open decisions

[R11] AWS region, data residency approval, private connectivity versus public TLS, telemetry retention, permitted telemetry schema, credential lifecycle and the trial decommissioning date remain undecided. A routed network path or a cloud icon must not be treated as approval. Production database and trial raw data stay on premises; only the explicitly bounded status/telemetry payloads may cross the stated interfaces.

[R12] Production has the stated API and database redundancy. Testbed recovery is manual restart and does not have a production availability commitment. End-to-end resilience, recovery times and evidence of firewall configuration are unverified. Do not describe this source as proof of compliance or operational readiness.
