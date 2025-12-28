#!/usr/bin/env python3
"""
Скрипт для импорта меню из PDF.
Запуск: python scripts/import_menu.py
"""

import asyncio
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete
from app.database import async_session, init_db
from app.models.category import Category
from app.models.dish import Dish


def slugify(text):
    """Простая транслитерация для slug."""
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': '-', '/': '-', '«': '', '»': '', '"': '', "'": '', ',': '',
        '.': '', '(': '', ')': '', ':': '', '+': '-plus-'
    }
    text = text.lower()
    result = ''
    for char in text:
        result += translit.get(char, char)
    # Убираем двойные дефисы и лишние символы
    result = re.sub(r'[^a-z0-9-]', '', result)
    result = re.sub(r'-+', '-', result)
    result = result.strip('-')
    return result[:100]


# Данные меню из PDF
MENU_DATA = {
    "Авторская бриошь": [
        {"name": "С рваной говядиной, руколой, маринованным луком и огурцом", "weight": "335 гр.", "price": 695},
        {"name": '"Любимая утка Канта" под соусом из свежего базилика', "weight": "295 гр.", "price": 655},
        {"name": "Рубанина из пеламиды под лимонно-горчичной заправкой", "weight": "230 гр.", "price": 675},
        {"name": "С ароматным филе скумбрии г/к под пикантным соусом из свежей кинзы", "weight": "325 гр.", "price": 655},
        {"name": "С нежным филе сельди и маринованным луком под лимонно-горчичной заправкой", "weight": "275 гр.", "price": 535},
        {"name": "Сет бриошей", "weight": "200 гр.", "price": 595},
    ],
    "Закуски/Салаты": [
        {"name": "Риет из филе скумбрии г/к с поджаренным хлебом и свежим огурцом", "weight": "70/40/40 гр.", "price": 565},
        {"name": "Паштет из куриной печени с вяленой клюквой и домашним вареньем", "weight": "80/30/80 гр.", "price": 435},
        {"name": "Микс салат из свежих овощей", "weight": "190 гр.", "price": 465, "description": "Заправка на выбор: бальзамик или соус из свежего базилика"},
        {"name": "Микс салат с фермерской брынзой", "weight": "210 гр.", "price": 515, "description": "Заправка на выбор: бальзамик или соус из свежего базилика"},
        {"name": "Микс салат с филе утки и маринованным печеным перцем", "weight": "220 гр.", "price": 585, "description": "Заправка на выбор: бальзамик или соус из свежего базилика"},
        {"name": 'Хот дог "Немецкий"', "weight": "200 гр.", "price": 375},
        {"name": "Хот дог с двумя колбасками и тушеной квашеной капустой", "weight": "220 гр.", "price": 385},
    ],
    "Супы": [
        {"name": "Похлебка прусская на местной рыбе", "weight": "300/50 гр.", "price": 515},
        {"name": "Суп немецкий на говяжьем бульоне с колбасками и грибами", "weight": "300/50 гр.", "price": 475},
        {"name": "Тыквенный суп с семечками", "weight": "300/5 гр.", "price": 365},
        {"name": "Тыквенный суп с беконом", "weight": "300/40 гр.", "price": 425},
    ],
    "Горячее": [
        {"name": 'Клопсы "Балтийские" из местной рыбы под сливочным соусом с каперсами и картофелем', "weight": "390 гр.", "price": 755},
        {"name": 'Клопсы "Де Прусс" из оленины и свинины под соусом из белых грибов с картофелем', "weight": "390 гр.", "price": 725},
        {"name": "Филе скумбрии г/к под пикантным соусом с картофельным пюре и салатом из маринованной свеклы", "weight": "340 гр.", "price": 675},
        {"name": "Кёнигсбергские колбаски (свинина) гарнир на выбор", "weight": "390 гр.", "price": 535},
        {"name": "Нюрнбергские колбаски (белые, свинина) гарнир на выбор", "weight": "360 гр.", "price": 575},
        {"name": "Немецкие колбаски XXL (свинина/курица) с капустой и картофелем", "weight": "560 гр.", "price": 725},
        {"name": 'Ребра "Пивные" копчено-томленые с капустой и картофелем', "weight": "540 гр.", "price": 695},
        {"name": "Бургер с фермерской говядиной", "weight": "380 гр.", "price": 655},
        {"name": "Бургер куриный под соусом из свежего базилика", "weight": "275 гр.", "price": 575},
    ],
    "Бранчи": [
        {"name": 'Баварский бранч (Ребра "Пивные" + 0,3 разливного Де Прусс)', "price": 825},
        {"name": "Немецкий бранч (Кёнигсбергские колбаски + 0,3 разливного Де Прусс)", "price": 695},
    ],
    "Выпечка": [
        {"name": "Брецель с солью", "price": 175},
        {"name": "Круассан сливочный", "price": 150},
        {"name": "Круассан с нутеллой", "price": 185},
        {"name": "Булочка с кленовым сиропом и орехом пекан", "price": 195},
        {"name": "Шарлотт яблочный с мороженым", "price": 415},
        {"name": "Тыквенный пирог с мороженым", "price": 475},
        {"name": "Вишневый пирог с мороженым", "price": 325},
    ],
    "Десерты": [
        {"name": 'Панна Котта с марципаном "Королева Луиза"', "price": 275},
        {"name": "Чизкейк", "price": 375},
        {"name": 'Наполеон «не классический»', "price": 455},
        {"name": "Торт фисташка-малина", "price": 455},
        {"name": "Сырники с фермерской сметаной и домашним вареньем", "price": 395},
        {"name": "Каша дня на цельнозерновом молоке", "price": 270},
        {"name": "Каша дня на альтернативном молоке", "price": 325},
    ],
    "Напитки Б/А": [
        {"name": "Вода стекло (газ/негаз)", "weight": "0,5 л", "price": 275},
        {"name": "Свежевыжатый сок (апельсин, грейпфрут, морковь, яблоко)", "weight": "0,2/0,3 л", "price": 350, "description": "Цена за 0,2 л / 0,3 л - 350/525"},
        {"name": "Лимонад собственного производства в ассортименте", "weight": "0,4/1,2 л", "price": 325, "description": "Цена за 0,4 л / 1,2 л - 325/835"},
        {"name": "Молочный коктейль (ваниль, клубника, шоколад)", "weight": "0,3 л", "price": 350},
        {"name": "Сок стекло (яблоко/апельсин/томат)", "weight": "0,25 л", "price": 250},
        {"name": "Квас TILSITKRONE", "weight": "0,45 л", "price": 255},
        {"name": "Ред Булл", "weight": "0,33 л", "price": 295},
        {"name": "Coca-Cola/Fanta original стекло", "weight": "0,25 л", "price": 295},
    ],
    "Кофе/Чай": [
        {"name": "Американо", "price": 170},
        {"name": "Эспрессо", "price": 170},
        {"name": "Доппио", "price": 190},
        {"name": "Капучино", "weight": "0,2/0,3 л", "price": 180, "description": "Цена за 0,2 л / 0,3 л - 180/200"},
        {"name": "Латте", "weight": "0,2/0,3 л", "price": 190, "description": "Цена за 0,2 л / 0,3 л - 190/210"},
        {"name": "Флэт Уайт", "weight": "0,25 л", "price": 235},
        {"name": "Раф", "weight": "0,3 л", "price": 290},
        {"name": "Какао сладкий/горький", "weight": "0,15 л", "price": 270},
        {"name": "Горячий шоколад", "weight": "0,15 л", "price": 285},
        {"name": "Чай в ассортименте (чайник)", "weight": "0,6 л", "price": 385},
        {"name": "Чай авторский: облепиховый, ягодный", "weight": "0,6 л", "price": 595},
    ],
    "Кант Вайн": [
        {"name": "Кант Вайн", "weight": "0,3/0,4 л", "price": 400, "description": "Цена за 0,3 л / 0,4 л - 400/450"},
        {"name": "Кант Вайн б/а", "weight": "0,35 л", "price": 325},
    ],
    "Пиво": [
        {"name": 'Разливное "ДЕ ПРУСС" Красное/Светлое (Калининград)', "weight": "0,3/0,5 л", "price": 245, "description": "Цена за 0,3 л / 0,5 л - 245/395"},
        {"name": "Биржалис бут. Красное/Светлое (Калининград)", "weight": "0,5 л", "price": 335},
        {"name": "Ландбир темное бут. (Германия)", "weight": "0,5 л", "price": 685},
        {"name": "Ешенбахер бут. неф. (Германия)", "weight": "0,5 л", "price": 585},
        {"name": '"ФРАНЦ ЕЗЕФ" бут. светлое (Германия)', "weight": "0,5 л", "price": 585},
        {"name": "Раухбир Вайцен копченое (Германия)", "weight": "0,5 л", "price": 785},
        {"name": "Сидр в ассортименте (Алтайский край)", "weight": "0,45 л", "price": 400},
        {"name": "Пиво б/а Параграф 77 TILSITKRONE (Калининград)", "weight": "0,45 л", "price": 295},
    ],
    "Снеки": [
        {"name": "Картофельная соломка", "weight": "50 г", "price": 295},
        {"name": "Ассорти орешков (кешью, миндаль, арахис XXL)", "weight": "100 г", "price": 375},
        {"name": "Уши свиные", "weight": "65 г", "price": 255},
        {"name": "Куриные чипсы", "weight": "50 г", "price": 295},
        {"name": "Вяленая оленина", "weight": "50 г", "price": 455},
    ],
}


