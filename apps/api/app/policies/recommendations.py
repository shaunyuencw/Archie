"""Deterministic relevance suggestions; never selects policies or asserts compliance."""
import re
from ..domain.commands import apply, DomainError
from ..domain.models import Operation
from .engine import zone_tier
from .library import clauses, selected_ids, validate_selection


def recommendations_for(project):
    library={clause['id']:clause for clause in clauses()}
    selected=set(selected_ids(project));suggestions={};signals={}
    components=project.components;by_id={component.id:component for component in components}
    assets={component.asset_id for component in components}
    deployments={deployment.component_id:deployment for deployment in project.deployments}
    def suggest(ident,reason,affected=()):
        if ident in selected or ident not in library or ident in suggestions:return
        clause=library[ident]
        suggestions[ident]={'policy_id':ident,'title':clause['title'],'reason':reason,'category':clause['category'],'implementation':clause['implementation'],'affected_ids':list(dict.fromkeys(affected))[:20],'origin':'rules'}
    def signal(tags,reason,affected=()):
        for tag in tags:signals[tag]=(reason,list(affected))
    tiers={zone_tier(zone) for zone in project.zones}-{None}
    if components:
        suggest('DEMO-ZON-01','The draft contains deployed components; review their declared security zones.',[component.id for component in components])
        suggest('ARCH-OWN-01','The draft contains services or devices that will need named support owners.',[component.id for component in components])
        signal(['ownership','support'],'Components in this draft need ownership and support review.',[component.id for component in components])
    if {'client','z1','z2'}<=tiers:
        suggest('ARCH-BOUND-01','The draft explicitly uses Client, Z1 and Z2 tiers.',[zone.id for zone in project.zones])
        suggest('ARCH-SEG-01','Client and protected Z2 tiers are present; review direct-access restrictions.',[zone.id for zone in project.zones if zone_tier(zone) in {'client','z2'}])
        signal(['segmentation','zone'],'The draft declares a Client / Z1 / Z2 architecture.',[zone.id for zone in project.zones])
    if project.interfaces:
        interface_ids=[interface.id for interface in project.interfaces]
        suggest('DEMO-IF-01','The draft includes network interfaces whose initiator and protocol should be recorded.',interface_ids)
        suggest('ARCH-TLS-01','The draft includes connections; review which need encryption and certificate ownership.',interface_ids)
        suggest('ARCH-LPR-01','Connected workloads need an explicit review of their permitted actions and resources.',interface_ids)
        signal(['tls','encryption','protocol','least privilege'],'The draft includes network connections.',interface_ids)
    crossing=[interface.id for interface in project.interfaces if deployments.get(interface.source) and deployments.get(interface.target) and deployments[interface.source].zone_id and deployments[interface.target].zone_id and deployments[interface.source].zone_id!=deployments[interface.target].zone_id]
    if crossing:
        suggest('ARCH-FLW-01','Interfaces cross declared zone boundaries; name the control for each session.',crossing)
        signal(['firewall','enforcement','network'],'Interfaces cross declared zone boundaries.',crossing)
    data=[component.id for component in components if component.asset_id in {'database','storage','aws-rds','aws-dynamodb','aws-s3','aws-efs'}]
    databases=[component.id for component in components if component.asset_id in {'database','aws-rds','aws-dynamodb'}]
    if databases and 'z2' in tiers:suggest('ARCH-DAT-01','The draft contains a database and a protected Z2 tier; check their placement.',databases)
    if data:
        suggest('ARCH-BAK-01','The draft stores data; agree recovery targets and how a restore will be tested.',data)
        suggest('ARCH-DATA-01','The draft includes data stores; agree permitted locations, retention and deletion.',data)
        signal(['backup','restore','recovery','data','retention','privacy'],'The draft includes data stores.',data)
    services=[component.id for component in components if component.asset_id in {'server','gpu-server','web-server','application-server','application','api-service','database','event-broker','identity-service','aws-ec2','aws-ecs','aws-eks','aws-lambda','aws-rds','aws-dynamodb','aws-api-gateway'}]
    users=[component.id for component in components if component.asset_id in {'workstation','operator-tablet'}]
    if services:
        suggest('ARCH-SEC-01','Application or data services are present; confirm whether credentials are needed and how they will be stored.',services)
        suggest('ARCH-LOG-01','Application or data services are present; review useful logs, destinations and alert owners.',services)
        suggest('ARCH-PAT-01','The draft contains software services that need patch and support ownership.',services)
        signal(['secrets','credentials','logging','audit','monitoring','patch'],'The draft includes software services.',services)
    if services or users:
        suggest('ARCH-IAM-01','The draft includes user devices or services; review user and administrator access separately.',users+services)
        signal(['identity','management'],'The draft includes user devices or services.',users+services)
    resilience=[constraint.id for constraint in project.constraints if constraint.key=='resilience_required' and constraint.value is True]
    multiples=[deployment.id for deployment in project.deployments if (deployment.quantity or 0)>1 or deployment.redundancy_mode!='unknown']
    if resilience:
        suggest('DEMO-HA-01','A resilience requirement is recorded; check that an availability strategy is also explicit.',resilience)
    if resilience or multiples:
        suggest('ARCH-AVL-01','The draft records resilience or multiple instances; review failure domains and failover, without treating quantity as proof.',resilience+multiples)
        signal(['availability','redundancy','failover','resilience'],'The draft records resilience or multiple instances.',resilience+multiples)
    cloud=[component.id for component in components if component.asset_id.startswith('aws-')]
    if cloud:
        suggest('ARCH-CLD-01','AWS components are present; review public/private boundaries and workload access.',cloud)
        suggest('ARCH-EGR-01','AWS components are present; document required outbound dependencies and service-loss behaviour.',cloud)
        signal(['aws','cloud','egress'],'The draft contains AWS components.',cloud)
    hybrid=[interface.id for interface in project.interfaces if interface.source in by_id and interface.target in by_id and ((interface.source in cloud)!=(interface.target in cloud))]
    if hybrid:
        suggest('ARCH-HYB-01','An interface connects AWS and non-AWS components; confirm the hosting boundary and approved connection design.',hybrid)
        signal(['hybrid','vpn'],'An interface connects AWS and non-AWS components; confirm whether a hybrid link applies.',hybrid)
    def boundary(zone,names):return re.split(r'[\s·:/_-]+',zone.name.lower())[0] in names or re.split(r'[_-]',zone.id.lower())[0] in names
    trial=[zone.id for zone in project.zones if boundary(zone,{'test','testbed','trial'})]
    production=[zone.id for zone in project.zones if boundary(zone,{'prod','production'})]
    robots=[component.id for component in components if component.asset_id=='robot']
    wireless=[component.id for component in components if component.asset_id in {'wireless-access-point','robot','operator-tablet'}]
    if trial and production:
        suggest('ARCH-TST-01','Production and trial/testbed boundaries are both declared; review their isolation.',production+trial)
        suggest('ARCH-HND-01','Production and trial/testbed boundaries are both declared; review any proposed handoff between them.',production+trial)
        signal(['testbed','trial'],'The draft declares a trial or testbed alongside production.',trial)
    if wireless:
        suggest('ARCH-WLS-01','Trial-device or wireless assets are present; confirm authentication, onboarding and the intended network access.',wireless)
        signal(['wireless','onboarding'],'The draft includes trial-device or wireless assets.',wireless)
    if robots:
        suggest('ARCH-ROB-01','A robot is present; physical command paths and emergency arrangements need a human safety review.',robots)
        signal(['robotics'],'The draft includes a robot.',robots)
    if trial and cloud:
        suggest('ARCH-TRL-01','The draft includes a trial/testbed and AWS services; review whether trial data may leave the trial boundary.',trial+cloud)
    for constraint in project.constraints:
        if constraint.key=='no_internet' and constraint.value is True:
            suggest('DEMO-NET-01','A no-internet requirement is recorded; check required external dependencies.',[constraint.id])
    local_only=[component.id for component in components if component.local_only is True]
    if local_only:suggest('DEMO-DAT-01','Some data is explicitly marked local-only; review its storage destination.',local_only)
    for clause in library.values():
        if clause['pack']!='Your local drafts':continue
        match=next((signals[tag.strip().lower()] for tag in clause['tags'] if tag.strip().lower() in signals),None)
        if match:suggest(clause['id'],'A local draft tag matches this architecture: '+match[0],match[1])
    return list(suggestions.values())


def proposal_recommendations(store,proposal_id):
    proposal=store.change(proposal_id)
    if proposal.state!='pending':raise DomainError('invalid_input','Proposal is no longer pending.')
    project=store.get(proposal.project_id)
    return recommendations_for(apply(project,proposal))


def with_policy_suggestions(project,proposal,policy_ids):
    """Append explicit user selections to the same validated acceptance transaction."""
    if not policy_ids:return proposal
    ids=validate_selection({'policy_ids':policy_ids})
    candidate=apply(project,proposal)
    allowed={item['policy_id'] for item in recommendations_for(candidate)}
    if set(ids)-allowed:raise DomainError('invalid_input','Choose policies from this proposal’s current suggestions.')
    combined=list(dict.fromkeys([*selected_ids(candidate),*ids]))
    operation=Operation(op='policy_selection',value={'policy_ids':combined})
    return proposal.model_copy(update={'operations':[*proposal.operations,operation]})
