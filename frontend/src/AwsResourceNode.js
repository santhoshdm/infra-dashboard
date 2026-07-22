import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const statusColors = {
  running: '#10b981',
  healthy: '#10b981',
  stopped: '#ef4444',
  degraded: '#f59e0b'
};

// Modern, sleek AWS Resource Card
export const AwsResourceNode = memo(({ data }) => {
  const statusColor = statusColors[data?.status?.toLowerCase()] || '#10b981';

  return (
    <div style={{
      padding: '12px 16px',
      borderRadius: '10px',
      background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
      border: `1px solid rgba(255, 255, 255, 0.1)`,
      borderLeft: `4px solid ${statusColor}`,
      color: '#f8fafc',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      minWidth: '230px',
      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.3)',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: statusColor, width: 8, height: 8 }} />
      
      <div style={{
        background: 'rgba(255, 255, 255, 0.05)',
        padding: '6px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <img 
          src={data.icon} 
          alt="" 
          style={{ width: '28px', height: '28px', objectFit: 'contain' }} 
          onError={(e) => { e.target.style.display = 'none'; }} 
        />
      </div>

      <div style={{ flexGrow: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '13px', fontWeight: '600', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#f8fafc', letterSpacing: '-0.01em' }}>
          {data.label}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
          <span style={{ fontSize: '11px', color: statusColor, fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: statusColor }}></span>
            {data.status || 'ACTIVE'}
          </span>
          <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '500' }}>
            {data.metric || ''}
          </span>
        </div>
      </div>

      <Handle type="source" position={Position.Right} style={{ background: statusColor, width: 8, height: 8 }} />
    </div>
  );
});

// Sleek Glassmorphism VPC Box Header
export const VpcContainerNode = memo(({ data }) => (
  <div style={{
    padding: '10px 16px',
    color: '#ff9900',
    fontWeight: '700',
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    background: 'rgba(30, 41, 59, 0.8)',
    backdropFilter: 'blur(8px)',
    borderBottom: '1px solid rgba(255, 153, 0, 0.2)',
    borderTopLeftRadius: '10px',
    borderTopRightRadius: '10px',
    fontFamily: 'Inter, system-ui, sans-serif'
  }}>
    <img src={data.icon} alt="" style={{ width: '22px', height: '22px' }} onError={(e) => { e.target.style.display = 'none'; }} />
    <span>{data.label}</span>
  </div>
));

// Subnet Header & Empty State Handling
export const SubnetContainerNode = memo(({ data }) => {
  const isPublic = data.isPublic;
  const accentColor = isPublic ? '#38bdf8' : '#34d399';

  return (
    <div style={{
      padding: '8px 12px',
      color: accentColor,
      fontWeight: '600',
      fontSize: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      background: 'rgba(15, 23, 42, 0.6)',
      borderBottom: `1px solid ${isPublic ? 'rgba(56, 189, 248, 0.2)' : 'rgba(52, 211, 153, 0.2)'}`,
      borderTopLeftRadius: '6px',
      borderTopRightRadius: '6px',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <img src={data.icon} alt="" style={{ width: '18px', height: '18px' }} onError={(e) => { e.target.style.display = 'none'; }} />
      <span>{data.label}</span>
    </div>
  );
});