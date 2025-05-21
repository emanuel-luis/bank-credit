import uvicorn
from argparse import ArgumentParser
import logging

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
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1
    )
    args = parser.parse_args()
    level = logging.DEBUG if args.verbose > 1 else logging.INFO if args.verbose == 1 else None
    if level:
        logging.basicConfig(level=level, format="%(asctime)s :: %(name)s :: %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    uvicorn.run("bank_credit.app.main:app", host=args.host, port=args.port, reload=args.reload)
