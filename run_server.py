import uvicorn
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Regional Language Preservation Backend API server.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP address to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  🎙️ DIGITAL PRESERVATION OF REGIONAL LANGUAGES & DIALECTS BACKEND")
    print("=" * 70)
    print(f"  ► Server URL:       http://{args.host}:{args.port}")
    print(f"  ► Swagger Docs:     http://{args.host}:{args.port}/docs")
    print(f"  ► ReDoc Docs:       http://{args.host}:{args.port}/redoc")
    print(f"  ► OpenAPI JSON:     http://{args.host}:{args.port}/api/v1/openapi.json")
    print(f"  ► WebSocket Stream: ws://{args.host}:{args.port}/api/v1/ws/activity")
    print("=" * 70)
    
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
