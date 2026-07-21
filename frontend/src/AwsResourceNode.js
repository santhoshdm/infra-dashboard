import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const statusConfig = {
  healthy: { color: '#10b981', badge: 'RUNNING' },
  degraded: { color: '#f59e0b', badge: 'WARNING' },
  error: { color: '#ef4444', badge: 'STOPPED' }
};

// Standard Resource Node (EC2, IGW, NAT, Route Table)
export const AwsResourceNode = memo(({ data }) => {
  const cfg = statusConfig[data.status] || { color: '#6b7280', badge: 'UNKNOWN' };

  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '8px',
      background: '#1a2234',
      color: '#ffffff',
      border: `2px solid ${cfg.color}`,
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      minWidth: '220px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: cfg.color }} />
      
      {data.icon && <img src={data.icon} alt={data.service} style={{ width: '30px', height: '30px' }} />}
      
      <div style={{ flexGrow: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {data.label}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
          <span style={{ fontSize: '10px', color: cfg.color, fontWeight: 'bold' }}>
            ● {cfg.badge}
          </span>
          <span style={{ fontSize: '10px', color: '#94a3b8' }}>
            {data.metric}
          </span>
        </div>
      </div>

      <Handle type="source" position={Position.Right} style={{ background: cfg.color }} />
    </div>
  );
});

// Outer VPC Group Container
export const VpcContainerNode = memo(({ data }) => (
  <div style={{ padding: '12px', color: '#ff9900', fontWeight: 'bold', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
    <img src={data.icon} alt="VPC" style={{ width: '24px', height: '24px' }} />
    {data.label}
  </div>
));

// Subnet Group Container
export const SubnetContainerNode = memo(({ data }) => (
  <div style={{ padding: '10px', color: '#00a4e4', fontWeight: 'bold', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
    <img src={data.icon} alt="Subnet" style={{ width: '20px', height: '20px' }} />
    {data.label}
  </div>
));