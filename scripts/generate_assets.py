"""Additional Lucide-based architecture symbols. No model calls or external downloads."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSETS=[
 ('web-server','Web server','server','Compute'),('application-server','Application server','container','Compute'),
 ('virtual-firewall','Virtual firewall','shield-check','Security'),('vpn-gateway','VPN gateway','key-round','Networking'),
 ('robot','Mobile robot','bot','Devices & robotics'),('wireless-access-point','Wireless access point','wifi','Networking'),
 ('sensor','Sensor','radio','Devices & robotics'),('edge-gateway','Edge gateway','cpu','Devices & robotics'),
 ('operator-tablet','Operator tablet','tablet','Devices & robotics'),
 ('aws-vpc','AWS VPC','network','AWS'),('aws-alb','AWS Load Balancer','waypoints','AWS'),
 ('aws-ec2','AWS EC2','server','AWS'),('aws-rds','AWS RDS','database','AWS'),('aws-s3','AWS S3','hard-drive','AWS'),
 ('aws-waf','AWS WAF','shield-check','AWS'),('aws-cloudwatch','AWS CloudWatch','activity','AWS'),
 ('aws-iam','AWS IAM','key-round','AWS'),('aws-lambda','AWS Lambda','zap','AWS'),
 ('aws-api-gateway','AWS API Gateway','plug','AWS'),
]
def generate(output=None):
 folder=Path(output or ROOT/'fixtures/assets');folder.mkdir(parents=True,exist_ok=True);rows=[]
 for ident,label,icon,category in ASSETS:
  body=(ROOT/f'apps/web/node_modules/lucide-static/icons/{icon}.svg').read_text()
  body=body.replace('stroke="currentColor"',f'stroke="{"#c87914" if category=="AWS" else "#183d5c"}"')
  (folder/f'{ident}.svg').write_text(body)
  rows.append(dict(id=ident,type=ident,label=label,category=category,icon=f'{ident}.svg',tags=[*ident.split('-'),category.lower()],handles=['left','right','top','bottom'],size=dict(width=185,height=100),licence='ISC / Lucide 0.468.0',symbol_note='Generic service symbol, not an official AWS architecture icon' if category=='AWS' else ''))
 (folder/'extra-manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':generate()
