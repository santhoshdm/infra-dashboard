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

        # -------------------------------------------------------------------
        # STEP 1 & 2: FETCH & FILTER ALL RESOURCES INDEPENDENTLY
        # -------------------------------------------------------------------
        raw_vpcs = ec2.describe_vpcs().get("Vpcs", [])
        raw_subnets = ec2.describe_subnets().get("Subnets", [])
        raw_igws = ec2.describe_internet_gateways().get("InternetGateways", [])
        reservations = ec2.describe_instances().get("Reservations", [])
        raw_instances = [inst for r in reservations for inst in r.get("Instances", [])]

        # Pure tag filtering (zero inter-resource dependency)
        matched_vpcs = [v for v in raw_vpcs if matches_env(v.get("Tags"), env)]
        matched_subnets = [s for s in raw_subnets if matches_env(s.get("Tags"), env)]
        matched_igws = [i for i in raw_igws if matches_env(i.get("Tags"), env)]
        matched_instances = [inst for inst in raw_instances if matches_env(inst.get("Tags"), env)]

        matched_vpc_ids = {v["VpcId"] for v in matched_vpcs}
        matched_subnet_ids = {s["SubnetId"] for s in matched_subnets}

        nodes = []
        edges = []
        
        # Track which resources get attached into containers
        attached_subnets = set()
        attached_instances = set()
        attached_igws = set()

        # -------------------------------------------------------------------
        # STEP 3: RENDER VPC CONTAINERS & ATTACH QUALIFYING CHILDREN
        # -------------------------------------------------------------------
        vpc_x_offset = 50

        for vpc in matched_vpcs:
            vpc_id = vpc["VpcId"]
            vpc_name = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), vpc_id)
            
            # Subnets that belong to this VPC AND matched the tag
            subnets_in_vpc = [s for s in matched_subnets if s.get("VpcId") == vpc_id]
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
                attached_subnets.add(sub_id)
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

                # Attach EC2 instances to this Subnet IF instance matches tag
                inst_y = 60
                for inst in matched_instances:
                    if inst.get("SubnetId") == sub_id:
                        inst_id = inst["InstanceId"]
                        attached_instances.add(inst_id)
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

            # Attach IGWs to this VPC IF IGW matches tag and has attachment
            igw_x = 30
            for igw in matched_igws:
                for attachment in igw.get("Attachments", []):
                    if attachment.get("VpcId") == vpc_id:
                        igw_id = igw["InternetGatewayId"]
                        attached_igws.add(igw_id)
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

        # -------------------------------------------------------------------
        # STEP 4: RENDER ALL STANDALONE / UNATTACHED MATCHED RESOURCES
        # -------------------------------------------------------------------
        # Position standalone nodes off to the right of the VPC containers
        standalone_x = vpc_x_offset if matched_vpcs else 50
        standalone_y = 50

        # 1. Unattached / Standalone IGWs
        for igw in matched_igws:
            if igw["InternetGatewayId"] not in attached_igws:
                igw_id = igw["InternetGatewayId"]
                state_str = "Attached (Other VPC)" if igw.get("Attachments") else "Detached"
                nodes.append({
                    "id": igw_id,
                    "type": "awsNode",
                    "data": {
                        "label": f"IGW: {igw_id}",
                        "service": "igw",
                        "status": "degraded" if state_str == "Detached" else "healthy",
                        "metric": state_str,
                        "icon": AWS_ICONS["igw"]
                    },
                    "position": {"x": standalone_x, "y": standalone_y}
                })
                standalone_y += 100

        # 2. Standalone Subnets (Subnet matched tag, but its VPC did not)
        for sub in matched_subnets:
            if sub["SubnetId"] not in attached_subnets:
                sub_id = sub["SubnetId"]
                sub_name = next((t["Value"] for t in sub.get("Tags", []) if t["Key"] == "Name"), sub_id)
                nodes.append({
                    "id": sub_id,
                    "type": "awsNode",
                    "data": {
                        "label": f"Subnet: {sub_name}",
                        "service": "subnet",
                        "status": "healthy",
                        "metric": f"VPC: {sub.get('VpcId')}",
                        "icon": AWS_ICONS["subnet_public"]
                    },
                    "position": {"x": standalone_x, "y": standalone_y}
                })
                standalone_y += 100

        # 3. Standalone EC2 Instances (Instance matched tag, but its Subnet did not)
        for inst in matched_instances:
            if inst["InstanceId"] not in attached_instances:
                inst_id = inst["InstanceId"]
                state = inst.get("State", {}).get("Name", "unknown")
                name = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), inst_id)
                nodes.append({
                    "id": inst_id,
                    "type": "awsNode",
                    "data": {
                        "label": f"{name} (Orphaned)",
                        "service": "ec2",
                        "status": state,
                        "metric": inst.get("InstanceType", ""),
                        "icon": AWS_ICONS["ec2"]
                    },
                    "position": {"x": standalone_x, "y": standalone_y}
                })
                standalone_y += 100

        return {"nodes": nodes, "edges": edges}

    except (BotoCoreError, ClientError) as e:
        logger.error(f"AWS API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))