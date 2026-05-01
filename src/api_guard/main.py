from __future__ import annotations

import argparse

import uvicorn

from api_guard.config import load_config
from api_guard.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="API Guard service")
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to the TOML config file.",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    app = create_app(args.config)
    uvicorn.run(app, host=config.bind_host, port=config.bind_port)


if __name__ == "__main__":
    main()
