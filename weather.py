from .. import loader, utils  # pylint: disable=relative-beyond-top-level
import logging
import requests

logger = logging.getLogger(__name__)


def register(cb):
    cb(WeatherMod())


@loader.tds
class WeatherMod(loader.Module):
    """Gets weather info from wttr.in"""

    strings = {"name": "Weather"}

    async def client_ready(self, client, db):
        self.client = client

    @loader.unrestricted
    async def weathercmd(self, message):
        """.weather <city> for weather"""
        message.edit("<b>Weather by wttr.in</b>")
        city = utils.get_args(message)
        msg = []
        if city:
            await message.send("Getting weather...")
            for i in city:
                r = requests.get(
                    "https://wttr.in/" + i + "?format=%l:+%c+%t,+%w+%m&m"
                )
                msg.append(r.text)
            await message.edit("".join(msg))
        else:
            await message.send("Getting weather...")
            r = requests.get("https://wttr.in/?format=%l:+%c+%t,+%w+%m&m")
            await message.edit(r.text)
