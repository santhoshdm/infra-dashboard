import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { AwsResourceNode, VpcContainerNode, SubnetContainerNode } from './AwsResourceNode';

const nodeTypes = {
  awsResource: AwsResourceNode,
  vpcContainer: VpcContainerNode,
  subnetContainer: SubnetContainerNode,
};

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTopology = useCallback(async () => {
    try {
      const response = await fetch('/api/topology');
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }
      const data = await response.json();
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch topology:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopology();
    const interval = setInterval(fetchTopology, 30000);
    return () => clearInterval(interval);
  }, [fetchTopology]);

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#f8f9fa' }}>
      {loading && (
        <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
          Loading AWS Topology...
        </div>
      )}
      {error && (
        <div style={{ padding: '20px', color: 'red', fontFamily: 'sans-serif' }}>
          Error fetching topology: {error}
        </div>
      )}
      {!loading && !error && (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#ccc" gap={16} />
          <Controls />
          <MiniMap />
        </ReactFlow>
      )}
    </div>
  );
}

export default App;