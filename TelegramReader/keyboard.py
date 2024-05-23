from typing import Optional

import structlog
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

logger = structlog.get_logger(__name__)


def template(text: str, callback_data: Optional[str] = None) -> dict[str, str]:
    """
    Example: template("text", "callback")

    :param text: str
    :param callback_data: Optional[str]
    :return: dict[str, str]
    """
    return {
        "text": text,
        "callback_data": (callback_data if callback_data is not None else "CALLBACK_DATA"),
    }


def callback_keyb(buttons: list[list | dict]) -> InlineKeyboardMarkup:
    """
    Example: [template(), template() [template(), template()]]

    :param buttons: list[dict]
    :return: InlineKeyboardMarkup
    """
    keyboard: list = []

    for button in buttons:
        if isinstance(button, list):
            keyboard.append([InlineKeyboardButton(**btn) for btn in button])
        elif isinstance(button, dict):
            keyboard.append([InlineKeyboardButton(**button)])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def reply_keyb(buttons: list[str | list[str]]) -> ReplyKeyboardMarkup:
    """
    Example: ["BTN_1", "BTN_2" ["BTN_3", "BTN_4"]]

    :param buttons: list[str]
    :return: ReplyKeyboardMarkup
    """
    keyboard: list = []

    for item in buttons:
        if isinstance(item, list):
            keyboard.append([KeyboardButton(text=text) for text in item])
        elif isinstance(item, str):
            keyboard.append([KeyboardButton(text=item)])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, is_persistent=True)
