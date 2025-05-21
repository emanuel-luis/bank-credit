import uvicorn
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="Bank Credit Application")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the application on",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the application on",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
        default=True
    )
    args = parser.parse_args()
    uvicorn.run("bank_credit.app.main:app", host=args.host, port=args.port, reload=args.reload)
