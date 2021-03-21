"""Cli access point for s3fm application."""
import asyncio

import click

from s3fm.api.config import Config
from s3fm.app import App
from s3fm.exceptions import Bug, ClientError


@click.command()
@click.help_option("-h", "--help")
def main() -> None:
    """Process config, read history and then run s3fm application.

    Raises:
        ClientError: When exception is caused due to client configuration.
        Bug: When exception is caused by unknown issue.
    """
    try:
        config = Config.load_config()
        asyncio.run(App(config=config, no_history=False).run())
    except ClientError:
        raise
    except Exception as e:
        raise Bug(str(e))
