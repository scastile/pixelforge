from typing import Any, Dict, List, BinaryIO
from PIL import Image
import io
from ..base import ImageTool, ToolMetadata, ToolCategory, ToolParameter, ToolResult


class FormatConvertTool(ImageTool):
    """Convert image between formats (JPEG, PNG, WebP, etc.)."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            id="format_convert",
            name="Format Convert",
            description="Convert image between formats (JPEG, PNG, WebP, TIFF, BMP, etc.)",
            category=ToolCategory.BASIC_ESSENTIALS,
            parameters=[
                ToolParameter(
                    name="format",
                    type="select",
                    description="Output format",
                    required=True,
                    default="png",
                    options=["jpeg", "png", "webp", "tiff", "bmp", "gif", "ico"]
                ),
                ToolParameter(
                    name="quality",
                    type="integer",
                    description="Quality (1-100) for JPEG/WebP",
                    required=False,
                    default=85,
                    min=1,
                    max=100
                ),
                ToolParameter(
                    name="lossless",
                    type="boolean",
                    description="WebP lossless compression",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="optimize",
                    type="boolean",
                    description="Optimize output (smaller file)",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="progressive",
                    type="boolean",
                    description="Progressive JPEG",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="transparency",
                    type="boolean",
                    description="Preserve transparency (PNG/WebP)",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="background_color",
                    type="string",
                    description="Background color for transparency (hex or name)",
                    required=False,
                    default="#ffffff"
                )
            ],
            examples=[
                {
                    "description": "Convert to high-quality JPEG",
                    "parameters": {
                        "format": "jpeg",
                        "quality": 90,
                        "optimize": True
                    }
                },
                {
                    "description": "Convert to WebP with transparency",
                    "parameters": {
                        "format": "webp",
                        "quality": 80,
                        "lossless": False,
                        "transparency": True
                    }
                },
                {
                    "description": "Convert to PNG with white background",
                    "parameters": {
                        "format": "png",
                        "transparency": False,
                        "background_color": "white"
                    }
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
        
        try:
            # Validate and convert parameters
            params = self.validate_parameters(parameters)
            format_type = params["format"].upper()
            
            if len(input_files) == 0:
                return ToolResult(
                    success=False,
                    error="No input file provided"
                )
            
            input_file = input_files[0]
            input_file.seek(0)
            input_data = input_file.read()
            
            # Open image
            image = Image.open(io.BytesIO(input_data))
            
            # Handle transparency/background if needed
            if (not params.get("transparency", True) and 
                image.mode in ('RGBA', 'LA', 'P') and
                params.get("background_color")):
                
                from PIL import ImageColor
                try:
                    bg_color = ImageColor.getcolor(params["background_color"], "RGB")
                except ValueError:
                    bg_color = (255, 255, 255)  # Default white
                
                # Create new image with background
                if image.mode == 'P' and 'transparency' in image.info:
                    # Handle palette with transparency
                    image = image.convert('RGBA')
                
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new("RGB", image.size, bg_color)
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])
                    else:  # LA mode
                        background.paste(image, mask=image.split()[-1])
                    image = background
            
            # Prepare output format and options
            output_format = format_type
            save_args = {}
            
            if format_type == "JPEG":
                save_args["quality"] = params.get("quality", 85)
                save_args["optimize"] = params.get("optimize", True)
                save_args["progressive"] = params.get("progressive", False)
                # Ensure RGB mode for JPEG
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                    
            elif format_type == "WEBP":
                save_args["quality"] = params.get("quality", 85)
                save_args["lossless"] = params.get("lossless", False)
                save_args["method"] = 6  # Default method
                
            elif format_type == "PNG":
                save_args["optimize"] = params.get("optimize", True)
                if params.get("compress_level"):
                    save_args["compress_level"] = params["compress_level"]
                    
            elif format_type == "TIFF":
                save_args["compression"] = "tiff_lzw"
                
            elif format_type == "GIF":
                # Handle palette for GIF
                if image.mode not in ('P', 'L'):
                    image = image.convert('P', palette=Image.ADAPTIVE, colors=256)
            
            # Save to bytes
            output_buffer = io.BytesIO()
            image.save(output_buffer, format=output_format, **save_args)
            output_data = output_buffer.getvalue()
            
            # Determine file extension
            ext_map = {
                "JPEG": "jpg",
                "PNG": "png", 
                "WEBP": "webp",
                "TIFF": "tiff",
                "BMP": "bmp",
                "GIF": "gif",
                "ICO": "ico"
            }
            ext = ext_map.get(output_format, output_format.lower())
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ToolResult(
                success=True,
                output_files=[{
                    "filename": f"converted.{ext}",
                    "content": output_data,
                    "size": len(output_data)
                }],
                metadata={
                    "original_format": image.format,
                    "output_format": output_format,
                    "output_size_bytes": len(output_data),
                    "dimensions": f"{image.width}x{image.height}"
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Format conversion failed: {str(e)}",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )