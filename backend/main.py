from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for React frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/topology")
def get_topology():
    # Returns the AWS resource nodes and connections
    return {
        "nodes": [
            {"id": "1", "type": "awsNode", "data": {"label": "API Gateway", "type": "gateway"}, "position": {"x": 100, "y": 150}},
            {"id": "2", "type": "awsNode", "data": {"label": "Lambda Function", "type": "compute"}, "position": {"x": 350, "y": 150}},
            {"id": "3", "type": "awsNode", "data": {"label": "DynamoDB Table", "type": "database"}, "position": {"x": 600, "y": 150}}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2", "animated": True},
            {"id": "e2-3", "source": "2", "target": "3", "animated": True}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)