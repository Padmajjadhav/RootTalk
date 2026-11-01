import uvicorn
import argparse
import os

if __name__ == "__main__":
    port_env = os.getenv("PORT")
    default_port = int(port_env) if port_env and port_env.isdigit() else 8000
    host_env = os.getenv("HOST")
    default_host = host_env if host_env else ("0.0.0.0" if port_env else "127.0.0.1")

    parser = argparse.ArgumentParser(description="Run the Regional Language Preservation Backend API server.")
    parser.add_argument("--host", type=str, default=default_host, help=f"Host IP address to bind (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to listen on (default: {default_port})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  [*] DIGITAL PRESERVATION OF REGIONAL LANGUAGES & DIALECTS BACKEND")
    print("=" * 70)
    print(f"  * Server URL:       http://{args.host}:{args.port}")
    print(f"  * Swagger Docs:     http://{args.host}:{args.port}/docs")
    print(f"  * ReDoc Docs:       http://{args.host}:{args.port}/redoc")
    print(f"  * OpenAPI JSON:     http://{args.host}:{args.port}/api/v1/openapi.json")
    print(f"  * WebSocket Stream: ws://{args.host}:{args.port}/api/v1/ws/activity")
    print("=" * 70)
    
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
