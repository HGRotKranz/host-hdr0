"""

    █▀▀ ▄▀█ █▄▀ █▀▀ █▀ ▀█▀ █░█░█ █ ▀▄▀
    █▄▄ █▀█ █░█ ██▄ ▄█ ░█░ ▀▄▀▄▀ █ █░█

    Copyleft 2022 t.me/CakesTwix
    Improved version with multi-image support, tags search, pagination & more

"""

__version__ = (2, 0, 0)

# requires: aiohttp
# meta pic: https://www.seekpng.com/png/full/824-8246338_yandere-sticker-yandere-simulator-ayano-bloody.png
# meta developer: @cakestwix_mods

import logging
import aiohttp
import asyncio
from .. import loader, utils

logger = logging.getLogger(__name__)

BASE_URL = "https://yande.re/post.json"
VOTE_URL = "https://yande.re/post/vote.json?login={login}&password_hash={password_hash}"


@loader.unrestricted
@loader.ratelimit
@loader.tds
class MoebooruMod(loader.Module):
    """Module for obtaining art from the ImageBoard yande.re"""

    strings = {
        "name": "Yandere",
        "no_results": "❌ No results found for tags: <b>{tags}</b>",
        "vote_ok": "✅ Voted successfully!",
        "vote_login": "❌ Login or password incorrect.",
        "vote_error": "❌ ERROR, check .logs",
        "vote_usage": "⚠️ Reply to a yandere post and provide a score.\nScores: Bad=-1, None=0, Good=1, Great=2, Favorite=3\nExample: <code>.yvote 3</code>",
        "invalid_count": "⚠️ Count must be between 1 and 10.",
        "invalid_page": "⚠️ Page must be a positive number.",
        "loading": "🔄 Loading...",
        "cfg_yandere_login": "Login from yande.re",
        "cfg_yandere_password_hash": "SHA1 hashed password",
        "cfg_default_count": "Default number of images to fetch (1-10)",
        "cfg_nsfw": "Allow NSFW content (rating:e/q). If False, only safe content is shown.",
    }

    strings_ru = {
        "no_results": "❌ Нічого не знайдено за тегами: <b>{tags}</b>",
        "vote_login": "❌ Невірний логін або пароль.",
        "vote_error": "❌ ПОМИЛКА, перевір .logs",
        "vote_usage": "⚠️ Відповідай на пост yandere та вказуй оцінку.\nОцінки: Bad=-1, None=0, Good=1, Great=2, Favorite=3\nПриклад: <code>.yvote 3</code>",
        "invalid_count": "⚠️ Кількість має бути від 1 до 10.",
        "invalid_page": "⚠️ Сторінка має бути позитивним числом.",
        "loading": "🔄 Завантаження...",
        "cfg_yandere_login": "Логін з yande.re",
        "cfg_yandere_password_hash": "Хешований пароль SHA1",
        "cfg_default_count": "Кількість зображень за замовчуванням (1-10)",
        "cfg_nsfw": "Дозволити NSFW контент (rating:e/q). Якщо False — тільки безпечний контент.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "yandere_login",
            "None",
            lambda m: self.strings("cfg_yandere_login", m),
            "yandere_password_hash",
            "None",
            lambda m: self.strings("cfg_yandere_password_hash", m),
            "default_count",
            5,
            lambda m: self.strings("cfg_default_count", m),
            "nsfw",
            True,
            lambda m: self.strings("cfg_nsfw", m),
        )
        self.name = self.strings["name"]

    def _auth_params(self):
        login = self.config["yandere_login"]
        pw = self.config["yandere_password_hash"]
        if login != "None" and pw != "None":
            return f"&login={login}&password_hash={pw}"
        return ""

    def _safe_tag(self):
        """Append rating filter if NSFW is disabled."""
        return "" if self.config["nsfw"] else " rating:s"

    def _caption(self, post):
        tags_preview = " ".join(post["tags"].split()[:10])
        if len(post["tags"].split()) > 10:
            tags_preview += "…"
        lines = [
            f"🏷 <b>Tags:</b> <code>{tags_preview}</code>",
            f"✍️ <b>Author:</b> {post.get('author') or 'Unknown'}",
        ]
        source = post.get("source")
        if source:
            lines.append(f"🔗 <b>Source:</b> {source}")
        lines.append(
            f"🆔 <a href='https://yande.re/post/show/{post['id']}'>{post['id']}</a>"
            f"  |  ⭐ Score: {post.get('score', 0)}"
        )
        return "\n".join(lines)

    async def _fetch_posts(self, tags: str, limit: int = 20, page: int = 1):
        """Fetch posts from yande.re API."""
        params = (
            f"?limit={limit}&page={page}"
            f"&tags={tags}{self._safe_tag()}"
            f"{self._auth_params()}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL + params) as resp:
                return await resp.json()

    async def _send_posts(self, message, posts, count):
        """Send up to `count` posts to the chat."""
        import random
        selected = random.sample(posts, min(count, len(posts)))
        for post in selected:
            url = post.get("sample_url") or post.get("file_url")
            if not url:
                continue
            await message.client.send_file(
                message.chat_id,
                url,
                caption=self._caption(post),
            )

    # ─── Commands ───────────────────────────────────────────────

    @loader.unrestricted
    @loader.ratelimit
    async def ylastcmd(self, message):
        """Get the latest posted art. Usage: .ylast [count=1]"""
        args = utils.get_args(message)
        count = self._parse_count(args, default=1)
        if count is None:
            return await utils.answer(message, self.strings("invalid_count"))

        await utils.answer(message, self.strings("loading"))
        posts = await self._fetch_posts(tags="", limit=count)
        await message.delete()

        if not posts:
            return await message.respond(self.strings("no_results").format(tags="latest"))

        for post in posts[:count]:
            url = post.get("sample_url") or post.get("file_url")
            if url:
                await message.client.send_file(
                    message.chat_id, url, caption=self._caption(post)
                )

    @loader.unrestricted
    @loader.ratelimit
    async def yrandomcmd(self, message):
        """Get random art. Usage: .yrandom [count=5]"""
        args = utils.get_args(message)
        count = self._parse_count(args, default=self.config["default_count"])
        if count is None:
            return await utils.answer(message, self.strings("invalid_count"))

        await utils.answer(message, self.strings("loading"))
        posts = await self._fetch_posts(tags="order:random", limit=count * 2)
        await message.delete()

        if not posts:
            return await message.respond(self.strings("no_results").format(tags="random"))

        await self._send_posts(message, posts, count)

    @loader.unrestricted
    @loader.ratelimit
    async def ysearchcmd(self, message):
        """Search art by tags. Usage: .ysearch <tags> [count=5] [page=1]
        
        Example: .ysearch maid 3
        Example: .ysearch blue_eyes blonde_hair 5 2
        """
        args = utils.get_args(message)
        if not args:
            return await utils.answer(
                message,
                "Usage: <code>.ysearch tags [count] [page]</code>\nExample: <code>.ysearch maid 3</code>"
            )

        # Parse trailing numbers as count and page
        page = 1
        count = self.config["default_count"]
        tag_parts = list(args)

        if tag_parts and tag_parts[-1].isdigit():
            maybe_page = int(tag_parts[-1])
            if len(tag_parts) >= 2 and tag_parts[-2].isdigit():
                page = maybe_page
                count = int(tag_parts[-2])
                tag_parts = tag_parts[:-2]
            else:
                count = maybe_page
                tag_parts = tag_parts[:-1]

        if not (1 <= count <= 10):
            return await utils.answer(message, self.strings("invalid_count"))
        if page < 1:
            return await utils.answer(message, self.strings("invalid_page"))

        tags = "+".join(tag_parts)
        await utils.answer(message, self.strings("loading"))
        posts = await self._fetch_posts(tags=tags, limit=count * 3, page=page)
        await message.delete()

        if not posts:
            return await message.respond(
                self.strings("no_results").format(tags=" ".join(tag_parts))
            )

        await self._send_posts(message, posts, count)

    @loader.unrestricted
    @loader.ratelimit
    async def ytopratecmd(self, message):
        """Get top-rated art. Usage: .ytoprate [count=5]"""
        args = utils.get_args(message)
        count = self._parse_count(args, default=self.config["default_count"])
        if count is None:
            return await utils.answer(message, self.strings("invalid_count"))

        await utils.answer(message, self.strings("loading"))
        posts = await self._fetch_posts(tags="order:score", limit=count * 2)
        await message.delete()

        if not posts:
            return await message.respond(self.strings("no_results").format(tags="top rated"))

        await self._send_posts(message, posts, count)

    @loader.unrestricted
    @loader.ratelimit
    async def yvotecmd(self, message):
        """Vote for art (reply to a yandere post).
        Scores: Bad=-1, None=0, Good=1, Great=2, Favorite=3
        Usage: .yvote <score>
        """
        reply = await message.get_reply_message()
        args = utils.get_args(message)

        if not reply or not args:
            return await utils.answer(message, self.strings("vote_usage"))

        # Extract ID from caption
        try:
            raw = reply.raw_text or ""
            yandere_id = None
            for line in raw.splitlines():
                if "🆔" in line:
                    # Grab the numeric ID after the emoji
                    part = line.split("🆔")[1].strip()
                    yandere_id = "".join(filter(str.isdigit, part.split()[0]))
                    break
            if not yandere_id:
                raise ValueError("ID not found")
        except Exception:
            return await utils.answer(message, "❌ Could not find post ID in the replied message.")

        score = args[0]
        params = {"id": yandere_id, "score": score}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                VOTE_URL.format(
                    login=self.config["yandere_login"],
                    password_hash=self.config["yandere_password_hash"],
                ),
                data=params,
            ) as post:
                result_code = post.status

        if result_code == 200:
            await utils.answer(message, self.strings("vote_ok"))
        elif result_code == 403:
            await utils.answer(message, self.strings("vote_login"))
        else:
            await utils.answer(message, self.strings("vote_error"))

        await asyncio.sleep(4)
        await message.delete()

    # ─── Helpers ────────────────────────────────────────────────

    def _parse_count(self, args, default):
        if args and args[0].isdigit():
            val = int(args[0])
            if not (1 <= val <= 10):
                return None
            return val
        return default
