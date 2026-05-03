from typing import Any, Dict, List, BinaryIO
from PIL import Image
import io
from ..base import ImageTool, ToolMetadata, ToolCategory, ToolParameter, ToolResult


class ResizeTool(ImageTool):
    """Resize image with various fit modes and presets."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            id="resize",
            name="Resize",
            description="Resize image with width/height, fit modes, or social media presets",
            category=ToolCategory.BASIC_ESSENTIALS,
            parameters=[
                ToolParameter(
                    name="width",
                    type="integer",
                    description="Width in pixels (0 for auto)",
                    required=False,
                    default=0,
                    min=0,
                    max=10000
                ),
                ToolParameter(
                    name="height",
                    type="integer",
                    description="Height in pixels (0 for auto)",
                    required=False,
                    default=0,
                    min=0,
                    max=10000
                ),
                ToolParameter(
                    name="fit",
                    type="select",
                    description="How to fit image to dimensions",
                    required=False,
                    default="cover",
                    options=["cover", "contain", "fill", "inside", "outside"]
                ),
                ToolParameter(
                    name="preset",
                    type="select",
                    description="Social media preset (overrides width/height)",
                    required=False,
                    default=None,
                    options=[
                        None,
                        "instagram_square", "instagram_portrait", "instagram_landscape",
                        "twitter_post", "twitter_header", 
                        "facebook_post", "facebook_cover",
                        "linkedin_post", "linkedin_banner",
                        "youtube_thumbnail", "youtube_channel_art",
                        "pinterest_pin",
                        "tiktok_portrait", "tiktok_landscape"
                    ]
                ),
                ToolParameter(
                    name="percentage",
                    type="integer",
                    description="Percentage scaling (overrides width/height)",
                    required=False,
                    default=None,
                    min=1,
                    max=1000
                ),
                ToolParameter(
                    name="without_enlargement",
                    type="boolean",
                    description="Don't enlarge if image is smaller than target",
                    required=False,
                    default=False
                )
            ],
            examples=[
                {
                    "description": "Resize to Instagram square (1080x1080)",
                    "parameters": {"preset": "instagram_square"}
                },
                {
                    "description": "Resize to 50% of original size",
                    "parameters": {"percentage": 50}
                },
                {
                    "description": "Resize to 800px wide, maintain aspect ratio",
                    "parameters": {"width": 800, "height": 0, "fit": "contain"}
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
        
        # Validate parameters
        params = self.validate_parameters(parameters)
        
        # Apply preset if specified
        if params.get("preset"):
            width, height = self._get_preset_dimensions(params["preset"])
            params["width"] = width
            params["height"] = height
        
        # Apply percentage if specified
        if params.get("percentage"):
            # We'll handle this after opening the image
            pass
        
        output_files = []
        
        for input_file in input_files:
            try:
                # Open image
                image = Image.open(input_file)
                original_format = image.format
                
                # Calculate target dimensions
                if params.get("percentage"):
                    # Percentage scaling
                    scale = params["percentage"] / 100.0
                    target_width = int(image.width * scale)
                    target_height = int(image.height * scale)
                else:
                    target_width = params.get("width", 0)
                    target_height = params.get("height", 0)
                    
                    # If only one dimension is specified, calculate the other
                    if target_width and not target_height:
                        target_height = int(image.height * (target_width / image.width))
                    elif target_height and not target_width:
                        target_width = int(image.width * (target_height / image.height))
                    elif not target_width and not target_height:
                        # No dimensions specified, use original
                        target_width = image.width
                        target_height = image.height
                
                # Apply without_enlargement constraint
                if params.get("without_enlargement", False):
                    if target_width > image.width:
                        target_width = image.width
                    if target_height > image.height:
                        target_height = image.height
                
                # Apply fit mode
                if params.get("fit") == "contain":
                    # Resize to fit within dimensions, maintain aspect ratio
                    ratio = min(target_width / image.width, target_height / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                elif params.get("fit") == "cover":
                    # Resize to cover dimensions, maintain aspect ratio, crop if needed
                    ratio = max(target_width / image.width, target_height / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    # Image will need cropping (not implemented in this basic version)
                else:
                    # "fill" mode - stretch to exact dimensions
                    new_width = target_width
                    new_height = target_height
                
                # Resize image
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save to bytes
                output_buffer = io.BytesIO()
                resized_image.save(output_buffer, format=original_format or "PNG")
                output_buffer.seek(0)
                
                output_files.append({
                    "filename": f"resized_{input_file.name if hasattr(input_file, 'name') else 'image'}",
                    "content": output_buffer.getvalue(),
                    "size": len(output_buffer.getvalue())
                })
                
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Failed to resize image: {str(e)}",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
        
        return ToolResult(
            success=True,
            output_files=output_files,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    def _get_preset_dimensions(self, preset: str) -> tuple[int, int]:
        """Get dimensions for social media presets."""
        presets = {
            "instagram_square": (1080, 1080),
            "instagram_portrait": (1080, 1350),
            "instagram_landscape": (1080, 566),
            "twitter_post": (1200, 675),
            "twitter_header": (1500, 500),
            "facebook_post": (1200, 630),
            "facebook_cover": (820, 312),
            "linkedin_post": (1200, 627),
            "linkedin_banner": (1584, 396),
            "youtube_thumbnail": (1280, 720),
            "youtube_channel_art": (2560, 1440),
            "pinterest_pin": (1000, 1500),
            "tiktok_portrait": (1080, 1920),
            "tiktok_landscape": (1920, 1080),
        }
        return presets.get(preset, (1080, 1080))