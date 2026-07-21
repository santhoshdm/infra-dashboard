import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const statusConfig = {
  healthy: { color: '#10b981', badge: 'RUNNING' },
  degraded: { color: '#f59e0b', badge: 'WARNING' },
  error: { color: '#ef4444', badge: 'STOPPED' }
};

// Standard AWS Resource Node (EC2, NAT, IGW, RouteTable)
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
      
      {/* Renders Official AWS PlantUML Icon */}
      {data.icon && <img src={data.icon} alt={data.service} style={{ width: '32px', height: '32px' }} />}
      
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

// Outer VPC Container Node
export const VpcContainerNode = memo(({ data }) => (
  <div style={{ padding: '12px', color: '#ff9900', fontWeight: 'bold', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
    <img src={data.icon} alt="VPC" style={{ width: '26px', height: '26px' }} />
    {data.label}
  </div>
));

// Subnet Container Node
export const SubnetContainerNode = memo(({ data }) => (
  <div style={{ padding: '10px', color: '#00a4e4', fontWeight: 'bold', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
    <img src={data.icon} alt="Subnet" style={{ width: '22px', height: '22px' }} />
    {data.label}
  </div>
));