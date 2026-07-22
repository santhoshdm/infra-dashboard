import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
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
  const [environment, setEnvironment] = useState('Production');
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

  // Key metrics calculation
  const ec2Count = nodes.filter(n => n.type === 'awsNode' && n.data?.service === 'ec2').length;
  const vpcCount = nodes.filter(n => n.type === 'vpcContainer').length;
  const subnetCount = nodes.filter(n => n.type === 'subnetContainer').length;

  if (loading) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: '#090d16', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, sans-serif' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid rgba(56, 189, 248, 0.2)', borderTop: '3px solid #38bdf8', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }}></div>
          <p style={{ fontWeight: '500', letterSpacing: '0.02em' }}>Initializing Live AWS Topology...</p>
        </div>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#090d16', position: 'relative', fontFamily: 'Inter, sans-serif' }}>
      
      {/* Top Floating Control Bar */}
      <div style={{
        position: 'absolute',
        top: 20,
        left: 24,
        right: 24,
        zIndex: 10,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        pointerEvents: 'none'
      }}>
        {/* Left Control Group */}
        <div style={{ pointerEvents: 'auto', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(12px)',
            padding: '6px 14px',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 10px 25px -5px rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span style={{ color: '#94a3b8', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Environment
            </span>
            <select 
              value={environment} 
              onChange={(e) => setEnvironment(e.target.value)}
              style={{
                background: '#1e293b',
                color: '#f8fafc',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                outline: 'none'
              }}
            >
              <option value="all">All Environments</option>
              <option value="Production">Production</option>
              <option value="dev">dev</option>
              <option value="staging">staging</option>
            </select>
          </div>

          {/* Infrastructure Metrics Badges */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(12px)',
            padding: '8px 16px',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            gap: '16px',
            fontSize: '12px',
            color: '#94a3b8'
          }}>
            <span><strong style={{ color: '#ff9900' }}>{vpcCount}</strong> VPCs</span>
            <span style={{ color: 'rgba(255,255,255,0.2)' }}>|</span>
            <span><strong style={{ color: '#38bdf8' }}>{subnetCount}</strong> Subnets</span>
            <span style={{ color: 'rgba(255,255,255,0.2)' }}>|</span>
            <span><strong style={{ color: '#10b981' }}>{ec2Count}</strong> Workloads</span>
          </div>
        </div>

        {/* Right Live Polling Badge */}
        <div style={{
          pointerEvents: 'auto',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(12px)',
          padding: '8px 16px',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#94a3b8',
          fontSize: '12px',
          fontWeight: '500',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 10px #10b981'
          }}></span>
          <span>Live Polling {lastUpdated && `• ${lastUpdated}`}</span>
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background color="#1e293b" gap={24} size={1} />
        <Controls style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fill: '#fff' }} />
        <MiniMap 
          nodeColor={(node) => {
            if (node.type === 'vpcContainer') return '#ff9900';
            if (node.type === 'subnetContainer') return '#38bdf8';
            return '#10b981';
          }}
          maskColor="rgba(9, 13, 22, 0.7)"
          style={{ background: '#0f172a', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}
        />
      </ReactFlow>
    </div>
  );
}

export default App;