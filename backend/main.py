from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aws-topology")

app = FastAPI(title="AWS Topology API")

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS PlantUML Icon CDN URLs
ICONS = {
    "vpc": "https://raw.githubusercontent.com/plantuml-stdlib/AWS-PlantUML/main/dist/NetworkingContent/VPC.png",
    "subnet": "https://raw.githubusercontent.com/plantuml-stdlib/AWS-PlantUML/main/dist/NetworkingContent/VPCsubnetpublic.png",
    "ec2": "https://raw.githubusercontent.com/plantuml-stdlib/AWS-PlantUML/main/dist/Compute/EC2.png",
    "igw": "https://raw.githubusercontent.com/plantuml-stdlib/AWS-PlantUML/main/dist/NetworkingContent/VPCInternetGateway.png",
    "nat": "https://raw.githubusercontent.com/plantuml-stdlib/AWS-PlantUML/main/dist/NetworkingContent/VPCNATGateway.png",
    "route_table": "https://raw.githubusercontent.com/plantuml-stdlib/AWS-PlantUML/main/dist/NetworkingContent/VPCRouteTable.png"
}

def get_ec2_client():
    return boto3.client("ec2")

def get_cloudwatch_client():
    return boto3.client("cloudwatch")

@app.get("/api/topology")
def get_topology():
    try:
        ec2 = get_ec2_client()
        cw = get_cloudwatch_client()

        nodes = []
        edges = []

        # -------------------------------------------------------------
        # 1. Fetch VPCs (Container Parent Nodes)
        # -------------------------------------------------------------
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
        vpc_x_offset = 0

        for vpc in vpcs:
            vpc_id = vpc["VpcId"]
            cidr = vpc.get("CidrBlock", "")
            
            nodes.append({
                "id": vpc_id,
                "type": "vpcContainer",
                "position": {"x": vpc_x_offset, "y": 0},
                "data": {
                    "label": f"VPC: {vpc_id} ({cidr})",
                    "icon": ICONS["vpc"]
                },
                "style": {
                    "width": 750,
                    "height": 500,
                    "backgroundColor": "rgba(15, 23, 42, 0.4)",
                    "border": "2px dashed #ff9900",
                    "borderRadius": "12px"
                }
            })

            # ---------------------------------------------------------
            # 2. Fetch Subnets inside this VPC
            # ---------------------------------------------------------
            subnets = ec2.describe_subnets(
                Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
            ).get("Subnets", [])

            subnet_x_offset = 30
            for subnet in subnets:
                subnet_id = subnet["SubnetId"]
                sub_cidr = subnet.get("CidrBlock", "")
                
                nodes.append({
                    "id": subnet_id,
                    "type": "subnetContainer",
                    "parentId": vpc_id,
                    "extent": "parent",
                    "position": {"x": subnet_x_offset, "y": 60},
                    "data": {
                        "label": f"Subnet: {subnet_id} ({sub_cidr})",
                        "icon": ICONS["subnet"]
                    },
                    "style": {
                        "width": 330,
                        "height": 380,
                        "backgroundColor": "rgba(30, 41, 59, 0.6)",
                        "border": "1px dashed #00a4e4",
                        "borderRadius": "8px"
                    }
                })

                # -----------------------------------------------------
                # 3. Fetch EC2 Instances inside this Subnet
                # -----------------------------------------------------
                reservations = ec2.describe_instances(
                    Filters=[{"Name": "subnet-id", "Values": [subnet_id]}]
                ).get("Reservations", [])

                instance_y_offset = 60
                for res in reservations:
                    for inst in res.get("Instances", []):
                        inst_id = inst["InstanceId"]
                        state = inst.get("State", {}).get("Name", "unknown")
                        
                        # Determine status badge mapping
                        status = "healthy" if state == "running" else "error"
                        
                        # Get Name Tag if present
                        name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), inst_id)

                        nodes.append({
                            "id": inst_id,
                            "type": "awsNode",
                            "parentId": subnet_id,
                            "extent": "parent",
                            "position": {"x": 20, "y": instance_y_offset},
                            "data": {
                                "label": name_tag,
                                "service": "EC2",
                                "status": status,
                                "metric": f"State: {state}",
                                "icon": ICONS["ec2"]
                            }
                        })
                        instance_y_offset += 100

                subnet_x_offset += 350

            # ---------------------------------------------------------
            # 4. Fetch Gateways and Route Tables for this VPC
            # ---------------------------------------------------------
            igws = ec2.describe_internet_gateways(
                Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
            ).get("InternetGateways", [])

            for igw in igws:
                igw_id = igw["InternetGatewayId"]
                nodes.append({
                    "id": igw_id,
                    "type": "awsNode",
                    "parentId": vpc_id,
                    "extent": "parent",
                    "position": {"x": 30, "y": 420},
                    "data": {
                        "label": f"IGW: {igw_id}",
                        "service": "IGW",
                        "status": "healthy",
                        "metric": "Attached",
                        "icon": ICONS["igw"]
                    }
                })

            nat_gws = ec2.describe_nat_gateways(
                Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
            ).get("NatGateways", [])

            for nat in nat_gws:
                nat_id = nat["NatGatewayId"]
                state = nat.get("State", "unknown")
                nodes.append({
                    "id": nat_id,
                    "type": "awsNode",
                    "parentId": vpc_id,
                    "extent": "parent",
                    "position": {"x": 280, "y": 420},
                    "data": {
                        "label": f"NAT: {nat_id}",
                        "service": "NAT",
                        "status": "healthy" if state == "available" else "degraded",
                        "metric": f"State: {state}",
                        "icon": ICONS["nat"]
                    }
                })

            vpc_x_offset += 800

        return {"nodes": nodes, "edges": edges}

    except (BotoCoreError, ClientError) as e:
        logger.error(f"AWS API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))