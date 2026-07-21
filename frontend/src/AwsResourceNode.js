import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const nodeStyles = {
  padding: '10px 15px',
  borderRadius: '8px',
  background: '#232f3e',
  color: '#ffffff',
  border: '2px solid #ff9900',
  fontWeight: 'bold',
  fontSize: '12px',
  textAlign: 'center'
};

const AwsResourceNode = ({ data }) => {
  return (
    <div style={nodeStyles}>
      <Handle type="target" position={Position.Left} />
      <div>⚡ {data.label}</div>
      <small style={{ color: '#ff9900', display: 'block', fontSize: '10px' }}>
        [{data.type.toUpperCase()}]
      </small>
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default memo(AwsResourceNode);