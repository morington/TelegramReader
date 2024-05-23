import asyncio
import math
from typing import Any

import PyPDF2
import structlog
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, Document, CallbackQuery
from confhub.reader import ReaderConf

from TelegramReader.keyboard import callback_keyb, template

logger: structlog.BoundLogger = structlog.get_logger(__name__)

reader = ReaderConf('config/settings.yml', 'config/.secrets.yml', dev=True)
reader.create_service_urls()
configuration = reader.data

bot = Bot(token=configuration.get('telegrambot', {}).get('token'))
dp = Dispatcher()

LIMIT_LETTERS_FOR_PAGE = 1700  # 1500-2500


class FileReading(StatesGroup):
    ready = State()
    busy = State()


def get_text_chunk(full_text: str, offset: int):
    limit = min(offset + LIMIT_LETTERS_FOR_PAGE, len(full_text))

    if limit < len(full_text):
        while full_text[limit] not in " .,!?-":
            limit -= 1
            if limit == offset:
                break

    chunk = full_text[offset:limit]
    return chunk


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FileReading.ready)
    await message.answer(
        text="Добро пожаловать в TelegramReader!\n\n"
             "Я могу дать возможность прочитать любую книгу в формате PDF!\n"
             "Просто отправь мне файл и мы начнем!"
    )


@dp.message(F.document, FileReading.ready)
async def doc_file(message: Message, bot: Bot, state: FSMContext) -> Any:
    file: Document = message.document

    if file.mime_type != 'application/pdf':
        return await message.answer('Отправь пожалуйста PDF формат, я не работаю с другими расширениями.')

    filename = f'Books/{file.file_name}'
    await bot.download(file, destination=filename)
    await message.answer('Загрузка файла завершена! Работаем над текстом..')

    reader_pdf = PyPDF2.PdfReader(filename)

    all_text = ""
    for page in range(len(reader_pdf.pages)):
        all_text += reader_pdf.pages[page].extract_text()

    text_page = get_text_chunk(all_text, 0)

    pages = math.ceil(len(all_text) / LIMIT_LETTERS_FOR_PAGE)

    await state.update_data(
        page=1,
        pages=pages,
        book=all_text,
        offset=len(text_page),
        chunks=[0, len(text_page)]
    )

    await state.set_state(FileReading.busy)

    await message.answer(
        text=text_page,
        reply_markup=callback_keyb(
            [
                [
                    template('Предыдущая страница', 'previous_page'),
                    template(f'1/{pages}', '_'),
                    template('Следующая страница', 'next_page')
                ],
                template('Закрыть книгу', 'close_book')
            ]
        )
    )


@dp.callback_query(F.data == 'next_page', FileReading.busy)
async def next_page(callback: CallbackQuery, state: FSMContext) -> None:
    user_data: dict = await state.get_data()

    if user_data.get('page') == user_data.get('pages'):
        await callback.answer()
        return

    text_page = get_text_chunk(user_data.get('book'), user_data.get('offset'))
    user_data.get('chunks').append(len(text_page))

    page = user_data.get('page') + 1

    await state.update_data(
        page=page, offset=user_data.get('offset')+len(text_page), chunks=user_data.get('chunks')
    )

    await callback.message.edit_text(
        text=text_page,
        reply_markup=callback_keyb(
            [
                [
                    template('Предыдущая страница', 'previous_page'),
                    template(f'{page}/{user_data.get("pages")}', '_'),
                    template('Следующая страница', 'next_page')
                ],
                template('Закрыть книгу', 'close_book')
            ]
        )
    )


@dp.callback_query(F.data == 'previous_page', FileReading.busy)
async def previous_page(callback: CallbackQuery, state: FSMContext) -> None:
    user_data: dict = await state.get_data()

    if user_data.get('page') == 1:
        await callback.answer()
        return

    chunks = user_data.get('chunks')[:-2]
    offset = chunks[-1]
    text_page = get_text_chunk(user_data.get('book'), offset)
    chunks.append(len(text_page))

    page = user_data.get('page') - 1

    await state.update_data(page=page, offset=offset+len(text_page), chunks=chunks)

    await callback.message.edit_text(
        text=text_page,
        reply_markup=callback_keyb(
            [
                [
                    template('Предыдущая страница', 'previous_page'),
                    template(f'{page}/{user_data.get("pages")}', '_'),
                    template('Следующая страница', 'next_page')
                ],
                template('Закрыть книгу', 'close_book')
            ]
        )
    )


@dp.callback_query(F.data == 'close_book', FileReading.busy)
async def close_book(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FileReading.ready)

    await callback.message.answer('Книга успешно закрыта!\nВы можете в любое время отправить мне новую.')


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
