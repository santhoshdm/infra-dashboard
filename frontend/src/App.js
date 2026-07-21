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
  const [lastUpdated, setLastUpdated] = useState(null);

  // Poll API for topology updates silently in background
  const fetchTopology = useCallback(async (isInitial = false) => {
    try {
      const response = await fetch('/api/topology');
      if (!response.ok) throw new Error('API fetch failed');
      const data = await response.json();

      if (data.nodes) setNodes(data.nodes);
      if (data.edges) setEdges(data.edges);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Failed to poll topology:", err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopology(true);

    // Live refresh every 10 seconds (preserves session without app restart)
    const interval = setInterval(() => {
      fetchTopology(false);
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchTopology]);

  if (loading) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: '#0f172a', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
        <h2>Fetching AWS Infrastructure Topology...</h2>
      </div>
    );
  }

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0b0f19', position: 'relative' }}>
      
      {/* Live Polling Status Indicator */}
      <div style={{
        position: 'absolute',
        top: 15,
        right: 20,
        zIndex: 10,
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
        Live Polling Active {lastUpdated && `(Updated ${lastUpdated})`}
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background color="#1e293b" gap={20} />
        <Controls style={{ button: { background: '#1e293b', color: '#fff', border: '1px solid #334155' } }} />
      </ReactFlow>
    </div>
  );
}

export default App;