async def import_menu():
    """Импорт всего меню в базу данных."""
    await init_db()

    async with async_session() as session:
        # Удаляем старые данные
        print("Удаляем старые данные...")
        await session.execute(delete(Dish))
        await session.execute(delete(Category))
        await session.commit()

        print("Создаем категории и блюда...")

        sort_order = 0
        used_slugs = set()

        for category_name, dishes in MENU_DATA.items():
            sort_order += 1

            # Создаем категорию
            cat_slug = slugify(category_name)
            category = Category(
                name=category_name,
                slug=cat_slug,
                sort_order=sort_order,
                is_active=True
            )
            session.add(category)
            await session.flush()  # Получаем ID категории

            print(f"  + Категория: {category_name}")

            # Добавляем блюда
            dish_sort = 0
            for dish_data in dishes:
                dish_sort += 1

                # Генерируем уникальный slug
                base_slug = slugify(dish_data["name"])
                dish_slug = base_slug
                counter = 1
                while dish_slug in used_slugs:
                    dish_slug = f"{base_slug}-{counter}"
                    counter += 1
                used_slugs.add(dish_slug)

                dish = Dish(
                    category_id=category.id,
                    name=dish_data["name"],
                    slug=dish_slug,
                    description=dish_data.get("description"),
                    price=dish_data["price"],
                    weight=dish_data.get("weight"),
                    sort_order=dish_sort,
                    is_available=True
                )
                session.add(dish)
                print(f"    - {dish_data['name']}: {dish_data['price']} ₽")

        await session.commit()

        # Подсчет
        cat_count = await session.execute(select(Category))
        dish_count = await session.execute(select(Dish))

        print(f"\n✅ Импорт завершен!")
        print(f"   Категорий: {len(cat_count.scalars().all())}")
        print(f"   Блюд: {len(dish_count.scalars().all())}")


if __name__ == "__main__":
    asyncio.run(import_menu())
