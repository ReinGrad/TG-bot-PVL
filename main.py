import asyncio
import logging
import os
from dataclasses import dataclass
from typing import List, Dict

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=".env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env or environment variables")

PAGE_SIZE = 5

DISTRICTS = {
    "bayanaul": "Баянаул",
    "ekibastuz": "Экибастуз",
    "pavlodar": "Павлодар",
}

TOP7_SLUGS = {
    "konyr-auliye",
    "zhasybai-batyr",
    "mashkhur-zhusup",
    "akkelin-shormanov",
    "auliekol",
    "isabek-ishan",
    "sultanbet-sultan",
}


@dataclass(frozen=True)
class SacredObject:
    slug: str
    name: str
    district: str
    location: str
    photo_url: str
    description: str


FAQ_ITEMS = [
    (
        "Что такое сакральная карта?",
        "Это структурированный каталог значимых исторических, духовных и культурных мест региона с удобной навигацией по объектам.",
    ),
    (
        "Как пользоваться ботом?",
        "Откройте главное меню, выберите раздел и нажмите на интересующий объект. Бот покажет фото, описание и локацию.",
    ),
    (
        "Чем ТОП-7 отличается от полного списка?",
        "ТОП-7 — это ключевые объекты проекта. Полный список содержит больше мест и разбит по районам.",
    ),
    (
        "Можно ли посмотреть объекты по районам?",
        "Да. В разделе 'Все объекты' доступны Баянаул, Экибастуз и Павлодар с постраничной навигацией.",
    ),
    (
        "Сколько объектов в базе?",
        "В этой версии есть более 20 карточек. Часть списка можно расширять и обновлять без изменения логики бота.",
    ),
    (
        "Есть ли фото у каждого объекта?",
        "Да, карточки поддерживают фото. Для части mock-объектов можно заменить изображения на реальные локальные файлы или URL.",
    ),
    (
        "Откуда берутся данные?",
        "Из заранее подготовленного каталога внутри проекта. При необходимости его легко заменить на JSON, БД или API.",
    ),
    (
        "Как обновить список объектов?",
        "Добавьте новую карточку в список объектов и укажите район, описание, локацию и фото.",
    ),
    (
        "Можно ли добавить поиск?",
        "Да. Архитектура уже подходит для расширения: можно добавить поиск по названию, фильтры и избранное.",
    ),
    (
        "Для кого этот бот?",
        "Для студентов, туристов, преподавателей и всех, кто изучает сакральное наследие Павлодарского региона.",
    ),
]

PROJECT_TEXT = (
    "<b>О проекте</b>\n\n"
    "• 7 объектов республиканского значения\n"
    "• 36 региональных объектов\n"
    "• ежегодное обновление списка\n"
    "• Баянаульский район — центр сакральных мест\n\n"
    "Проект создан как удобный цифровой гид по сакральной карте Павлодарского региона."
)


def make_photo_url(slug: str) -> str:
    return f"https://picsum.photos/seed/{slug}/900/600"


