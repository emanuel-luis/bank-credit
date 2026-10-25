import logging
from argparse import ArgumentParser

import uvicorn

from bank_credit.app.config import get_settings


def main():
    parser = ArgumentParser(description="Bank Credit Application")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()
    logging.basicConfig(
        level=get_settings().log_level.upper(),
        format="%(asctime)s :: %(name)s :: %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    uvicorn.run(
        "bank_credit.app.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
