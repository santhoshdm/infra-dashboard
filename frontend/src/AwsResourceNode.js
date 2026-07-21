import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

// Embedded SVG fallbacks if image fails to load
const FallbackIcon = ({ type, color = '#ff9900' }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="20" rx="4" />
    <path d="M6 12h12M12 6v12" />
  </svg>
);

const statusColors = {
  running: '#10b981',
  healthy: '#10b981',
  stopped: '#ef4444',
  degraded: '#f59e0b'
};

export const AwsResourceNode = memo(({ data }) => {
  const statusColor = statusColors[data?.status?.toLowerCase()] || '#10b981';

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
      boxShadow: '0 4px 12px rgba(0,0,0,0.4)'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: statusColor }} />
      
      <img 
        src={data.icon} 
        alt="" 
        style={{ width: '32px', height: '32px', objectFit: 'contain' }}
        onError={(e) => { e.target.style.display = 'none'; }} 
      />

      <div style={{ flexGrow: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#f8fafc' }}>
          {data.label}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
          <span style={{ fontSize: '10px', color: statusColor, fontWeight: 'bold' }}>
            ● {data.status || 'ACTIVE'}
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

export const VpcContainerNode = memo(({ data }) => (
  <div style={{
    padding: '12px 16px',
    color: '#ff9900',
    fontWeight: 'bold',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    background: 'rgba(15, 23, 42, 0.7)',
    borderTopLeftRadius: '10px',
    borderTopRightRadius: '10px'
  }}>
    <img 
      src={data.icon} 
      alt="VPC" 
      style={{ width: '28px', height: '28px' }} 
      onError={(e) => { e.target.style.display = 'none'; }}
    />
    <span>{data.label}</span>
  </div>
));

export const SubnetContainerNode = memo(({ data }) => {
  const isPublic = data.isPublic;
  const color = isPublic ? '#00a4e4' : '#00c7b7';

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
      <img 
        src={data.icon} 
        alt="Subnet" 
        style={{ width: '22px', height: '22px' }} 
        onError={(e) => { e.target.style.display = 'none'; }}
      />
      <span>{data.label}</span>
    </div>
  );
});