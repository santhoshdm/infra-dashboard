import os
import boto3
from datetime import datetime
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

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))

AWS_ICONS = {
    "vpc": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/VPC.png",
    "subnet_public": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/PublicSubnet.png",
    "subnet_private": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/PrivateSubnet.png",
    "ec2": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Compute/EC2.png",
    "igw": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/InternetGateway.png",
    "nat": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/NATGateway.png"
}

@app.get("/api/topology")
def get_topology():
    ec2 = boto3.client('ec2', region_name=AWS_REGION)

    try:
        raw_vpcs = ec2.describe_vpcs().get('Vpcs', [])
        raw_subnets = ec2.describe_subnets().get('Subnets', [])
        raw_igws = ec2.describe_internet_gateways().get('InternetGateways', [])
        
        reservations = ec2.describe_instances().get('Reservations', [])
        raw_instances = [inst for r in reservations for inst in r.get('Instances', [])]

        # Group subnets & instances
        vpc_to_subnets = {}
        for sub in raw_subnets:
            vpc_to_subnets.setdefault(sub['VpcId'], []).append(sub)

        subnet_to_instances = {}
        for inst in raw_instances:
            if inst.get('SubnetId'):
                subnet_to_instances.setdefault(inst['SubnetId'], []).append(inst)

        nodes = []
        edges = []
        vpc_x_offset = 50

        for vpc in raw_vpcs:
            vpc_id = vpc['VpcId']
            vpc_name = next((t['Value'] for t in vpc.get('Tags', []) if t['Key'] == 'Name'), vpc_id)
            subnets_in_vpc = vpc_to_subnets.get(vpc_id, [])

            # DYNAMIC SIZING CALCULATIONS:
            # Subnet width = 380, spacing = 40. 
            subnet_count = max(len(subnets_in_vpc), 1)
            vpc_width = (subnet_count * 420) + 60

            nodes.append({
                "id": vpc_id,
                "type": "vpcContainer",
                "data": {
                    "label": f"VPC: {vpc_name} ({vpc.get('CidrBlock', '')})",
                    "icon": AWS_ICONS["vpc"]
                },
                "position": {"x": vpc_x_offset, "y": 50},
                "style": {
                    "width": vpc_width,
                    "height": 550,
                    "backgroundColor": "rgba(15, 23, 42, 0.85)",
                    "border": "2px dashed #ff9900",
                    "borderRadius": "12px"
                }
            })

            subnet_x = 30
            for sub in subnets_in_vpc:
                sub_id = sub['SubnetId']
                sub_name = next((t['Value'] for t in sub.get('Tags', []) if t['Key'] == 'Name'), sub_id)
                is_public = sub.get('MapPublicIpOnLaunch', False)

                nodes.append({
                    "id": sub_id,
                    "type": "subnetContainer",
                    "parentNode": vpc_id,
                    "extent": "parent",
                    "data": {
                        "label": f"{'Public' if is_public else 'Private'} Subnet: {sub_name}",
                        "isPublic": is_public
                    },
                    "position": {"x": subnet_x, "y": 70},
                    "style": {
                        "width": 380,
                        "height": 380,
                        "backgroundColor": "rgba(30, 41, 59, 0.6)",
                        "border": f"1.5px dashed {'#00a4e4' if is_public else '#00c7b7'}",
                        "borderRadius": "8px"
                    }
                })

                # Instances inside subnet
                inst_y = 60
                for inst in subnet_to_instances.get(sub_id, []):
                    inst_id = inst['InstanceId']
                    state = inst['State']['Name']
                    name = next((t['Value'] for t in inst.get('Tags', []) if t['Key'] == 'Name'), inst_id)

                    nodes.append({
                        "id": inst_id,
                        "type": "awsNode",
                        "parentNode": sub_id,
                        "extent": "parent",
                        "data": {
                            "label": name,
                            "service": "ec2",
                            "status": state,
                            "metric": inst.get("InstanceType", ""),
                            "icon": AWS_ICONS["ec2"]
                        },
                        "position": {"x": 20, "y": inst_y}
                    })
                    inst_y += 90

                subnet_x += 420

            # Attach IGW to bottom of VPC
            igw_x = 30
            for igw in raw_igws:
                for attachment in igw.get('Attachments', []):
                    if attachment.get('VpcId') == vpc_id:
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
                                "metric": "Attached",
                                "icon": AWS_ICONS["igw"]
                            },
                            "position": {"x": igw_x, "y": 460}
                        })
                        igw_x += 240

            vpc_x_offset += vpc_width + 80

        return {"nodes": nodes, "edges": edges, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        return {"error": str(e), "nodes": [], "edges": []}