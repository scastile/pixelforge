from typing import Any, Dict, List, BinaryIO
from PIL import Image
import io
from ..base import ImageTool, ToolMetadata, ToolCategory, ToolParameter, ToolResult


class CropTool(ImageTool):
    """Crop image with manual coordinates or smart detection."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            id="crop",
            name="Crop",
            description="Crop image with manual coordinates or smart detection",
            category=ToolCategory.BASIC_ESSENTIALS,
            parameters=[
                ToolParameter(
                    name="mode",
                    type="select",
                    description="Crop mode",
                    required=False,
                    default="manual",
                    options=["manual", "smart_attention", "smart_entropy", "face_detection"]
                ),
                ToolParameter(
                    name="left",
                    type="integer",
                    description="Left coordinate (pixels)",
                    required=False,
                    default=0,
                    min=0
                ),
                ToolParameter(
                    name="top",
                    type="integer",
                    description="Top coordinate (pixels)",
                    required=False,
                    default=0,
                    min=0
                ),
                ToolParameter(
                    name="width",
                    type="integer",
                    description="Crop width (pixels)",
                    required=False,
                    default=None,
                    min=1
                ),
                ToolParameter(
                    name="height",
                    type="integer",
                    description="Crop height (pixels)",
                    required=False,
                    default=None,
                    min=1
                ),
                ToolParameter(
                    name="unit",
                    type="select",
                    description="Unit for manual coordinates",
                    required=False,
                    default="pixels",
                    options=["pixels", "percent"]
                ),
                ToolParameter(
                    name="aspect_ratio",
                    type="string",
                    description="Aspect ratio (e.g., '16:9', '4:3', '1:1')",
                    required=False,
                    default=None
                )
            ],
            examples=[
                {
                    "description": "Manual crop at 100,100 with 300x300 size",
                    "parameters": {"left": 100, "top": 100, "width": 300, "height": 300}
                },
                {
                    "description": "Smart crop using attention detection",
                    "parameters": {"mode": "smart_attention", "width": 500, "height": 500}
                },
                {
                    "description": "Crop to 16:9 aspect ratio centered",
                    "parameters": {"aspect_ratio": "16:9", "mode": "smart_attention"}
                }
            ]
        )
    
    async def execute(
        self, 
        input_files: List[BinaryIO], 
        parameters: Dict[str, Any]
    ) -> ToolResult:
        import time
        start_time = time.time()
        
        params = self.validate_parameters(parameters)
        output_files = []
        
        for input_file in input_files:
            try:
                # Open image
                image = Image.open(input_file)
                original_format = image.format
                
                # Get crop coordinates based on mode
                if params["mode"] == "manual":
                    left, top, width, height = self._get_manual_coords(image, params)
                elif params["mode"] in ["smart_attention", "smart_entropy"]:
                    left, top, width, height = await self._get_smart_coords(image, params)
                elif params["mode"] == "face_detection":
                    left, top, width, height = await self._get_face_coords(image, params)
                else:
                    left, top, width, height = 0, 0, image.width, image.height
                
                # Validate coordinates
                left = max(0, min(left, image.width - 1))
                top = max(0, min(top, image.height - 1))
                width = min(width, image.width - left)
                height = min(height, image.height - top)
                
                if width <= 0 or height <= 0:
                    raise ValueError("Invalid crop dimensions")
                
                # Perform crop
                cropped_image = image.crop((left, top, left + width, top + height))
                
                # Save to bytes
                output_buffer = io.BytesIO()
                cropped_image.save(output_buffer, format=original_format or "PNG")
                output_buffer.seek(0)
                
                output_files.append({
                    "filename": f"cropped_{input_file.name if hasattr(input_file, 'name') else 'image'}",
                    "content": output_buffer.getvalue(),
                    "size": len(output_buffer.getvalue())
                })
                
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Failed to crop image: {str(e)}",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
        
        return ToolResult(
            success=True,
            output_files=output_files,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    def _get_manual_coords(self, image: Image.Image, params: Dict[str, Any]) -> tuple[int, int, int, int]:
        """Get coordinates for manual crop."""
        width = params.get("width") or image.width
        height = params.get("height") or image.height
        
        if params.get("unit") == "percent":
            left = int(image.width * (params.get("left", 0) / 100))
            top = int(image.height * (params.get("top", 0) / 100))
            width = int(image.width * (width / 100))
            height = int(image.height * (height / 100))
        else:
            left = params.get("left", 0)
            top = params.get("top", 0)
        
        return left, top, width, height
    
    async def _get_smart_coords(self, image: Image.Image, params: Dict[str, Any]) -> tuple[int, int, int, int]:
        """Get coordinates for smart crop (simplified version)."""
        # For now, return center crop
        # TODO: Implement actual attention/entropy detection
        width = params.get("width") or image.width // 2
        height = params.get("height") or image.height // 2
        
        left = (image.width - width) // 2
        top = (image.height - height) // 2
        
        return left, top, width, height
    
    async def _get_face_coords(self, image: Image.Image, params: Dict[str, Any]) -> tuple[int, int, int, int]:
        """Get coordinates for face detection crop."""
        # TODO: Implement face detection with MediaPipe
        # For now, return center crop
        width = params.get("width") or image.width // 2
        height = params.get("height") or image.height // 2
        
        left = (image.width - width) // 2
        top = (image.height - height) // 2
        
        return left, top, width, height