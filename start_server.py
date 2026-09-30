"""
Quick server start script with proper configuration.
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def main():
    """Start the FastAPI server."""
    print("=" * 70)
    print("TulaPramaan - Starting Development Server")
    print("=" * 70)
    print()
    print("API Documentation:")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc:      http://localhost:8000/redoc")
    print()
    print("Health Check:")
    print("  http://localhost:8000/health")
    print()
    print("=" * 70)
    print()
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Import and run
    import uvicorn
    from config import get_settings
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()
