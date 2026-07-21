import React from 'react';
import { Handle, Position } from 'reactflow';

// Inline SVG Icons for self-contained, 404-free rendering
const SVG_ICONS = {
  ec2: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FF9900" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
      <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
      <line x1="6" y1="6" x2="6.01" y2="6"></line>
      <line x1="6" y1="18" x2="6.01" y2="18"></line>
    </svg>
  ),
  igw: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8C4FFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="2" y1="12" x2="22" y2="12"></line>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
    </svg>
  ),
  default: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#232F3E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2"></rect>
      <circle cx="9" cy="9" r="2"></circle>
      <path d="M21 15l-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>
    </svg>
  )
};

const STATE_COLORS = {
  running: '#1d8102',
  stopped: '#d13212',
  pending: '#eb5f07',
  terminated: '#545b64'
};

export const AwsResourceNode = ({ data }) => {
  const resourceType = data?.resourceType?.toLowerCase() || 'ec2';
  const icon = SVG_ICONS[resourceType] || SVG_ICONS.default;
  const stateColor = STATE_COLORS[data?.state?.toLowerCase()] || '#232f3e';

  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '8px',
      background: '#ffffff',
      border: '1px solid #d5dbdb',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
      minWidth: '200px'
    }}>
      <Handle type="target" position={Position.Top} />
      <div>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: '600', fontSize: '13px', color: '#232f3e' }}>
          {data.label}
        </div>
        {data.subtext && (
          <div style={{ fontSize: '11px', color: '#687078', marginTop: '2px' }}>
            {data.subtext}
          </div>
        )}
      </div>
      {data.state && (
        <span style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: stateColor,
          display: 'inline-block'
        }} title={`State: ${data.state}`} />
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export const VpcContainerNode = ({ data }) => (
  <div style={{
    padding: '16px',
    border: '2px dashed #879596',
    borderRadius: '8px',
    backgroundColor: 'rgba(135, 149, 150, 0.04)',
    width: '100%',
    height: '100%',
    boxSizing: 'border-box'
  }}>
    <Handle type="target" position={Position.Top} />
    <div style={{ fontWeight: 'bold', fontSize: '13px', color: '#879596', marginBottom: '8px' }}>
      VPC: {data.label} {data.cidr ? `(${data.cidr})` : ''}
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

export const SubnetContainerNode = ({ data }) => (
  <div style={{
    padding: '14px',
    border: `2px dashed ${data.isPublic ? '#007dbc' : '#116600'}`,
    borderRadius: '6px',
    backgroundColor: data.isPublic ? 'rgba(0, 125, 188, 0.04)' : 'rgba(17, 102, 0, 0.04)',
    width: '100%',
    height: '100%',
    boxSizing: 'border-box'
  }}>
    <div style={{ fontWeight: 'bold', fontSize: '12px', color: data.isPublic ? '#007dbc' : '#116600', marginBottom: '6px' }}>
      Subnet: {data.label} {data.cidr ? `(${data.cidr})` : ''}
    </div>
  </div>
);