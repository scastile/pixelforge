from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, BinaryIO
from pydantic import BaseModel, Field
from enum import Enum
import asyncio


class ToolCategory(str, Enum):
    """Tool categories matching our 8-category system."""
    BASIC_ESSENTIALS = "basic_essentials"
    OPTIMIZATION = "optimization"
    ADJUSTMENTS = "adjustments"
    WATERMARK_OVERLAY = "watermark_overlay"
    UTILITIES = "utilities"
    LAYOUT_COMPOSITION = "layout_composition"
    FORMAT_CONVERSION = "format_conversion"
    AI_TOOLS = "ai_tools"


class ToolParameter(BaseModel):
    """Parameter definition for a tool."""
    name: str
    type: str  # "integer", "float", "string", "boolean", "file", "select"
    description: str
    required: bool = True
    default: Optional[Any] = None
    options: Optional[List[Any]] = None  # For select type
    min: Optional[float] = None
    max: Optional[float] = None


class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    id: str
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    version: str = "1.0.0"


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output_files: List[Dict[str, Any]] = Field(default_factory=list)  # [{filename: str, content: bytes, size: int}]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None


class ImageTool(ABC):
    """Base class for all image tools."""
    
    def __init__(self):
        self.metadata = self.get_metadata()
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        pass
    
    @abstractmethod
    async def execute(
        self, 
        input_files: List[BinaryIO], 
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute the tool on input files with given parameters."""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize parameters."""
        validated = {}
        for param in self.metadata.parameters:
            if param.name in parameters:
                value = parameters[param.name]
                # Type conversion and validation
                if param.type == "integer":
                    value = int(value)
                    if param.min is not None and value < param.min:
                        raise ValueError(f"{param.name} must be >= {param.min}")
                    if param.max is not None and value > param.max:
                        raise ValueError(f"{param.name} must be <= {param.max}")
                elif param.type == "float":
                    value = float(value)
                    if param.min is not None and value < param.min:
                        raise ValueError(f"{param.name} must be >= {param.min}")
                    if param.max is not None and value > param.max:
                        raise ValueError(f"{param.name} must be <= {param.max}")
                elif param.type == "boolean":
                    value = bool(value)
                elif param.type == "select" and param.options:
                    if value not in param.options:
                        raise ValueError(f"{param.name} must be one of {param.options}")
                
                validated[param.name] = value
            elif param.required:
                if param.default is not None:
                    validated[param.name] = param.default
                else:
                    raise ValueError(f"Required parameter '{param.name}' missing")
        
        return validated


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, ImageTool] = {}
    
    def register(self, tool: ImageTool) -> None:
        """Register a tool."""
        self._tools[tool.metadata.id] = tool
    
    def get(self, tool_id: str) -> Optional[ImageTool]:
        """Get a tool by ID."""
        return self._tools.get(tool_id)
    
    def list(self) -> List[ToolMetadata]:
        """List all available tools."""
        return [tool.metadata for tool in self._tools.values()]
    
    def list_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """List tools by category."""
        return [
            tool.metadata 
            for tool in self._tools.values() 
            if tool.metadata.category == category
        ]