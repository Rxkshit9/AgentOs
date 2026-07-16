import os
import platform
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(
    title="AgentOS Local MCP Server",
    description="A local Model Context Protocol (MCP) server hosting utility tools.",
    version="1.0.0"
)

class MCPCallPayload(BaseModel):
    server: str
    method: str
    params: Dict[str, Any]

@app.get("/health")
def health():
    return {"status": "healthy", "server": "agentos-mcp"}

@app.get("/tools")
def list_mcp_tools():
    """Lists all available tools hosted by this local MCP server."""
    return {
        "tools": [
            {
                "name": "calculator",
                "description": "Performs basic mathematical operations.",
                "args": {
                    "a": "float",
                    "b": "float",
                    "operation": "add | subtract | multiply | divide"
                }
            },
            {
                "name": "system_info",
                "description": "Retrieves local system OS, machine, and Python versions.",
                "args": {}
            },
            {
                "name": "file_reader",
                "description": "Reads text content of files in the workspace (safely).",
                "args": {
                    "filepath": "string"
                }
            }
        ]
    }

@app.post("/call")
def call_mcp_tool(payload: MCPCallPayload):
    """Router to execute local tools based on method names."""
    method = payload.method
    params = payload.params
    
    if method == "calculator":
        try:
            a = float(params.get("a", 0))
            b = float(params.get("b", 0))
            op = params.get("operation", "add")
            
            if op == "add":
                res = a + b
            elif op == "subtract":
                res = a - b
            elif op == "multiply":
                res = a * b
            elif op == "divide":
                if b == 0:
                    raise HTTPException(status_code=400, detail="Division by zero")
                res = a / b
            else:
                raise HTTPException(status_code=400, detail=f"Unknown operation: {op}")
            return {"status": "success", "result": res}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    elif method == "system_info":
        return {
            "status": "success",
            "result": {
                "os": platform.system(),
                "os_release": platform.release(),
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            }
        }
        
    elif method == "file_reader":
        filepath = params.get("filepath")
        if not filepath:
            raise HTTPException(status_code=400, detail="filepath is required")
            
        # Ensure path is within workspace for safety
        normalized_path = os.path.abspath(filepath)
        workspace_root = os.path.abspath(os.getcwd())
        
        # Simple safety check: file must be under current workspace directory
        if not normalized_path.startswith(workspace_root):
            raise HTTPException(status_code=403, detail="Access denied: Path is outside workspace.")
            
        if not os.path.exists(normalized_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        try:
            with open(normalized_path, "r", encoding="utf-8") as f:
                content = f.read(5000)  # Read up to 5k chars for safety
            return {"status": "success", "result": content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    else:
        raise HTTPException(status_code=404, detail=f"Tool/method '{method}' not found on this MCP server.")

def main():
    uvicorn.run("backend.mcp_server:app", host="0.0.0.0", port=8500, reload=True)

if __name__ == "__main__":
    main()
