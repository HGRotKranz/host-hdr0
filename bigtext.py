#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: hikka_min 1.2.10

# meta pic: https://img.icons8.com/external-soft-fill-juicy-fish/480/000000/external-big-cute-monsters-soft-fill-soft-fill-juicy-fish-4.png
# meta banner: https://mods.hikariatama.ru/badges/bigtext.jpg
# meta developer: @rotkranz
# scope: hikka_only

import contextlib

from telethon.tl.types import Message

from .. import loader, utils

mapping = {
    "a": """█▀▀█\n █▄▄█\n ▀  ▀""",
    "b": """█▀▀▄\n █▀▀▄\n ▀▀▀""",
    "c": """█▀▀\n █\n ▀▀▀""",
    "d": """█▀▀▄\n █  █\n ▀▀▀""",
    "e": """█▀▀\n █▀▀\n ▀▀▀""",
    "f": """█▀▀\n █▀▀\n ▀""",
    "g": """█▀▀▀\n █ ▀█\n ▀▀▀▀""",
    "h": """█  █\n █▀▀█\n ▀  ▀""",
    "i": """▀\n ▀█▀\n ▀▀▀""",
    "j": """▀\n █\n █▄█""",
    "k": """█ █\n █▀▄\n ▀ ▀""",
    "l": """█\n █\n ▀▀▀""",
    "m": """█▀▄▀█\n █ ▀ █\n ▀   ▀""",
    "n": """█▀▀▄\n █  █\n ▀  ▀""",
    "o": """█▀▀█\n █  █\n ▀▀▀▀""",
    "p": """█▀▀█\n █  █\n █▀▀▀""",
    "q": """█▀▀█\n █  █\n ▀▀█▄""",
    "r": """█▀▀█\n █▄▄▀\n █  █""",
    "s": """█▀▀▀█\n ▀▀▀▄▄\n █▄▄▄█""",
    "t": """▀▀█▀▀\n █\n █""",
    "u": """█  █\n █  █\n ▀▄▄▀""",
    "v": """█   █\n █ █\n ▀▄▀""",
    "w": """█   █\n █ █ █\n █▄▀▄█""",
    "x": """▀▄ ▄▀\n █\n ▄▀ ▀▄""",
    "y": """█   █\n █▄▄▄█\n █""",
    "z": """█▀▀▀█\n ▄▄▄▀▀\n █▄▄▄█""",
    " ": """     \n     \n     """,
}


def process(cir, text):
    result = ""
    for chunk in utils.chunks(
        [mapping.get(letter.lower(), "").splitlines() for letter in text], cir
    ):
        row = ["" for _ in range(max(list(map(len, mapping.values()))))]
        row_result = []
        for i, line in enumerate(row):
            for letter in chunk:
                with contextlib.suppress(IndexError):
                    l_ = letter[i]
                    if len(l_) < 5:
                        l_ += " " * (5 - len(l_))
                    line += f"{l_} "

            row_result += [line]

        result += "\n".join([r for r in row_result if r.strip()]) + "\n"

    return result


@loader.tds
class BigTextMod(loader.Module):
    """Creates big ASCII Text"""

    strings = {"name": "BigText"}

    async def btcmd(self, message: Message):
        """[chars in line] - Create big text"""
        args = utils.get_args_raw(message)
        cir = 6
        if args.split() and args.split()[0].isdigit():
            cir = int(args.split()[0])
            args = args[args.find(" ") + 1 :]

        await utils.answer(message, f"<code>{process(cir, args)}</code>")
