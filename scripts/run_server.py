"""
Script to run the FastAPI server
"""
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config


def main():
    parser = argparse.ArgumentParser(description="Run Sentinel-Voice API server")
    parser.add_argument(
        "--host",
        type=str,
        default=config.server.host,
        help=f"Server host (default: {config.server.host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.server.port,
        help=f"Server port (default: {config.server.port})"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=config.server.debug,
        help="Enable auto-reload"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Sentinel-Voice API Server")
    print("=" * 60)
    print(f"Host:   {args.host}")
    print(f"Port:   {args.port}")
    print(f"Reload: {args.reload}")
    print("=" * 60)
    print("\nStarting server...")
    print("API docs will be available at:")
    print(f"  - Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  - ReDoc:      http://{args.host}:{args.port}/redoc")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)

    import uvicorn

    uvicorn.run(
        "src.server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