def build_objects() -> List[SacredObject]:
    data = [
        SacredObject(
            slug="konyr-auliye",
            name="Пещера Коныр-Аулие",
            district="bayanaul",
            location="Баянаульский район, Павлодарская область",
            photo_url=make_photo_url("konyr-auliye"),
            description=(
                "Коныр-Аулие — один из самых узнаваемых сакральных объектов Баянаула. Место связано с легендами о целебной воде, "
                "внутренних гротах и древних паломнических маршрутах.\n\n"
                "Сегодня сюда приезжают не только ради природы, но и ради духовного опыта. Маршрут к пещере сочетает горный ландшафт, "
                "исторический контекст и атмосферу уединения."
            ),
        ),
        SacredObject(
            slug="zhasybai-batyr",
            name="Могила Жасыбай батыра",
            district="bayanaul",
            location="Баянаульский район, рядом с одноимённым озером",
            photo_url=make_photo_url("zhasybai-batyr"),
            description=(
                "Мемориальное место, связанное с именем Жасыбай батыра, занимает важное место в исторической памяти региона. Оно напоминает "
                "о героическом прошлом и традиции почитания защитников земли.\n\n"
                "Памятный комплекс и окружающий ландшафт формируют сильный образ территории: здесь соединяются история, легенда и природная среда."
            ),
        ),
        SacredObject(
            slug="mashkhur-zhusup",
            name="Мавзолей Машхур Жусуп Копеева",
            district="bayanaul",
            location="Баянаульский район, село Жанажол",
            photo_url=make_photo_url("mashkhur-zhusup"),
            description=(
                "Мавзолей посвящён Машхур Жусупу Копееву — выдающемуся поэту, мыслителю и просветителю. Это не просто мемориальный "
                "объект, а важная точка культурной памяти.\n\n"
                "Посетители приходят сюда, чтобы прикоснуться к наследию духовного лидера и увидеть современное пространство, где традиция "
                "сохранена в достойной архитектурной форме."
            ),
        ),
        SacredObject(
            slug="akkelin-shormanov",
            name="Комплекс Аккелин (Шорманов)",
            district="bayanaul",
            location="Баянаульский район",
            photo_url=make_photo_url("akkelin-shormanov"),
            description=(
                "Комплекс связан с историей семьи Шормановых и региональной элиты XIX века. В таких объектах особенно хорошо читается "
                "связь между родовой памятью, общественной ролью и локальной историей.\n\n"
                "Аккелин воспринимается как часть более широкой культурной карты Баянаула, где рядом существуют сакральные, исторические и "
                "этнографические слои наследия."
            ),
        ),
        SacredObject(
            slug="auliekol",
            name="Аулиеколь",
            district="bayanaul",
            location="Баянаульский район",
            photo_url=make_photo_url("auliekol"),
            description=(
                "Аулиеколь — объект, в котором природный ландшафт и сакральный смысл воспринимаются как единое целое. Название само по себе "
                "подчёркивает особый статус места.\n\n"
                "Для паломников и туристов это точка спокойного маршрута, где можно совместить познавательную поездку и отдых на природе."
            ),
        ),
        SacredObject(
            slug="isabek-ishan",
            name="Мавзолей Исабек ишан",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("isabek-ishan"),
            description=(
                "Мавзолей Исабек ишана связан с религиозно-духовной традицией и почитанием местных просветителей. Он входит в число объектов, "
                "которые формируют представление о сакральном наследии степного региона.\n\n"
                "Карточка объекта помогает быстро получить базовые сведения: где находится место, чем оно известно и почему его включают в туристические и образовательные маршруты."
            ),
        ),
        SacredObject(
            slug="sultanbet-sultan",
            name="Усадьба Султанбет султана",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("sultanbet-sultan"),
            description=(
                "Усадьба Султанбет султана — пример объекта, где историческая память связана с именем правителя и локальной аристократической традицией. "
                "Такие места помогают восстановить картину прошлого через архитектуру и предания.\n\n"
                "Сегодня объект интересен как исследователям, так и экскурсионным группам: он хорошо вписывается в маршрут по сакральным местам области."
            ),
        ),
        SacredObject(
            slug="bayanaul-tasbulaq",
            name="Источник Тасбұлақ",
            district="bayanaul",
            location="Баянаульский район",
            photo_url=make_photo_url("bayanaul-tasbulaq"),
            description="Родник с локальной сакральной репутацией. Подходит для расширения маршрута по природно-духовным точкам Баянаула.",
        ),
        SacredObject(
            slug="bayanaul-kempirtas",
            name="Скала Кемпиртас",
            district="bayanaul",
            location="Баянаульский район",
            photo_url=make_photo_url("bayanaul-kempirtas"),
            description="Скальный объект, известный своим выразительным силуэтом и включением в местные легенды. Хорошо подходит для коротких экскурсионных остановок.",
        ),
        SacredObject(
            slug="bayanaul-toraygyr",
            name="Урочище Торайгыр",
            district="bayanaul",
            location="Баянаульский район",
            photo_url=make_photo_url("bayanaul-toraygyr"),
            description="Ландшафтный объект, где природная среда тесно связана с исторической памятью и туристическими маршрутами региона.",
        ),
        SacredObject(
            slug="ekibastuz-aquly",
            name="Священный источник Акулы",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("ekibastuz-aquly"),
            description="Mock-объект для расширения каталога. Используется как пример карточки с фото, описанием и локацией.",
        ),
        SacredObject(
            slug="ekibastuz-karagaily",
            name="Курган Карагайлы",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("ekibastuz-karagaily"),
            description="Археолого-историческая точка в регионе. Подходит для демонстрации структурированного каталога в боте.",
        ),
        SacredObject(
            slug="ekibastuz-shiderty",
            name="Комплекс Шидерты",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("ekibastuz-shiderty"),
            description="Mock-объект, который можно заменить на реальный памятник без изменения интерфейса бота.",
        ),
        SacredObject(
            slug="ekibastuz-tasbulak",
            name="Родник Тасбұлақ",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("ekibastuz-tasbulak"),
            description="Место локального почитания и коротких остановок в маршрутах по району.",
        ),
        SacredObject(
            slug="ekibastuz-sarybulak",
            name="Скала Сарыбұлақ",
            district="ekibastuz",
            location="Экибастузский район",
            photo_url=make_photo_url("ekibastuz-sarybulak"),
            description="Природно-исторический объект в mock-каталоге. Используется для демонстрации пагинации и карточек.",
        ),
        SacredObject(
            slug="pavlodar-irtysh-memorial",
            name="Мемориальный комплекс Прииртышья",
            district="pavlodar",
            location="Павлодарский район",
            photo_url=make_photo_url("pavlodar-irtysh-memorial"),
            description="Mock-объект для Павлодарского района. Подходит для расширения полного каталога сакральной карты.",
        ),
        SacredObject(
            slug="pavlodar-karavan",
            name="Старый караванный путь",
            district="pavlodar",
            location="Павлодарский район",
            photo_url=make_photo_url("pavlodar-karavan"),
            description="Объект, подчеркивающий исторические маршруты движения и обмена между поселениями и степью.",
        ),
        SacredObject(
            slug="pavlodar-muslim-center",
            name="Духовный центр Павлодара",
            district="pavlodar",
            location="Павлодар",
            photo_url=make_photo_url("pavlodar-muslim-center"),
            description="Mock-объект, который демонстрирует карточку городского уровня для полной версии каталога.",
        ),
        SacredObject(
            slug="pavlodar-irtish-kamen",
            name="Памятный камень Иртыша",
            district="pavlodar",
            location="Павлодарский район",
            photo_url=make_photo_url("pavlodar-irtish-kamen"),
            description="Локальная точка памяти на берегу Иртыша. Хорошо вписывается в экскурсии по региону.",
        ),
        SacredObject(
            slug="pavlodar-zhyrau",
            name="Аллея жырау",
            district="pavlodar",
            location="Павлодар",
            photo_url=make_photo_url("pavlodar-zhyrau"),
            description="Mock-объект с культурным контекстом. Подходит для образовательных маршрутов и демонстрации карточек.",
        ),
    ]
    return data


