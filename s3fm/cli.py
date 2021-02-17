"""Cli access point for s3fm application."""
import asyncio

import click

from s3fm.app import App
from s3fm.exceptions import Bug, ClientError


@click.command()
@click.help_option("-h", "--help")
def main() -> None:
    """Process config, read cache and then run s3fm application."""
    try:
        # TODO: get user config
        asyncio.run(App(no_cache=False).run())
    except ClientError:
        raise
    except Exception as e:
        raise Bug(str(e))
