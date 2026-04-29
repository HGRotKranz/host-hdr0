# meta developer: @RotKranz
version = (1, 0, 1)

from .. import loader, utils
from telethon.tl.functions.account import GetAuthorizationsRequest
import logging

logger = logging.getLogger(__name__)

@loader.tds
class SessionCheckerMod(loader.Module):
    """Перевірка активних сесій аккаунта"""
    strings = {"name": "SessionChecker"}

    @loader.command()
    async def sessions(self, message):
        """Показати всі активні сесії"""
        await utils.answer(message, "<b>🔄 Запитую список сесій у Telegram...</b>")
        
        try:
            # Запит до API Telegram
            result = await message.client(GetAuthorizationsRequest())
            
            text = "<b>📱 Активні сесії твого аккаунта:</b>\n\n"
            
            for session in result.authorizations:
                status = "🟢 (Ця сесія)" if session.current else "⚪️"
                device = f"{session.device_model}, {session.platform}"
                app = f"{session.app_name} (v{session.app_version})"
                location = f"{session.country} (IP: {session.ip})"
                
                text += (
                    f"{status} <b>{device}</b>\n"
                    f"└ <b>Додаток:</b> <code>{app}</code>\n"
                    f"└ <b>Локація:</b> <code>{location}</code>\n"
                    f"└ <b>ID сесії:</b> <code>{session.hash}</code>\n\n"
                )
            
            await utils.answer(message, text)
            
        except Exception as e:
            logger.error(f"Error fetching sessions: {e}")
            await utils.answer(message, f"<b>❌ Помилка:</b> <code>{str(e)}</code>")