OBJECTS = build_objects()
OBJECTS_BY_SLUG: Dict[str, SacredObject] = {item.slug: item for item in OBJECTS}
OBJECTS_BY_DISTRICT: Dict[str, List[SacredObject]] = {
    district: [item for item in OBJECTS if item.district == district] for district in DISTRICTS
}

router = Router()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗺 Сакральная карта", callback_data="menu:map")
    builder.button(text="🏛 ТОП-7 объектов", callback_data="menu:top7")
    builder.button(text="📍 Все объекты", callback_data="menu:all")
    builder.button(text="FAQ", callback_data="menu:faq")
    builder.button(text="📖 О проекте", callback_data="menu:about")
    builder.adjust(1)
    return builder.as_markup()


def menu_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:home")]]
    )


def faq_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, (question, _) in enumerate(FAQ_ITEMS):
        builder.button(text=f"{index + 1}. {question}", callback_data=f"faq:{index}")
    builder.button(text="⬅️ Назад", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


def faq_answer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ К вопросам", callback_data="menu:faq")]]
    )


def top7_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in OBJECTS:
        if item.slug in TOP7_SLUGS:
            builder.button(text=item.name, callback_data=f"obj:{item.slug}:top7")
    builder.button(text="⬅️ Назад", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


def districts_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for district_key, district_name in DISTRICTS.items():
        builder.button(text=district_name, callback_data=f"district:{district_key}:1")
    builder.button(text="⬅️ Назад", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


def district_list_keyboard(district_key: str, page: int) -> InlineKeyboardMarkup:
    items = OBJECTS_BY_DISTRICT[district_key]
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = items[start:end]

    rows: list[list[InlineKeyboardButton]] = []
    for item in page_items:
        rows.append([InlineKeyboardButton(text=item.name, callback_data=f"obj:{item.slug}:district_{district_key}_{page}")])

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"district:{district_key}:{page - 1}"))
    if end < len(items):
        nav_row.append(InlineKeyboardButton(text="Далее ➡️", callback_data=f"district:{district_key}:{page + 1}"))
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="🏙 Выбор района", callback_data="menu:all")])
    rows.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def detail_back_target(back_target: str) -> str:
    return back_target or "menu"


def detail_keyboard(back_target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back:{back_target}")]]
    )


async def send_object_detail(message_or_query, item: SacredObject, back_target: str) -> None:
    caption = (
        f"<b>{item.name}</b>\n"
        f"<i>{DISTRICTS[item.district]}</i>\n\n"
        f"{item.description}\n\n"
        f"<b>Локация:</b> {item.location}"
    )
    try:
        await message_or_query.answer_photo(
            photo=item.photo_url,
            caption=caption,
            reply_markup=detail_keyboard(back_target),
        )
    except TelegramAPIError:
        await message_or_query.answer(
            caption,
            reply_markup=detail_keyboard(back_target),
        )


def map_overview_text() -> str:
    return (
        "<b>Сакральная карта Павлодарского региона</b>\n\n"
        "Выберите район или откройте ТОП-7. В этом боте карта собрана в виде удобного каталога с фото, описанием и локацией.\n\n"
        "• Баянаул — главный центр сакральных мест\n"
        "• Экибастуз — маршруты памятных и духовных точек\n"
        "• Павлодар — городские и районные объекты"
    )


