import React, { useState, useEffect } from 'react';
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
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const response = await fetch('/api/topology');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
        setError(null);
      } catch (err) {
        console.error("Topology fetch failed:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTopology();
    const interval = setInterval(fetchTopology, 30000); // 30s polling
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: '#0f172a', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <h2>Loading AWS Topology Canvas...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: '#0f172a', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
        <h2>Error loading topology</h2>
        <p style={{ color: '#94a3b8' }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0f172a' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#334155" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export default App;