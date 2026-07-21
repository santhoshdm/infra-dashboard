import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

// High-resolution AWS Official SVGs via Reliable CDN
const AWS_ICONS = {
  vpc: 'https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/VPC.png',
  subnet_public: 'https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/PublicSubnet.png',
  subnet_private: 'https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/GroupIcons/PrivateSubnet.png',
  ec2: 'https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/Compute/EC2.png',
  igw: 'https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/InternetGateway.png',
  nat: 'https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist/NetworkingContentDelivery/NATGateway.png'
};

const statusColors = {
  healthy: '#10b981',
  running: '#10b981',
  degraded: '#f59e0b',
  error: '#ef4444',
  stopped: '#ef4444'
};

// 1. AWS Resource Node (EC2, IGW, NAT)
export const AwsResourceNode = memo(({ data }) => {
  const service = data?.service?.toLowerCase() || 'ec2';
  const iconUrl = data?.icon || AWS_ICONS[service] || AWS_ICONS.ec2;
  const statusColor = statusColors[data?.status?.toLowerCase()] || statusColors[data?.state?.toLowerCase()] || '#10b981';

  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '8px',
      background: '#1e293b',
      border: `2px solid ${statusColor}`,
      color: '#f8fafc',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      minWidth: '220px',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.4)',
      boxSizing: 'border-box'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: statusColor }} />
      
      <img src={iconUrl} alt={service} style={{ width: '32px', height: '32px', objectFit: 'contain' }} />

      <div style={{ flexGrow: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#f8fafc' }}>
          {data.label}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
          <span style={{ fontSize: '10px', color: statusColor, fontWeight: 'bold' }}>
            ● {data.status || data.state || 'ACTIVE'}
          </span>
          <span style={{ fontSize: '10px', color: '#94a3b8' }}>
            {data.metric || ''}
          </span>
        </div>
      </div>

      <Handle type="source" position={Position.Right} style={{ background: statusColor }} />
    </div>
  );
});

// 2. VPC Container Node
export const VpcContainerNode = memo(({ data }) => (
  <div style={{
    padding: '12px 16px',
    color: '#ff9900',
    fontWeight: 'bold',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    background: 'rgba(15, 23, 42, 0.65)',
    borderTopLeftRadius: '10px',
    borderTopRightRadius: '10px'
  }}>
    <img src={AWS_ICONS.vpc} alt="VPC" style={{ width: '28px', height: '28px' }} />
    <span>{data.label}</span>
  </div>
));

// 3. Subnet Container Node
export const SubnetContainerNode = memo(({ data }) => {
  const isPublic = data.isPublic;
  const color = isPublic ? '#00a4e4' : '#00c7b7';
  const icon = isPublic ? AWS_ICONS.subnet_public : AWS_ICONS.subnet_private;

  return (
    <div style={{
      padding: '10px 14px',
      color: color,
      fontWeight: 'bold',
      fontSize: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      background: 'rgba(30, 41, 59, 0.7)',
      borderTopLeftRadius: '6px',
      borderTopRightRadius: '6px'
    }}>
      <img src={icon} alt="Subnet" style={{ width: '22px', height: '22px' }} />
      <span>{data.label}</span>
    </div>
  );
});