from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path

# Try to import rembg for background removal
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("Warning: rembg not installed. Background removal will not be available.")

# Try to import cv2 for upscaling
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not installed. Advanced upscaling will not be available.")

UPSCALING_AVAILABLE = CV2_AVAILABLE
FACE_ENHANCEMENT_AVAILABLE = False  # Will enable if gfpgan installs

app = FastAPI(title="PixelForge API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("/app/data") if os.path.exists("/app/data") else Path("./data")
UPLOAD_DIR = DATA_DIR / "uploads"
RESULT_DIR = DATA_DIR / "results"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

class Category(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    tools: List[str]

CATEGORIES = [
    {
        "id": "basic",
        "name": "Basic Adjustments",
        "icon": "🎨",
        "description": "Essential image adjustments: brightness, contrast, saturation, and more",
        "tools": ["Brightness", "Contrast", "Saturation", "Hue", "Temperature", "Tint", "Exposure", "Highlights/Shadows"]
    },
    {
        "id": "filters",
        "name": "Filters & Effects",
        "icon": "✨",
        "description": "Apply artistic filters and creative effects to transform your images",
        "tools": ["Vintage", "Sepia", "Grayscale", "Blur", "Sharpen", "Emboss", "Edge Detection", "Posterize"]
    },
    {
        "id": "transform",
        "name": "Transform & Resize",
        "icon": "📐",
        "description": "Resize, crop, rotate, and transform images with precision",
        "tools": ["Resize", "Crop", "Rotate", "Flip", "Mirror", "Aspect Ratio", "Scale", "Thumbnail"]
    },
    {
        "id": "ai",
        "name": "AI Tools",
        "icon": "🤖",
        "description": "Advanced AI-powered tools with model selection for optimal results",
        "tools": ["Background Removal", "Upscaling", "Face Enhancement", "Denoise", "Colorize", "Inpainting", "Super Resolution", "Style Transfer"]
    },
    {
        "id": "color",
        "name": "Color & Tone",
        "icon": "🌈",
        "description": "Advanced color correction and tone adjustments",
        "tools": ["White Balance", "Levels", "Curves", "Color Balance", "Vibrance", "Black & White", "Duotone", "Gradient Map"]
    },
    {
        "id": "text",
        "name": "Text & Watermark",
        "icon": "🔤",
        "description": "Add text overlays, watermarks, and annotations",
        "tools": ["Add Text", "Watermark", "Caption", "Exif Caption", "Text Logo", "Annotated Arrow", "Speech Bubble", "Copyright"]
    },
    {
        "id": "layout",
        "name": "Layout & Composition",
        "icon": "📄",
        "description": "Combine images, create collages, and manage layouts",
        "tools": ["Collage", "Merge", "Border", "Padding", "Instagram Frame", "Passport Photo", "ID Card", "Polaroid"]
    },
    {
        "id": "export",
        "name": "Export & Share",
        "icon": "📤",
        "description": "Save, convert, and share your processed images",
        "tools": ["Format Convert", "Quality Adjust", "Metadata Strip", "Batch Compress", "WebP Optimize", "HEIC Convert", "PDF Export", "Share Link"]
    }
]

def adjust_brightness(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def adjust_contrast(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def adjust_saturation(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def adjust_sharpness(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def apply_sepia(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    width, height = img.size
    pixels = img.load()
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
    return img

def apply_grayscale(img):
    return ImageOps.grayscale(img).convert('RGB')

def apply_blur(img, radius=2.0):
    return img.filter(ImageFilter.GaussianBlur(radius=radius))

def apply_sharpen(img):
    return img.filter(ImageFilter.SHARPEN)

def rotate_image(img, degrees):
    return img.rotate(degrees, expand=True)

def flip_horizontal(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)

def flip_vertical(img):
    return img.transpose(Image.FLIP_TOP_BOTTOM)

def resize_image(img, width, height):
    return img.resize((width, height), Image.Resampling.LANCZOS)

def remove_background(img):
    if not REMBG_AVAILABLE:
        raise Exception("rembg not installed. Install with: pip install rembg")
    # Convert to bytes for rembg
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Remove background
    result = remove(img_byte_arr)
    
    # Convert back to PIL Image
    result_img = Image.open(io.BytesIO(result))
    
    # Convert RGBA to RGB (JPEG doesn't support alpha)
    if result_img.mode == 'RGBA':
        # Create white background
        background = Image.new('RGB', result_img.size, (255, 255, 255))
        background.paste(result_img, mask=result_img.split()[3])  # Use alpha channel as mask
        return background
    return result_img

def upscale_image(img, scale_factor=2):
    """Upscale image using cv2 dnn_superres if available, else PIL Lanczos"""
    if CV2_AVAILABLE:
        try:
            # Try to use cv2's dnn_superres for proper AI upscaling
            # For now, use cv2's resize with INTER_CUBIC which is decent
            width, height = img.size
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            upscaled = cv2.resize(cv_img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            return Image.fromarray(cv2.cvtColor(upscaled, cv2.COLOR_BGR2RGB))
        except Exception as e:
            print(f"cv2 upscaling failed: {e}, falling back to PIL")
    
    # Fallback to PIL Lanczos
    width, height = img.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

def enhance_face(img):
    """Face enhancement - placeholder using PIL enhancements"""
    # Basic enhancement: sharpen + contrast + slight brightness
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    return img

TOOL_FUNCTIONS = {
    "Brightness": lambda img, **kwargs: adjust_brightness(img, float(kwargs.get('factor', 1.2))),
    "Contrast": lambda img, **kwargs: adjust_contrast(img, float(kwargs.get('factor', 1.2))),
    "Saturation": lambda img, **kwargs: adjust_saturation(img, float(kwargs.get('factor', 1.5))),
    "Sharpen": lambda img, **kwargs: adjust_sharpness(img, float(kwargs.get('factor', 1.5))),
    "Sepia": lambda img, **kwargs: apply_sepia(img),
    "Grayscale": lambda img, **kwargs: apply_grayscale(img),
    "Blur": lambda img, **kwargs: apply_blur(img, float(kwargs.get('radius', 2.0))),
    "Rotate": lambda img, **kwargs: rotate_image(img, float(kwargs.get('degrees', 90))),
    "Flip": lambda img, **kwargs: flip_horizontal(img) if kwargs.get('direction') == 'horizontal' else flip_vertical(img),
    "Resize": lambda img, **kwargs: resize_image(img, int(kwargs.get('width', 800)), int(kwargs.get('height', 600))),
    "Background Removal": lambda img, **kwargs: remove_background(img),
    "Upscaling": lambda img, **kwargs: upscale_image(img, float(kwargs.get('scale', 2))),
    "Face Enhancement": lambda img, **kwargs: enhance_face(img),
}

@app.get("/")
async def root():
    return {
        "name": "PixelForge API",
        "version": "0.2.0",
        "description": "Privacy-first image manipulation API with actual processing",
        "categories": len(CATEGORIES),
        "tools": sum(len(c["tools"]) for c in CATEGORIES)
    }

@app.get("/api/categories")
async def get_categories():
    return CATEGORIES

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_ext = Path(file.filename).suffix.lower() or '.jpg'
        file_path = UPLOAD_DIR / f"{Path(file.filename).stem}_{os.urandom(4).hex()}{file_ext}"
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        try:
            img = Image.open(file_path)
            width, height = img.size
            img.close()
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"Invalid image: {str(e)}"})
        
        return {
            "filename": file_path.name,
            "original_name": file.filename,
            "path": str(file_path),
            "size": {"width": width, "height": height},
            "status": "uploaded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/process/{tool_id}")
async def process_image(
    tool_id: str,
    file: UploadFile = File(...),
    factor: Optional[float] = Query(1.0),
    degrees: Optional[float] = Query(90),
    width: Optional[int] = Query(None),
    height: Optional[int] = Query(None),
    radius: Optional[float] = Query(2.0),
    direction: Optional[str] = Query('horizontal'),
    scale: Optional[float] = Query(2.0)
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        kwargs = {}
        if tool_id in ["Brightness", "Contrast", "Saturation", "Sharpen"]:
            kwargs = {'factor': factor}
        elif tool_id == "Blur":
            kwargs = {'radius': radius}
        elif tool_id == "Rotate":
            kwargs = {'degrees': degrees}
        elif tool_id == "Flip":
            kwargs = {'direction': direction}
        elif tool_id == "Resize" and width and height:
            kwargs = {'width': width, 'height': height}
        elif tool_id == "Upscaling":
            kwargs = {'scale_factor': scale}
        elif tool_id == "Face Enhancement":
            kwargs = {}
        
        if tool_id in TOOL_FUNCTIONS:
            img = TOOL_FUNCTIONS[tool_id](img, **kwargs)
        else:
            raise HTTPException(status_code=400, detail=f"Tool '{tool_id}' not implemented yet")
        
        result_filename = f"{tool_id.lower()}_{Path(file.filename).stem}_{os.urandom(4).hex()}.jpg"
        result_path = RESULT_DIR / result_filename
        img.save(result_path, "JPEG", quality=95)
        img.close()
        
        return {
            "tool": tool_id,
            "status": "completed",
            "result_url": f"/api/result/{result_filename}",
            "filename": result_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/api/result/{filename}")
async def get_result(filename: str):
    file_path = RESULT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")
    return FileResponse(str(file_path), media_type="image/jpeg")

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8206))
    uvicorn.run(app, host="0.0.0.0", port=port)
