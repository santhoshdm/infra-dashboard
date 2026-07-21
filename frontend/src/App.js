import React from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

// 1. Import node components
import { AwsResourceNode, VpcContainerNode, SubnetContainerNode } from './AwsResourceNode';

// 2. Register node types
const nodeTypes = {
  awsNode: AwsResourceNode,
  vpcContainer: VpcContainerNode,
  subnetContainer: SubnetContainerNode,
};

// 3. Define the App component explicitly
function App() {
  // Your state, useEffect, and ReactFlow layout logic here...

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

// 4. Export App as default
export default App;