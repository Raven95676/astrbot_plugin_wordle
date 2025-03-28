import os
import random
import re

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.star.filter.event_message_type import EventMessageType

from .games import WordleBase, WordleClassic  # type: ignore

IGNORGE_MSG = ["wordle start", "wordle stop", "wordle hint"]


@register(
    "astrbot_plugin_wordle",
    "Raven95676",
    "Astrbot wordle游戏，支持指定位数",
    "1.0.1",
    "https://github.com/Raven95676/astrbot_plugin_wordle",
)
class PluginWordle(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.game_sessions: dict[str, WordleBase] = {}

    @staticmethod
    async def get_answers(length, count: int = 1) -> tuple[list[str], list[str]] | None:
        try:
            wordlist_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "wordlist.txt"
            )

            if not os.path.exists(wordlist_path):
                logger.error("词表文件不存在")
                return None

            with open(wordlist_path, "r", encoding="utf-8") as file:
                content = file.read()
                words = content.split()
                filtered_words = [
                    word.strip().upper()
                    for word in words
                    if len(word.strip()) == length
                ]

                if not filtered_words:
                    return None

                return random.sample(filtered_words, count), filtered_words
        except Exception as e:
            logger.error(f"加载词表失败: {e!s}")
            return None

    @filter.command_group("wordle")
    def wordle(self):
        pass

    @wordle.command("start")
    async def start_wordle(self, event: AstrMessageEvent, length: int = 5):
        """开始Wordle游戏"""
        result = await self.get_answers(length, 1)
        session_id = event.unified_msg_origin

        if session_id in self.game_sessions:
            del self.game_sessions[session_id]

        if not result:
            yield event.plain_result(f"未找到长度为{length}的单词")
            return

        answer, filtered_words = result
        game = WordleClassic(answer[0], filtered_words)
        self.game_sessions[session_id] = game
        yield event.plain_result("游戏已开始，请输入猜测")
        logger.debug(f"答案是：{answer}")

    @wordle.command("stop")
    async def stop_wordle(self, event: AstrMessageEvent):
        """中止Wordle游戏"""
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
            yield event.plain_result("已结束当前游戏")
        else:
            yield event.plain_result("当前未开始游戏")

    @wordle.command("hint")
    async def give_hint(self, event: AstrMessageEvent):
        """获取提示（第一个字母）"""
        session_id = event.unified_msg_origin
        if session_id not in self.game_sessions:
            yield event.plain_result("当前未开始游戏")
            return

        game = self.game_sessions[session_id]
        hint = f"提示: 第一个字母是 {game.answer[0]}"
        yield event.plain_result(hint)

    @filter.event_message_type(EventMessageType.ALL)  # noqa: F405
    async def on_all_message(self, event: AstrMessageEvent):
        msg = event.get_message_str()
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions and event.is_at_or_wake_command:
            game = self.game_sessions[session_id]

            for IGNORGE in IGNORGE_MSG:
                if IGNORGE in msg:
                    return

            length = game.length
            if len(msg) != length:
                yield event.plain_result(f"输入单词长度应该为{length}")
                return

            if not msg.isalpha():
                yield event.plain_result("输入应该是英文")
                return

            if msg.upper() not in game.valid_words:
                yield event.plain_result("该单词不在有效词表中，请重新输入")
                return

            image_result = await game.guess(msg)

            # 保证兼容性,处理Windows下非法路径问题
            if os.name == "nt":
                session_id = re.sub(r'[\\/:*?"<>|!]', "_", session_id)
            img_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"{session_id}_{len(game.guesses)}_wordle.png",
            )
            with open(img_path, "wb") as f:
                f.write(image_result)

            if game.is_won:
                sender_info = (
                    event.get_sender_name()
                    if event.get_sender_name()
                    else event.get_sender_id()
                )
                game_status = f"恭喜{sender_info}猜对了！正确答案是: {game.answer}"
                del self.game_sessions[session_id]
            elif game.is_game_over:
                game_status = f"游戏结束。正确答案是: {game.answer}"
                del self.game_sessions[session_id]
            else:
                game_status = f"已猜测 {len(game.guesses)}/{game.max_attempts} 次"

            await event.send(MessageChain().file_image(img_path).message(game_status))

            os.remove(img_path)

    def terminate(self):
        """当插件被卸载/停用时会调用"""
        del self.game_sessions