def all_overview_text() -> str:
    return (
        "<b>Все объекты</b>\n\n"
        "Список разбит по районам. Нажмите на район, затем выбирайте объекты постранично — по 5 карточек на страницу."
    )


def district_page_text(district_key: str, page: int) -> str:
    items = OBJECTS_BY_DISTRICT[district_key]
    total = len(items)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    district_name = DISTRICTS[district_key]
    return (
        f"<b>{district_name}</b>\n"
        f"Страница {page}/{pages}\n"
        f"Всего объектов: {total}\n\n"
        f"Нажмите на объект, чтобы открыть карточку."
    )


async def show_home(target: Message | CallbackQuery) -> None:
    text = (
        "<b>Интеллектуальный гид по сакральной карте Павлодарского региона</b>\n\n"
        "Выберите раздел в меню ниже."
    )
    if isinstance(target, Message):
        await target.answer(text, reply_markup=main_menu_keyboard())
    else:
        await target.message.edit_text(text, reply_markup=main_menu_keyboard())
        await target.answer()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await show_home(message)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await show_home(message)


@router.callback_query(F.data == "menu:home")
async def cb_home(query: CallbackQuery) -> None:
    await show_home(query)


@router.callback_query(F.data == "menu:map")
async def cb_map(query: CallbackQuery) -> None:
    await query.message.edit_text(map_overview_text(), reply_markup=districts_keyboard())
    await query.answer()


@router.callback_query(F.data == "menu:top7")
async def cb_top7(query: CallbackQuery) -> None:
    text = "<b>ТОП-7 объектов</b>\n\nВыберите объект из списка ниже."
    await query.message.edit_text(text, reply_markup=top7_keyboard())
    await query.answer()


@router.callback_query(F.data == "menu:all")
async def cb_all(query: CallbackQuery) -> None:
    await query.message.edit_text(all_overview_text(), reply_markup=districts_keyboard())
    await query.answer()


@router.callback_query(F.data == "menu:faq")
async def cb_faq(query: CallbackQuery) -> None:
    await query.message.edit_text("<b>FAQ</b>\n\nВыберите вопрос.", reply_markup=faq_keyboard())
    await query.answer()


@router.callback_query(F.data == "menu:about")
async def cb_about(query: CallbackQuery) -> None:
    await query.message.edit_text(PROJECT_TEXT, reply_markup=menu_back_keyboard())
    await query.answer()


@router.callback_query(F.data.startswith("district:"))
async def cb_district(query: CallbackQuery) -> None:
    _, district_key, page_str = query.data.split(":")
    page = max(1, int(page_str))
    items = OBJECTS_BY_DISTRICT[district_key]
    pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, pages)
    await query.message.edit_text(
        district_page_text(district_key, page),
        reply_markup=district_list_keyboard(district_key, page),
    )
    await query.answer()


@router.callback_query(F.data.startswith("obj:"))
async def cb_object(query: CallbackQuery) -> None:
    _, slug, back_target = query.data.split(":", 2)
    item = OBJECTS_BY_SLUG[slug]
    await send_object_detail(query.message, item, detail_back_target(back_target))
    await query.answer()


@router.callback_query(F.data.startswith("back:"))
async def cb_back(query: CallbackQuery) -> None:
    back_target = query.data.split(":", 1)[1]

    try:
        await query.message.delete()
    except TelegramAPIError:
        pass

    if back_target == "menu":
        await show_home(query.message)
    elif back_target == "top7":
        await query.message.answer("<b>ТОП-7 объектов</b>\n\nВыберите объект из списка ниже.", reply_markup=top7_keyboard())
    elif back_target == "faq":
        await query.message.answer("<b>FAQ</b>\n\nВыберите вопрос.", reply_markup=faq_keyboard())
    elif back_target == "about":
        await query.message.answer(PROJECT_TEXT, reply_markup=menu_back_keyboard())
    elif back_target.startswith("district_"):
        _, district_key, page_str = back_target.split("_")
        page = int(page_str)
        await query.message.answer(
            district_page_text(district_key, page),
            reply_markup=district_list_keyboard(district_key, page),
        )
    else:
        await show_home(query.message)

    await query.answer()


@router.callback_query(F.data.startswith("faq:"))
async def cb_faq_item(query: CallbackQuery) -> None:
    index = int(query.data.split(":", 1)[1])
    question, answer = FAQ_ITEMS[index]
    text = f"<b>{question}</b>\n\n{answer}"
    await query.message.edit_text(text, reply_markup=faq_answer_keyboard())
    await query.answer()


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Используйте меню ниже.", reply_markup=main_menu_keyboard())


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
