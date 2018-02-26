import os

from mastodon import Mastodon

import graftbot.dirs
from graftlib.world import World


def register_app(world: World, api_base_url: str) -> int:
    os.makedirs(graftbot.dirs.config_dir(), exist_ok=True)
    Mastodon.create_app(
         "graft",
         api_base_url=api_base_url,
         website="https://github.com/andybalaam/graft",
         to_file=graftbot.dirs.client_file(),
    )
    return 0
