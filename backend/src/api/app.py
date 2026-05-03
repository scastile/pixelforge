from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import io
import uuid

from ..core.config import settings
from ..core.tools.base import ToolRegistry, ToolResult, ToolCategory
from ..core.tools.basic.resize import ResizeTool
from ..core.tools.basic.crop import CropTool
from ..core.tools.basic.format_convert import FormatConvertTool


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Self-hosted image manipulation suite with 40+ tools and local AI processing",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create tool registry and register tools
    tool_registry = ToolRegistry()
    tool_registry.register(ResizeTool())
    tool_registry.register(CropTool())
    tool_registry.register(FormatConvertTool())
    
    # Store registry in app state
    app.state.tool_registry = tool_registry
    
    # API router
    api_router = APIRouter(prefix="/api/v1")
    
    @api_router.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "service": settings.app_name
        }
    
    @api_router.get("/tools")
    async def list_tools():
        """List all available tools."""
        registry: ToolRegistry = app.state.tool_registry
        return registry.list()
    
    @api_router.get("/tools/{category}")
    async def list_tools_by_category(category: str):
        """List tools by category."""
        registry: ToolRegistry = app.state.tool_registry
        try:
            # Try to convert string to ToolCategory enum
            category_enum = ToolCategory(category)
            return registry.list_by_category(category_enum)
        except ValueError:
            # Return empty list if category not found
            return []
    
    @api_router.get("/tools/{tool_id}/info")
    async def get_tool_info(tool_id: str):
        """Get detailed information about a specific tool."""
        registry: ToolRegistry = app.state.tool_registry
        tool = registry.get(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
        return tool.metadata
    
    @api_router.post("/tools/{tool_id}")
    async def execute_tool(
        tool_id: str,
        file: UploadFile = File(...),
        params: Optional[str] = None  # JSON string of parameters
    ):
        """Execute a tool on a single file."""
        registry: ToolRegistry = app.state.tool_registry
        tool = registry.get(tool_id)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
        
        # Parse parameters
        parameters = {}
        if params:
            import json
            try:
                parameters = json.loads(params)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON parameters")
        
        # Read file content
        content = await file.read()
        
        # Execute tool
        try:
            result: ToolResult = await tool.execute(
                input_files=[io.BytesIO(content)],
                parameters=parameters
            )
            
            if not result.success:
                raise HTTPException(status_code=400, detail=result.error)
            
            # Return the processed file
            if result.output_files:
                output_file = result.output_files[0]
                # Detect media type from filename
                filename = output_file["filename"]
                if filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    media_type = "image/jpeg"
                elif filename.endswith(".png"):
                    media_type = "image/png"
                elif filename.endswith(".webp"):
                    media_type = "image/webp"
                elif filename.endswith(".gif"):
                    media_type = "image/gif"
                elif filename.endswith(".tiff"):
                    media_type = "image/tiff"
                elif filename.endswith(".bmp"):
                    media_type = "image/bmp"
                else:
                    media_type = "application/octet-stream"
                
                return StreamingResponse(
                    io.BytesIO(output_file["content"]),
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "X-Processing-Time": str(result.processing_time_ms)
                    }
                )
            else:
                return JSONResponse(
                    content={"message": "Tool executed successfully but no output file generated"},
                    status_code=200
                )
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @api_router.post("/tools/{tool_id}/batch")
    async def execute_tool_batch(
        tool_id: str,
        files: List[UploadFile] = File(...),
        # TODO: Add JSON parameters
    ):
        """Execute a tool on multiple files (returns ZIP)."""
        # TODO: Implement batch processing with ZIP archive
        raise HTTPException(status_code=501, detail="Batch processing not yet implemented")
    
    # LLM-friendly documentation endpoints (inspired by SnapOtter)
    @api_router.get("/llms.txt")
    async def get_llm_summary():
        """LLM-friendly API summary."""
        registry: ToolRegistry = app.state.tool_registry
        tools = registry.list()
        
        summary = f"""PixelForge API v{settings.app_version}

Available tools ({len(tools)} total):
"""
        for tool in tools:
            summary += f"- {tool.id}: {tool.description} (category: {tool.category})\n"
        
        summary += f"""
API endpoints:
- POST /api/v1/tools/{{tool_id}} - Process single image
- POST /api/v1/tools/{{tool_id}}/batch - Process multiple images (returns ZIP)
- GET /api/v1/tools - List all tools
- GET /api/v1/tools/{{tool_id}}/info - Get tool details

Example curl:
curl -X POST http://localhost:{settings.port}/api/v1/tools/resize \\
  -F "file=@input.jpg" \\
  -F 'parameters={{"width":800,"height":600}}'

Default port: {settings.port}
"""
        return summary
    
    @api_router.get("/llms-full.txt")
    async def get_llm_full_docs():
        """Complete LLM-friendly documentation."""
        registry: ToolRegistry = app.state.tool_registry
        tools = registry.list()
        
        docs = f"""PixelForge API - Complete Documentation
Version: {settings.app_version}

ALL TOOLS:
"""
        for tool in tools:
            docs += f"""
{tool.id.upper()}
Name: {tool.name}
Description: {tool.description}
Category: {tool.category}
Parameters:
"""
            for param in tool.parameters:
                docs += f"  - {param.name} ({param.type}): {param.description}"
                if param.required:
                    docs += " [REQUIRED]"
                if param.default is not None:
                    docs += f" [default: {param.default}]"
                docs += "\n"
            
            if tool.examples:
                docs += "Examples:\n"
                for example in tool.examples:
                    docs += f"  - {example['description']}\n"
                    docs += f"    Parameters: {example['parameters']}\n"
        
        docs += f"""
API ENDPOINTS:
- GET /api/v1/health - Health check
- GET /api/v1/tools - List all tools
- GET /api/v1/tools/{{category}} - List tools by category
- GET /api/v1/tools/{{tool_id}}/info - Get tool details
- POST /api/v1/tools/{{tool_id}} - Execute tool on single file
- POST /api/v1/tools/{{tool_id}}/batch - Execute tool on multiple files (ZIP)
- GET /api/docs - Interactive API documentation
- GET /api/redoc - Alternative API documentation
- GET /llms.txt - This summary
- GET /llms-full.txt - This complete documentation

AUTHENTICATION:
Currently: None (development mode)
Future: API keys, JWT tokens

FILE UPLOADS:
Max size: {settings.max_upload_size // (1024*1024)}MB
Formats: JPEG, PNG, WebP, GIF, TIFF, etc.

BATCH PROCESSING:
Returns ZIP archive with processed files.
"""
        return docs
    
    # Include API router
    app.include_router(api_router)
    
    return app