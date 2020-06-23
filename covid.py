#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2020 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import requests
import json
from datetime import datetime
import dateutil.parser

from .. import loader, utils

logger = logging.getLogger(__name__)


class CoronaReportsMod(loader.Module):
    """Получай самую последнюю информацию о COVID-19"""
    strings = {"name": "COVID-19-RU"}
    def __init__(self):
        self.config = loader.ModuleConfig("Страна по умолчанию", ("russia"),
                                          "Введите другую страну здесь")

    async def coronacmd(self, message):
        """.corona <country (Optional)>"""
        args = utils.get_args_raw(message)
        if not args:
            country = self.config["Страна по умолчанию"]
        else:
            country = args
            
        await message.edit("<code>Получаю информацию...</code>")

        url = "https://covid19.mathdro.id/api/countries/" + country
        tries = 0
        response = requests.get(url)

        while response.status_code == 400 and tries < 10:
            response = requests.get(url)
            tries += 1
            await message.edit("<code>Попытка #" + str(tries) + "...</code>")

        jsonDumps = json.dumps(response.json(), sort_keys=True)
        jsonResponse = json.loads(jsonDumps)

        if(response.status_code == 200):
            confirmed = jsonResponse['confirmed']['value']
            recovered = jsonResponse['recovered']['value']
            deaths = jsonResponse['deaths']['value']       
            active = confirmed - recovered - deaths

            try:
                lastUpdate = dateutil.parser.parse(jsonResponse['lastUpdate']).strftime("%d/%m/%Y - %X")
            except (ValueError, TypeError) as e:
                logger.error(e)
                lastUpdate = jsonResponse['lastUpdate']

            msg = "<s>-------------------------------------</s>\n";
            msg += "В "+ country.capitalize() + "<i> "+lastUpdate+"</i>\n"
            msg += "<s>-------------------------------------</s>\n";
            msg+= "<b>Подтверждено:</b> " + str(confirmed)
            msg+= "\n<b>Болеют:</b> " + str(active) + " (" + str(round(active/confirmed * 100, 2)) + "%)"
            msg+= "\n<b>Выздоровели:</b> " + str(recovered) + " (" + str(round(recovered/confirmed * 100, 2)) + "%)"
            msg+= "\n<b>Летальные исходы:</b> " + str(deaths) + " (" + str(round(deaths/confirmed * 100, 2)) + "%)"


        elif response.status_code == 404:
            msg = "<code>"+jsonResponse['error']['message']+"</code>"
        elif response.status_code == 400:
            msg = "<code>Неправильный запрос</code>"
        else:
            msg = "<code>Неизвестная ошибка</code>"
        await message.edit(msg)
        