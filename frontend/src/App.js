import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

import { AwsResourceNode, VpcContainerNode, SubnetContainerNode } from './AwsResourceNode';

const nodeTypes = {
  awsNode: AwsResourceNode,
  vpcContainer: VpcContainerNode,
  subnetContainer: SubnetContainerNode,
};

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [environment, setEnvironment] = useState('all');
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchTopology = useCallback(async (selectedEnv, isInitial = false) => {
    try {
      const url = selectedEnv && selectedEnv !== 'all' 
        ? `/api/topology?env=${selectedEnv}` 
        : '/api/topology';

      const response = await fetch(url);
      if (!response.ok) throw new Error('API fetch failed');
      const data = await response.json();

      setNodes(data.nodes || []);
      setEdges(data.edges || []);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Failed to fetch topology:", err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopology(environment, true);

    const interval = setInterval(() => {
      fetchTopology(environment, false);
    }, 10000);

    return () => clearInterval(interval);
  }, [environment, fetchTopology]);

  if (loading) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: '#0f172a', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
        <h2>Loading AWS Topology Dashboard...</h2>
      </div>
    );
  }

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0b0f19', position: 'relative' }}>
      
      {/* Top Header Control Bar */}
      <div style={{
        position: 'absolute',
        top: 15,
        left: 20,
        right: 20,
        zIndex: 10,
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        pointerEvents: 'none'
      }}>
        {/* Environment Selector Dropdown */}
        <div style={{ pointerEvents: 'auto', background: '#1e293b', padding: '8px 16px', borderRadius: '8px', border: '1px solid #334155', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 'bold' }}>Environment Tag:</label>
          <select 
            value={environment} 
            onChange={(e) => setEnvironment(e.target.value)}
            style={{
              background: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #475569',
              padding: '6px 12px',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Environments</option>
            <option value="dev">dev</option>
            <option value="Production">Production</option>
            <option value="staging">staging</option>
          </select>
        </div>

        {/* Live Status Indicator */}
        <div style={{
          background: '#1e293b',
          padding: '8px 14px',
          borderRadius: '20px',
          border: '1px solid #334155',
          color: '#94a3b8',
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
          Polling Active {lastUpdated && `(Updated ${lastUpdated})`}
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#1e293b" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export default App;