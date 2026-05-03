# PixelForge

Privacy-first, self-hosted image editor with 44 tools across 8 categories. Your images never leave your server.

## Features
- 11 implemented tools (Brightness, Contrast, Saturation, Sepia, Grayscale, Blur, Sharpen, Rotate, Flip, Resize, Background Removal)
- Apple-inspired design: Inter font, light/default theme, 12px radius, card-lift effects
- Undo support, dark mode toggle (manual, light default)
- Docker Compose stack (FastAPI backend + static frontend)
- CPU-friendly: no GPU required for core tools

## Tech Stack
- Backend: FastAPI, Pillow, Rembg
- Frontend: Vanilla HTML/JS, Inter font
- Deploy: Docker Compose (2 containers)

## Quick Start
1. Clone repo:
   ```bash
   git clone https://github.com/scastile/pixelforge.git
   cd pixelforge
   ```
2. Start services:
   ```bash
   docker compose up -d
   ```
3. Open editor:
   - Frontend: http://localhost:3201/editor.html
   - Backend API docs: http://localhost:8206/docs

## URLs (Default)
- Frontend: http://10.0.0.179:3201/editor.html
- Backend API: http://10.0.0.179:8206

## License
MIT

## TODO
- Implement remaining 33 tools (AI upscaling, face enhancement, etc.)
- Push to GitHub
- Add user-selectable AI model tiers
- Plugin architecture
