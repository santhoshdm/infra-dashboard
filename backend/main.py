import os
import boto3
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

AWS_ICONS = {
    "vpc": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/VPC.png",
    "subnet_public": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/PublicSubnet.png",
    "subnet_private": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/PrivateSubnet.png",
    "ec2": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Compute/EC2.png",
    "lambda": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Compute/Lambda.png",
    "igw": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/InternetGateway.png",
    "nat": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/NATGateway.png",
    "routetable": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/RouteTable.png",
    "generic": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/General/GenericResource.png"
}

def get_ec2_metrics(cw_client, instance_id):
    """Fetch CloudWatch metrics independently for a given instance."""
    try:
        res = cw_client.get_metric_data(
            MetricDataQueries=[{
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [{'Name': 'InstanceId', 'Value': instance_id}]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                }
            }],
            StartTime=datetime.utcnow() - timedelta(minutes=10),
            EndTime=datetime.utcnow()
        )
        values = res['MetricDataResults'][0].get('Values', [])
        if values:
            avg_cpu = values[0]
            if avg_cpu > 85.0:
                return "degraded", f"CPU: {avg_cpu:.1f}%"
            return "healthy", f"CPU: {avg_cpu:.1f}%"
    except Exception:
        pass
    return "healthy", "Normal"


@app.get("/api/topology")
def get_topology():
    ec2 = boto3.client('ec2', region_name=AWS_REGION)
    cw = boto3.client('cloudwatch', region_name=AWS_REGION)
    tagging = boto3.client('resourcegroupstaggingapi', region_name=AWS_REGION)

    try:
        # ------------------------------------------------------------------
        # STEP 1: Independent Top-Level AWS Resource Data Fetching
        # ------------------------------------------------------------------
        raw_vpcs = ec2.describe_vpcs().get('Vpcs', [])
        raw_subnets = ec2.describe_subnets().get('Subnets', [])
        raw_igws = ec2.describe_internet_gateways().get('InternetGateways', [])
        raw_route_tables = ec2.describe_route_tables().get('RouteTables', [])
        raw_nats = ec2.describe_nat_gateways().get('NatGateways', [])
        
        reservations = ec2.describe_instances().get('Reservations', [])
        raw_instances = [inst for r in reservations for inst in r.get('Instances', [])]
        
        raw_tagged = tagging.get_resources().get('ResourceTagMappingList', [])

        # ------------------------------------------------------------------
        # STEP 2: In-Memory Relationship Indexing & Architectural Inference
        # ------------------------------------------------------------------
        # Map IGWs to VPCs
        vpc_to_igws = {}
        for igw in raw_igws:
            for attachment in igw.get('Attachments', []):
                vpc_id = attachment.get('VpcId')
                if vpc_id:
                    vpc_to_igws.setdefault(vpc_id, []).append(igw)

        # Identify Public Subnets via Route Table inspects (Route to 0.0.0.0/0 via IGW)
        public_subnet_ids = set()
        subnet_to_rts = {}
        for rt in raw_route_tables:
            has_igw_route = any(
                route.get('GatewayId', '').startswith('igw-') 
                for route in rt.get('Routes', [])
            )
            for assoc in rt.get('Associations', []):
                s_id = assoc.get('SubnetId')
                if s_id:
                    subnet_to_rts.setdefault(s_id, []).append(rt)
                    if has_igw_route:
                        public_subnet_ids.add(s_id)

        # Group Subnets, NATs, EC2s by Subnet and VPC
        vpc_to_subnets = {}
        for sub in raw_subnets:
            vpc_to_subnets.setdefault(sub['VpcId'], []).append(sub)

        subnet_to_nats = {}
        for nat in raw_nats:
            if nat.get('SubnetId'):
                subnet_to_nats.setdefault(nat['SubnetId'], []).append(nat)

        subnet_to_instances = {}
        for inst in raw_instances:
            if inst.get('SubnetId'):
                subnet_to_instances.setdefault(inst['SubnetId'], []).append(inst)

        # ------------------------------------------------------------------
        # STEP 3: Graph Construction (Nodes and Edges)
        # ------------------------------------------------------------------
        nodes = []
        edges = []
        vpc_x_offset = 50

        for vpc in raw_vpcs:
            vpc_id = vpc['VpcId']
            vpc_name = next((t['Value'] for t in vpc.get('Tags', []) if t['Key'] == 'Name'), vpc_id)
            subnets_in_vpc = vpc_to_subnets.get(vpc_id, [])

            # Compute VPC Container bounds dynamically based on children
            subnet_count = max(len(subnets_in_vpc), 1)
            vpc_width = max(subnet_count * 430 + 60, 500)

            nodes.append({
                "id": vpc_id,
                "type": "vpcContainer",
                "data": {
                    "label": f"VPC: {vpc_name} ({vpc['CidrBlock']})",
                    "icon": AWS_ICONS["vpc"]
                },
                "position": {"x": vpc_x_offset, "y": 50},
                "style": {
                    "width": vpc_width,
                    "height": 620,
                    "backgroundColor": "rgba(35, 47, 62, 0.25)",
                    "border": "2px dashed #ff9900",
                    "borderRadius": "12px"
                }
            })

            # Attach Internet Gateways at VPC top level
            igw_x = 40
            for igw in vpc_to_igws.get(vpc_id, []):
                igw_id = igw['InternetGatewayId']
                nodes.append({
                    "id": igw_id,
                    "type": "awsNode",
                    "parentNode": vpc_id,
                    "extent": "parent",
                    "data": {
                        "label": f"IGW: {igw_id}",
                        "service": "igw",
                        "status": "healthy",
                        "metric": "Active",
                        "icon": AWS_ICONS["igw"]
                    },
                    "position": {"x": igw_x, "y": 60}
                })
                igw_x += 240

            # Layout Subnets and inside resources
            subnet_x = 40
            for sub in subnets_in_vpc:
                sub_id = sub['SubnetId']
                sub_name = next((t['Value'] for t in sub.get('Tags', []) if t['Key'] == 'Name'), sub_id)
                is_public = (sub_id in public_subnet_ids) or sub.get('MapPublicIpOnLaunch', False)

                nodes.append({
                    "id": sub_id,
                    "type": "subnetContainer",
                    "parentNode": vpc_id,
                    "extent": "parent",
                    "data": {
                        "label": f"{'Public' if is_public else 'Private'} Subnet: {sub_name}",
                        "icon": AWS_ICONS["subnet_public"] if is_public else AWS_ICONS["subnet_private"]
                    },
                    "position": {"x": subnet_x, "y": 180},
                    "style": {
                        "width": 390,
                        "height": 400,
                        "backgroundColor": "rgba(15, 23, 42, 0.45)",
                        "border": "1.5px solid #00a4e4" if is_public else "1.5px solid #00c7b7",
                        "borderRadius": "8px"
                    }
                })

                inner_y = 50

                # 1. Route Tables inside Subnet
                for rt in subnet_to_rts.get(sub_id, []):
                    rt_id = rt['RouteTableId']
                    node_id = f"{sub_id}-{rt_id}"
                    nodes.append({
                        "id": node_id,
                        "type": "awsNode",
                        "parentNode": sub_id,
                        "extent": "parent",
                        "data": {
                            "label": f"Route Table: {rt_id}",
                            "service": "routetable",
                            "status": "healthy",
                            "metric": "Associated",
                            "icon": AWS_ICONS["routetable"]
                        },
                        "position": {"x": 20, "y": inner_y}
                    })
                    inner_y += 85

                    # Map Edge: IGW -> Route Table
                    for igw in vpc_to_igws.get(vpc_id, []):
                        edges.append({
                            "id": f"e-{igw['InternetGatewayId']}-{node_id}",
                            "source": igw['InternetGatewayId'],
                            "target": node_id,
                            "animated": True,
                            "style": {"stroke": "#00a4e4", "strokeWidth": 2}
                        })

                # 2. NAT Gateways inside Subnet
                for nat in subnet_to_nats.get(sub_id, []):
                    nat_id = nat['NatGatewayId']
                    state = nat.get('State', 'unknown')
                    nodes.append({
                        "id": nat_id,
                        "type": "awsNode",
                        "parentNode": sub_id,
                        "extent": "parent",
                        "data": {
                            "label": f"NAT: {nat_id}",
                            "service": "nat",
                            "status": "healthy" if state == "available" else "degraded",
                            "metric": state.capitalize(),
                            "icon": AWS_ICONS["nat"]
                        },
                        "position": {"x": 20, "y": inner_y}
                    })
                    inner_y += 85

                # 3. EC2 Instances inside Subnet
                for inst in subnet_to_instances.get(sub_id, []):
                    inst_id = inst['InstanceId']
                    raw_state = inst['State']['Name']

                    if raw_state == "running":
                        status, metric_txt = get_ec2_metrics(cw, inst_id)
                    else:
                        status, metric_txt = "error", raw_state.capitalize()

                    nodes.append({
                        "id": inst_id,
                        "type": "awsNode",
                        "parentNode": sub_id,
                        "extent": "parent",
                        "data": {
                            "label": f"EC2: {inst_id}",
                            "service": "ec2",
                            "status": status,
                            "metric": metric_txt,
                            "icon": AWS_ICONS["ec2"],
                            "tags": {t['Key']: t['Value'] for t in inst.get('Tags', [])}
                        },
                        "position": {"x": 20, "y": inner_y}
                    })
                    inner_y += 85

                subnet_x += 430

            vpc_x_offset += vpc_width + 80

        # Unbound / Serverless / Tagged Resources (e.g. Lambda, DynamoDB)
        extra_x = 50
        for item in raw_tagged:
            arn = item['ResourceARN']
            service = arn.split(':')[2] if len(arn.split(':')) > 2 else 'generic'
            if service in ['lambda', 'dynamodb', 's3']:
                res_id = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]
                nodes.append({
                    "id": res_id,
                    "type": "awsNode",
                    "data": {
                        "label": f"{service.upper()}: {res_id}",
                        "service": service,
                        "status": "healthy",
                        "metric": "Active",
                        "icon": AWS_ICONS.get(service, AWS_ICONS["generic"]),
                        "tags": {t['Key']: t['Value'] for t in item.get('Tags', [])}
                    },
                    "position": {"x": extra_x, "y": 720}
                })
                extra_x += 240

        return {"nodes": nodes, "edges": edges, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        return {"error": str(e), "nodes": [], "edges": []}