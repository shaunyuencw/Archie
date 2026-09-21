"""Readable browse categories for fictional policy drafts."""
CATEGORIES = [
    {'id':'network-access','name':'Network & access','description':'Zones, allowed connections, identity and encrypted sessions.'},
    {'id':'cloud-hybrid','name':'Cloud & hybrid connections','description':'AWS boundaries, on-premises links and outbound dependencies.'},
    {'id':'data-recovery','name':'Data, secrets & backups','description':'Data handling, credentials, retention and recovery.'},
    {'id':'resilience-monitoring','name':'Resilience & monitoring','description':'Availability, audit trails, capacity and operational visibility.'},
    {'id':'devices-testbed','name':'Devices & testbeds','description':'Wireless onboarding, robotics trials and production separation.'},
    {'id':'operations','name':'Ownership & operations','description':'Support, maintenance, usability and human approval responsibilities.'},
    {'id':'local-drafts','name':'Other local drafts','description':'Locally authored policies without a matching category.'},
]
GROUPS = {
    'network-access': {'DEMO-ZON-01','DEMO-ADM-01','DEMO-FW-01','DEMO-IF-01','DEMO-MAN-01','ARCH-SEG-01','ARCH-DAT-01','ARCH-FLW-01','ARCH-TLS-01','ARCH-IAM-01','ARCH-LPR-01','ARCH-BOUND-01'},
    'cloud-hybrid': {'DEMO-NET-01','ARCH-CLD-01','ARCH-EGR-01','ARCH-HYB-01'},
    'data-recovery': {'DEMO-DAT-01','DEMO-MAN-02','DEMO-MAN-05','DEMO-MAN-06','ARCH-SEC-01','ARCH-BAK-01','ARCH-DATA-01'},
    'resilience-monitoring': {'DEMO-HA-01','DEMO-AUD-01','DEMO-MAN-08','DEMO-MAN-09','ARCH-AVL-01','ARCH-LOG-01'},
    'devices-testbed': {'ARCH-TST-01','ARCH-HND-01','ARCH-WLS-01','ARCH-ROB-01','ARCH-TRL-01'},
    'operations': {'DEMO-MAN-03','DEMO-MAN-04','DEMO-MAN-07','DEMO-MAN-10','DEMO-MAN-11','DEMO-MAN-12','ARCH-PAT-01','ARCH-OWN-01'},
}
TAG_CATEGORIES = [
    ('devices-testbed', {'wireless','robotics','trial','testbed','onboarding'}),
    ('cloud-hybrid', {'aws','cloud','hybrid','vpn','egress','internet'}),
    ('data-recovery', {'backup','restore','recovery','data','retention','privacy','secrets','credentials','crypto'}),
    ('resilience-monitoring', {'availability','redundancy','failover','resilience','monitoring','audit','logging','capacity'}),
    ('network-access', {'zone','segmentation','network','identity','management','enforcement','firewall','tls','protocol','least privilege'}),
    ('operations', {'ownership','operations','patch','support','supplier','accessibility','decommission','ppm','physical'}),
]


def category_for(clause):
    for category, ids in GROUPS.items():
        if clause['id'] in ids:return category
    tags={tag.strip().lower() for tag in clause.get('tags',[])}
    return next((category for category,keywords in TAG_CATEGORIES if tags&keywords),'local-drafts')
