import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aws-topology")

app = FastAPI(title="AWS Topology API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "ap-south-1"))

AWS_ICONS = {
    "vpc": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Groups/VPC.png",
    "subnet_public": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Groups/PublicSubnet.png",
    "subnet_private": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Groups/PrivateSubnet.png",
    "ec2": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Compute/EC2.png",
    "igw": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContent/VPCInternetGateway.png"
}

def matches_env(tags_list: Optional[List[Dict[str, str]]], target_env: Optional[str]) -> bool:
    """Evaluates if a resource directly matches the requested environment tag."""
    if not target_env or target_env.lower() in ["all", ""]:
        return True
    
    tags = {t.get("Key", "").lower(): t.get("Value", "").lower() for t in (tags_list or [])}
    env_val = tags.get("environment") or tags.get("env")
    return env_val == target_env.lower()

@app.get("/api/topology")
def get_topology(env: Optional[str] = Query(None)):
    try:
        ec2 = boto3.client("ec2", region_name=AWS_REGION)

        # 1. Fetch ALL raw resources independently from AWS
        raw_vpcs = ec2.describe_vpcs().get("Vpcs", [])
        raw_subnets = ec2.describe_subnets().get("Subnets", [])
        raw_igws = ec2.describe_internet_gateways().get("InternetGateways", [])
        
        reservations = ec2.describe_instances().get("Reservations", [])
        raw_instances = [inst for r in reservations for inst in r.get("Instances", [])]

        # 2. INDEPENDENT TAG FILTERING
        # Each resource category is filtered purely by its own tags
        directly_matched_vpcs = [v for v in raw_vpcs if matches_env(v.get("Tags"), env)]
        directly_matched_subnets = [s for s in raw_subnets if matches_env(s.get("Tags"), env)]
        directly_matched_igws = [i for i in raw_igws if matches_env(i.get("Tags"), env)]
        directly_matched_instances = [inst for inst in raw_instances if matches_env(inst.get("Tags"), env)]

        # 3. CONSTRUCT WORKING SET (Ensure valid hierarchy display)
        # Include subnets if directly matched OR if their parent VPC matched
        matched_vpc_ids = {v["VpcId"] for v in directly_matched_vpcs}
        
        final_subnets = [
            s for s in raw_subnets 
            if s["SubnetId"] in {sub["SubnetId"] for sub in directly_matched_subnets} or s["VpcId"] in matched_vpc_ids
        ]

        # Ensure parent VPCs exist for any matched subnets/IGWs
        required_vpc_ids = matched_vpc_ids.union({s["VpcId"] for s in final_subnets})
        for igw in directly_matched_igws:
            for att in igw.get("Attachments", []):
                if att.get("VpcId"):
                    required_vpc_ids.add(att["VpcId"])

        final_vpcs = [v for v in raw_vpcs if v["VpcId"] in required_vpc_ids]

        # Group subnets & instances by parent IDs
        vpc_to_subnets: Dict[str, List[Dict[str, Any]]] = {}
        for sub in final_subnets:
            vpc_to_subnets.setdefault(sub["VpcId"], []).append(sub)

        subnet_to_instances: Dict[str, List[Dict[str, Any]]] = {}
        for inst in directly_matched_instances:
            sub_id = inst.get("SubnetId")
            if sub_id:
                subnet_to_instances.setdefault(sub_id, []).append(inst)

        nodes = []
        edges = []
        vpc_x_offset = 50

        # 4. BUILD CANVAS TOPOLOGY
        for vpc in final_vpcs:
            vpc_id = vpc["VpcId"]
            vpc_name = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), vpc_id)
            subnets_in_vpc = vpc_to_subnets.get(vpc_id, [])

            subnet_count = max(len(subnets_in_vpc), 1)
            vpc_width = (subnet_count * 420) + 60

            # Render VPC Container Node
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
                sub_id = sub["SubnetId"]
                sub_name = next((t["Value"] for t in sub.get("Tags", []) if t["Key"] == "Name"), sub_id)
                is_public = sub.get("MapPublicIpOnLaunch", False)

                # Render Subnet Container Node
                nodes.append({
                    "id": sub_id,
                    "type": "subnetContainer",
                    "parentNode": vpc_id,
                    "extent": "parent",
                    "data": {
                        "label": f"{'Public' if is_public else 'Private'} Subnet: {sub_name}",
                        "isPublic": is_public,
                        "icon": AWS_ICONS["subnet_public"] if is_public else AWS_ICONS["subnet_private"]
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

                # Render EC2 Instances inside Subnet (if any match the filter)
                inst_y = 60
                for inst in subnet_to_instances.get(sub_id, []):
                    inst_id = inst["InstanceId"]
                    state = inst.get("State", {}).get("Name", "unknown")
                    name = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), inst_id)

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

            # Render IGWs attached to this VPC (if IGW matches filter)
            igw_x = 30
            for igw in directly_matched_igws:
                for attachment in igw.get("Attachments", []):
                    if attachment.get("VpcId") == vpc_id:
                        igw_id = igw["InternetGatewayId"]
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

        return {"nodes": nodes, "edges": edges}

    except (BotoCoreError, ClientError) as e:
        logger.error(f"AWS API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))