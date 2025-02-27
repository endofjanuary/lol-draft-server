import uvicorn
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run LoL Draft Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host IP address')
    parser.add_argument('--port', type=int, default=8000, help='Port number')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
