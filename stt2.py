from .. import loader, utils
from telethon import events
import logging
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.errors.common import AlreadyInConversationError

logger = logging.getLogger(__name__)


def register(cb):
    cb(sttMod())

@loader.tds
class sttMod(loader.Module):
    """FOR ONE-USER USE ONLY"""
    strings = {'name': 'sttMod',
               'on': '<b>Автоматическое преобразование включено</b>',
               'off': '<b>Автоматическое преобразование выключено</b>',
               'afk': '<b>Я не принимаю голосовые сообщения • I no longer accept voice messages</b>',
               'afk_reason': '<b>Я не принимаю голосовые сообщения • I do not accept voice messages right now\nПричина • Reason:</b> <i>{}</i>',
               'strict_on':'<b>Строгий режим включен</b>',
               'strict_off':'<b>Строгий режим выключен</b>',}

    def __init__(self):
        self.name = self.strings['name']
        self._me = None
        self._rateLimit = []

    async def client_ready(self, client, db):
        self.client = client
        self._db = db
        self._me = await client.get_me(True)

    async def sttcmd(self, message):  # u can copy this, but pls point me as a source
        """Speech to text"""
        reply = await message.get_reply_message()
        if not reply:
            await message.edit('<code>I need a reply</code>')
            return
        if reply.voice or reply.video_note:  # check if reply message is a voice message
            if not message.reply_to_msg_id:
                await message.edit('<code>need reply</code>')
                return
            elif message.reply_to_msg_id:
                voice_mess = True  # just variable for check
        else:  # if not -> return
            await message.edit('<code>I need voice message</code>')
            return
        chat = '@voicybot'  # telegram bot
        await message.edit('<code>Listening...</code>')
        try:
            async with message.client.conversation(chat) as conv:  # conversation with @voicybot
                try:
                    response = conv.wait_event(events.NewMessage(incoming=True,
                                                                 from_users=259276793))
                    if voice_mess:  # line 38
                        await message.client.forward_messages(chat, reply)
                    else:
                        await conv.edit('something went wrong')
                    response = await response
                except YouBlockedUserError:  # if bot in black list
                    await message.reply('<code>Unblock @voicybot</code>')
                    return
                if not response.message.text:
                    await message.edit('<code>bot answer is not a text</code>')
                    return
                await message.delete()
                if voice_mess:
                    await message.client.send_message(message.chat_id,
                                                     f'<b>Transcription: </b> {response.message.message}',
                                                     reply_to=reply.id)
                    await response.delete()
                else:
                    await message.edit('something went wrong')
        except AlreadyInConversationError:
            await message.edit('<code>can not do 2 tasks in the same time</code>')

    async def vconcmd(self, message):
        """turn on automatic voice transcription"""
        self._db.set(__name__, 'voicy', True)
        self._db.set(__name__, "ratelimit", [])
        await message.edit(self.strings['on'])

    async def vcoffcmd(self, message):
        """turn off automatic voice transcription"""
        self._db.set(__name__, 'voicy', False)
        self._db.set(__name__, "ratelimit", [])
        await message.edit(self.strings['off'])

    async def protectcmd(self, message):
        """.protect [text]"""
        if utils.get_args_raw(message):
            self._db.set(__name__, 'afk', utils.get_args_raw(message))
            await message.edit(self.strings["afk"])
        else:
            self._db.set(__name__, 'afk', True)
            await message.edit(self.strings["afk"])

    async def unprotectcmd(self, message):
        """Accept islam"""
        self._db.set(__name__, 'afk', False)
        await message.edit('<b>Now i accept voice messages</b>')

    async def strictcmd(self, message):
        """Strict mode will delete all voice messages with your mention and in your PM"""
        self._db.set(__name__, 'strict', True)
        await utils.answer(message, self.strings["strict_on"])

    async def unstrictcmd(self, message):
        """Turn off strict mode"""
        self._db.set(__name__, 'strict', False)
        await utils.answer(message, self.strings["strict_off"])

    async def watcher(self, message):
        state = self.on_state()
        afk_state = self.get_afk()
        me_entity = await self.client.get_me(id)
        my_id = me_entity.user_id
        strict_mode = self.get_strict()

        if strict_mode is True:
            if message.from_id == my_id:
                return
            if message.mentioned or message.is_private is True:
                if message.voice:
                    await utils.answer(message, '<b>Я не принимаю и не слушаю голосовые сообщения • I do not accept voice messages right now</b>')
                    await message.delete()
                    return

        if afk_state is False:
            return
        if message.from_id == my_id:
            return  
        if message.mentioned or message.is_private is True:
            if message.voice:
                if afk_state is not True:
                    ret = self.strings["afk_reason"].format(str(afk_state))
                    await utils.answer(message, ret)
                else:
                    await utils.answer(message,
                                      '<b>Я не принимаю и не слушаю голосовые сообщения • I do not accept voice messages right now</b>')
        if not state:
            return
        if message.voice or message.video_note:
            if message.voice or message.video_note:  # check if reply message is a voice message
                chat = '@voicybot'  # telegram bot
            try:
                async with message.client.conversation(chat) as conv:  # conversation with @voicybot
                    try:
                        response = conv.wait_event(events.NewMessage(incoming=True,
                                                                    from_users=259276793))
                        await message.client.forward_messages(chat, message)
                        response = await response
                    except YouBlockedUserError:  # if bot in black list
                        await self.client.send_message(message.chat_id,'<code>Unblock @voicybot</code>')
                        return
                    if not response.message.text:
                        await self.client.send_message(message.chat_id,'<code>answer is not a text</code>')
                        return
                    await self.client.send_message(message.chat_id,
                                                   f'<b>Transcription: </b> {response.message.message}',
                                                    reply_to=message.id)
                    await response.delete()
            except AlreadyInConversationError:
                return
        else:
            return

    def on_state(self):
        return self._db.get(__name__, 'voicy', False)

    def get_strict(self):
        return self._db.get(__name__, 'strict', True)

    def get_afk(self):
        return self._db.get(__name__, 'afk', True)
