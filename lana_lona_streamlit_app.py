import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io


GOLD_PRICE = 4600
WORK_VYSHYVANKA = 3100
WORK_INDIVIDUAL = 3000
WORK_RING = 6100
PACKAGING = 3000
K = 13

STONE_PRICES_USD = {
    "Натуральні діаманти": {
        "1 мм": 9,
        "1.25 мм": 15,
        "1.5 мм": 24,
        "1.75 мм": 42,
        "2 мм": 55,
        "2.5 мм": 100,
        "3 мм": 220,
        "3.5 мм": 380,
        "4 мм": 800,
    },
    "Лабораторні діаманти": {
        "1 мм": 7,
        "1.25 мм": 10,
        "1.5 мм": 15,
        "1.75 мм": 30,
        "2 мм": 30,
        "2.5 мм": 60,
        "3 мм": 140,
        "3.5 мм": 210,
        "4 мм": 390,
    },
    "Муасаніти": {
        "1 мм": 5,
        "1.25 мм": 7,
        "1.5 мм": 9,
        "1.75 мм": 14,
        "2 мм": 16,
        "2.5 мм": 30,
        "3 мм": 60,
        "3.5 мм": 104,
        "4 мм": 154,
    },
}


def get_usd_rate():
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        data = requests.get(url, timeout=5).json()

        for item in data:
            if item.get("cc") == "USD":
                return float(item.get("rate"))
    except Exception:
        pass

    return 44.5


def money(value):
    return f"{value:,.0f}".replace(",", " ")


def money100(value):
    value = round(value / 100) * 100
    return f"{value:,.0f}".replace(",", " ")


def calc_weight(size, width, thickness):
    w = width / 10
    t = thickness / 10
    length = ((size * 3.14) / 10) + (thickness / 10) * 3
    return length * w * t * K


def get_work_price(product_type, design=None):
    if product_type == "Каблучка":
        return WORK_RING

    if design == "Вишиванка":
        return WORK_VYSHYVANKA

    return WORK_INDIVIDUAL


def get_stone_cost_by_type(stone_type, stone_size, qty, usd_rate):
    if qty <= 0:
        return 0, 0

    price_usd = STONE_PRICES_USD[stone_type][stone_size]
    total_usd = price_usd * qty
    total_uah = total_usd * usd_rate

    return total_usd, total_uah


def make_inserts_text(main_size, main_qty, small_size, small_qty):
    parts = []

    if main_qty > 0:
        parts.append(f"{main_size} - {main_qty} шт")

    if small_qty > 0:
        parts.append(f"{small_size} - {small_qty} шт")

    return "; ".join(parts) if parts else "не додано"




def get_font(size, bold=False):
    """Підбирає шрифт, який нормально підтримує українську мову."""
    font_paths = []

    # 1) Часто є на Streamlit Cloud / Linux
    if bold:
        font_paths += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ]
    else:
        font_paths += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]

    # 2) Якщо є matplotlib — він майже завжди має DejaVu Sans всередині
    try:
        import matplotlib.font_manager as fm
        font_paths.append(fm.findfont("DejaVu Sans", fallback_to_default=True))
    except Exception:
        pass

    # 3) Локальні назви
    font_paths += [
        "DejaVuSans.ttf",
        "DejaVuSerif.ttf",
        "Arial.ttf",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue

    return ImageFont.load_default()


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def draw_center(draw, text, y, font, fill, canvas_width):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (canvas_width - (bbox[2] - bbox[0])) / 2
    draw.text((x, y), text, font=font, fill=fill)


def wrap_text(draw, text, font, max_width):
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def remove_light_background(img):
    """Робить білий/світлий фон прозорим, щоб фото лягало на чорний фон."""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]

            # Білий або майже білий фон
            if r > 225 and g > 225 and b > 225:
                pixels[x, y] = (r, g, b, 0)
            # Дуже світло-сірий фон
            elif r > 210 and g > 210 and b > 210 and abs(r - g) < 18 and abs(g - b) < 18:
                pixels[x, y] = (r, g, b, 0)

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    return img



def fit_font(draw, text, start_size, max_width, bold=False, min_size=24):
    """Підбирає найбільший шрифт, щоб текст вліз у ширину."""
    size = start_size
    while size >= min_size:
        font = get_font(size, bold=bold)
        lines = wrap_text(draw, text, font, max_width)
        if all(text_width(draw, line, font) <= max_width for line in lines):
            return font, lines
        size -= 2
    font = get_font(min_size, bold=bold)
    return font, wrap_text(draw, text, font, max_width)


def draw_text_center(draw, text, y, font, fill, canvas_width, stroke=0):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    x = (canvas_width - (bbox[2] - bbox[0])) / 2
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke,
        stroke_fill="#000000",
    )


def draw_text_box_center(draw, text, center_x, y, font, fill, max_width, max_lines=2, line_gap=8):
    lines = wrap_text(draw, text, font, max_width)
    yy = y
    for line in lines[:max_lines]:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=1)
        x = center_x - (bbox[2] - bbox[0]) / 2
        draw.text(
            (x, yy),
            line,
            font=font,
            fill=fill,
            stroke_width=1,
            stroke_fill="#000000",
        )
        yy += (bbox[3] - bbox[1]) + line_gap


def generate_client_image(uploaded_image, poster_data):
    # Великий формат для чіткого тексту в Instagram / месенджерах
    W, H = 1080, 1350
    bg = Image.new("RGB", (W, H), "#020202")
    draw = ImageDraw.Draw(bg)

    copper = "#e09a62"
    white = "#f7f7f7"
    muted = "#9c9c9c"
    line_color = "#c27a4a"

    title = poster_data.get("title", "Індивідуальна модель обручок")
    gold = poster_data.get("gold", "Біле родоване золото 585 проби")
    sizes = poster_data.get("sizes", "")
    widths = poster_data.get("widths", "")
    coating = poster_data.get("coating", "")
    weight = poster_data.get("weight", "")
    price = poster_data.get("price", "")
    inserts = poster_data.get("inserts", "")

    # Прибираємо emoji, бо вони часто ламаються на серверних шрифтах Pillow
    title_clean = (
        title.replace("⚜️", "")
        .replace("💍", "")
        .replace("💎", "")
        .strip()
        .upper()
    )
    gold_clean = gold.replace("💍", "").strip().upper()

    # Шрифти більші, щоб текст нормально читався
    title_font, title_lines = fit_font(draw, title_clean, 72, 980, bold=False, min_size=44)
    subtitle_font, subtitle_lines = fit_font(draw, gold_clean, 40, 920, bold=False, min_size=30)
    label_font = get_font(30, bold=True)
    value_font = get_font(34, bold=False)
    price_label_font = get_font(42, bold=True)
    price_font = get_font(82, bold=False)
    brand_font = get_font(38, bold=False)

    # Заголовок
    y = 42
    for line in title_lines[:2]:
        draw_text_center(draw, line, y, title_font, copper, W, stroke=1)
        y += 78

    subtitle_y = max(y + 8, 185)
    for line in subtitle_lines[:1]:
        draw_text_center(draw, line, subtitle_y, subtitle_font, white, W, stroke=1)

    # Фото виробу: прибираємо білий фон і кладемо на чорний
    uploaded_image.seek(0)
    img = Image.open(uploaded_image)
    img = remove_light_background(img)
    img.thumbnail((850, 590), Image.LANCZOS)

    img_x = (W - img.width) // 2
    img_y = 285
    bg.paste(img, (img_x, img_y), img)

    # Нижній блок характеристик
    y_top = 900

    gold_value = (
        gold.replace("Біле родоване ", "")
        .replace(" проби 💍", "")
        .replace(" проби", "")
        .strip()
    )
    sizes_value = sizes.replace("Розміри: ", "").replace("Розмір: ", "").strip()
    widths_value = widths.replace("Ширина: ", "").strip()
    coating_value = coating.replace("Покриття: ", "").strip()
    weight_value = weight.replace("Середня вага виробу: ", "").strip()
    inserts_value = inserts.replace("Вставки: ", "").strip()

    cols = [
        ("ЗОЛОТО", gold_value),
        ("РОЗМІРИ" if "та" in sizes_value else "РОЗМІР", sizes_value),
        ("ШИРИНА", widths_value),
        ("ПОКРИТТЯ", coating_value),
        ("ВАГА", weight_value),
    ]

    if inserts_value and inserts_value != "не додано":
        cols.append(("ВСТАВКИ", inserts_value))

    col_w = W / len(cols)

    for i, (label, value) in enumerate(cols):
        x_center = col_w * i + col_w / 2

        # для 6 колонок трохи зменшуємо, але все одно крупно
        lf = get_font(26 if len(cols) == 6 else 30, bold=True)
        vf = get_font(30 if len(cols) == 6 else 34, bold=False)

        label_w = text_width(draw, label, lf)
        draw.text(
            (x_center - label_w / 2, y_top),
            label,
            font=lf,
            fill=copper,
            stroke_width=1,
            stroke_fill="#000000",
        )

        draw_text_box_center(
            draw,
            value,
            x_center,
            y_top + 52,
            vf,
            white,
            col_w - 20,
            max_lines=2,
            line_gap=8,
        )

        if i > 0:
            x_line = int(col_w * i)
            draw.line((x_line, y_top - 10, x_line, y_top + 135), fill=line_color, width=3)

    # Лінія та ціна
    draw.line((90, 1085, 990, 1085), fill=line_color, width=3)
    draw_text_center(draw, "СЕРЕДНЯ ВАРТІСТЬ ВИРОБУ:", 1130, price_label_font, copper, W, stroke=1)
    draw_text_center(draw, f"{price} грн", 1195, price_font, copper, W, stroke=1)
    draw_text_center(draw, "LANA & LONA", 1290, brand_font, muted, W, stroke=1)

    buffer = io.BytesIO()
    bg.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def calculate_wedding_rings(data):
    usd_rate = get_usd_rate()

    size_1 = data["size_1"]
    width_1 = data["width_1"]
    thickness_1 = data["thickness_1"]

    use_second_ring = data.get("use_second_ring", True)

    size_2 = data["size_2"] if use_second_ring else 0
    width_2 = data["width_2"] if use_second_ring else 0
    thickness_2 = data["thickness_2"] if use_second_ring else 0

    design = data["design"]
    coating_usd = data["coating_usd"]
    coating_uah = coating_usd * usd_rate
    engraving = data["engraving"]
    delivery = data["delivery"]
    discount_percent = data["discount_percent"]

    ring_stone_enabled = data["ring_stone_enabled"]
    ring_stone_size = data["ring_stone_size"]
    ring_stone_qty = data["ring_stone_qty"] if ring_stone_enabled else 0

    manual_weight_1 = data.get("manual_weight_1", 0)
    manual_weight_2 = data.get("manual_weight_2", 0)

    auto_weight_1 = calc_weight(size_1, width_1, thickness_1)
    auto_weight_2 = calc_weight(size_2, width_2, thickness_2) if use_second_ring else 0

    if manual_weight_1 > 0:
        weight_1 = manual_weight_1
        weight_note_1 = "Вага виробу 1 задана вручну"
    else:
        weight_1 = auto_weight_1
        weight_note_1 = "Вага виробу 1 розрахована автоматично"

    if use_second_ring:
        if manual_weight_2 > 0:
            weight_2 = manual_weight_2
            weight_note_2 = "Вага виробу 2 задана вручну"
        else:
            weight_2 = auto_weight_2
            weight_note_2 = "Вага виробу 2 розрахована автоматично"
    else:
        weight_2 = 0
        weight_note_2 = "Друга обручка не додана"

    total_weight = weight_1 + weight_2

    work_per_gram = get_work_price("Пара обручок", design)
    work_cost = total_weight * work_per_gram
    discount = work_cost * (discount_percent / 100)
    work_after_discount = work_cost - discount
    gold_cost = total_weight * GOLD_PRICE

    base_total_without_stones = (
        gold_cost
        + work_after_discount
        + PACKAGING
        + engraving
        + coating_uah
        + delivery
    )

    stones_usd, stones_uah = get_stone_cost_by_type(
        "Натуральні діаманти",
        ring_stone_size,
        ring_stone_qty,
        usd_rate,
    )

    total = base_total_without_stones + stones_uah

    title = (
        "Індивідуальна модель обручок «Вишиванка» ⚜️"
        if design == "Вишиванка"
        else "Індивідуальна модель обручок ⚜️"
    )

    coating_client = "Без покриття" if coating_usd == 0 else "Родій"

    inserts_text = "не додано"
    if ring_stone_qty > 0:
        inserts_text = f"{ring_stone_size} - {ring_stone_qty} шт"

    second_weight_text = ""
    if use_second_ring:
        second_weight_text = f"""
{weight_note_2}:
{weight_2:.2f} г
"""

    if use_second_ring:
        client_sizes_text = f"Розміри: {size_1:g} та {size_2:g}"
        client_width_text = f"Ширина: {width_1:g} мм та {width_2:g} мм"
    else:
        client_sizes_text = f"Розмір: {size_1:g}"
        client_width_text = f"Ширина: {width_1:g} мм"

    technical_text = f"""Курс USD: {usd_rate:.2f} грн

Тип виробу:
Пара обручок

{weight_note_1}:
{weight_1:.2f} г
{second_weight_text}
Загальна вага:
{total_weight:.2f} г

Золото:
{money(gold_cost)} грн

Робота:
{money(work_cost)} грн

Знижка:
-{money(discount)} грн

Робота після знижки:
{money(work_after_discount)} грн

Упаковка:
{money(PACKAGING)} грн

Гравіювання:
{money(engraving)} грн

Покриття:
{money(coating_uah)} грн

Діаманти / каміння:
{money(stones_uah)} грн ({stones_usd}$)

Доставка:
{money(delivery)} грн

=====================
ДО СПЛАТИ:
{money(total)} грн
"""

    client_text = f"""{title}

Біле родоване золото 585 проби 💍
{client_sizes_text}
{client_width_text}
Покриття: {coating_client}
Середня вага виробу: {total_weight:.1f} г
"""

    if ring_stone_qty > 0:
        variant_totals = {}

        for stone_type in STONE_PRICES_USD.keys():
            _, stone_uah_variant = get_stone_cost_by_type(
                stone_type,
                ring_stone_size,
                ring_stone_qty,
                usd_rate,
            )
            variant_totals[stone_type] = base_total_without_stones + stone_uah_variant

        client_text += f"""Вставки: {inserts_text}

Середня вартість виробу:
• з натуральними діамантами:
{money100(variant_totals["Натуральні діаманти"])} грн 💎
• з лабораторними діамантами:
{money100(variant_totals["Лабораторні діаманти"])} грн 💎
• з муасанітами:
{money100(variant_totals["Муасаніти"])} грн 💎
"""
    else:
        client_text += f"""
Середня вартість виробу:
{money100(total)} грн 💎
"""

    poster_data = {
        "title": title,
        "gold": "Біле родоване золото 585 проби 💍",
        "sizes": client_sizes_text,
        "widths": client_width_text,
        "coating": f"Покриття: {coating_client}",
        "weight": f"Середня вага виробу: {total_weight:.1f} г",
        "price": money100(total),
    }

    return technical_text, client_text, poster_data


def calculate_ring(data):
    usd_rate = get_usd_rate()

    size = data["size"]
    width = data["width"]
    thickness = data["thickness"]
    coating_usd = data["coating_usd"]
    coating_uah = coating_usd * usd_rate
    engraving = data["engraving"]
    delivery = data["delivery"]
    discount_percent = data["discount_percent"]
    main_size = data["main_size"]
    main_qty = data["main_qty"]
    small_size = data["small_size"]
    small_qty = data["small_qty"]
    manual_weight = data.get("manual_weight", 0)

    auto_weight = calc_weight(size, width, thickness)

    if manual_weight > 0:
        total_weight = manual_weight
        weight_note = "Вага задана вручну"
    else:
        total_weight = auto_weight
        weight_note = "Вага розрахована автоматично"

    weight_1 = total_weight

    work_per_gram = get_work_price("Каблучка")
    work_cost = total_weight * work_per_gram
    discount = work_cost * (discount_percent / 100)
    work_after_discount = work_cost - discount
    gold_cost = total_weight * GOLD_PRICE

    base_total_without_stones = (
        gold_cost
        + work_after_discount
        + PACKAGING
        + engraving
        + coating_uah
        + delivery
    )

    main_usd, main_uah = get_stone_cost_by_type(
        "Натуральні діаманти",
        main_size,
        main_qty,
        usd_rate,
    )

    small_usd, small_uah = get_stone_cost_by_type(
        "Натуральні діаманти",
        small_size,
        small_qty,
        usd_rate,
    )

    stones_usd = main_usd + small_usd
    stones_uah = main_uah + small_uah
    total = base_total_without_stones + stones_uah

    coating_client = "Без покриття" if coating_usd == 0 else "Родій"
    inserts_text = make_inserts_text(main_size, main_qty, small_size, small_qty)

    technical_text = f"""Курс USD: {usd_rate:.2f} грн

Тип виробу:
Каблучка

{weight_note}:
{weight_1:.2f} г

Загальна вага:
{total_weight:.2f} г

Золото:
{money(gold_cost)} грн

Робота:
{money(work_cost)} грн

Знижка:
-{money(discount)} грн

Робота після знижки:
{money(work_after_discount)} грн

Упаковка:
{money(PACKAGING)} грн

Гравіювання:
{money(engraving)} грн

Покриття:
{money(coating_uah)} грн

Діаманти / каміння:
{money(stones_uah)} грн ({stones_usd}$)

Доставка:
{money(delivery)} грн

=====================
ДО СПЛАТИ:
{money(total)} грн
"""

    variant_totals = {}

    for stone_type in STONE_PRICES_USD.keys():
        _, main_uah_variant = get_stone_cost_by_type(
            stone_type,
            main_size,
            main_qty,
            usd_rate,
        )

        _, small_uah_variant = get_stone_cost_by_type(
            stone_type,
            small_size,
            small_qty,
            usd_rate,
        )

        variant_totals[stone_type] = (
            base_total_without_stones
            + main_uah_variant
            + small_uah_variant
        )

    client_text = f"""Каблучка індивідуального дизайну ⚜️

Біле родоване золото 585 проби 💍
Розмір: {size:g}
Ширина: {width:g} мм
Покриття: {coating_client}
Середня вага виробу: {total_weight:.1f} г
Вставки: {inserts_text}

Середня вартість виробу:
• з натуральними діамантами:
{money100(variant_totals["Натуральні діаманти"])} грн 💎
• з лабораторними діамантами:
{money100(variant_totals["Лабораторні діаманти"])} грн 💎
• з муасанітами:
{money100(variant_totals["Муасаніти"])} грн 💎
"""

    poster_data = {
        "title": "Каблучка індивідуального дизайну ⚜️",
        "gold": "Біле родоване золото 585 проби 💍",
        "sizes": f"Розмір: {size:g}",
        "widths": f"Ширина: {width:g} мм",
        "coating": f"Покриття: {coating_client}",
        "weight": f"Середня вага виробу: {total_weight:.1f} г",
        "price": money100(total),
    }

    return technical_text, client_text, poster_data


st.set_page_config(page_title="Калькулятор Lana & Lona", layout="wide")

if "screen" not in st.session_state:
    st.session_state.screen = "start"

st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        font-size: 34px;
        font-weight: 700;
        margin-top: 40px;
    }
    textarea {
        font-size: 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def go_start():
    st.session_state.screen = "start"


def go_wedding():
    st.session_state.screen = "wedding"


def go_ring():
    st.session_state.screen = "ring"


if st.session_state.screen == "start":
    st.markdown(
        '<div class="main-title">Що потрібно прорахувати?</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.button("Обручки", use_container_width=True, on_click=go_wedding)
        st.button("Каблучка", use_container_width=True, on_click=go_ring)


elif st.session_state.screen == "wedding":
    st.button("← Назад", on_click=go_start)
    st.title("Калькулятор обручок")

    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("Дані для прорахунку")

        design = st.selectbox("Дизайн", ["Вишиванка", "Індивідуальний"])

        st.markdown("### Обручка 1")
        size_1 = st.number_input("Розмір 1", min_value=1.0, value=16.0, step=0.5)
        width_1 = st.number_input("Ширина 1, мм", min_value=0.1, value=5.0, step=0.1)
        thickness_1 = st.number_input("Товщина 1, мм", min_value=0.1, value=1.2, step=0.1)

        use_second_ring = st.checkbox("Додати другу обручку", value=True)

        if use_second_ring:
            st.markdown("### Обручка 2")
            size_2 = st.number_input("Розмір 2", min_value=1.0, value=19.0, step=0.5)
            width_2 = st.number_input("Ширина 2, мм", min_value=0.1, value=5.0, step=0.1)
            thickness_2 = st.number_input("Товщина 2, мм", min_value=0.1, value=1.2, step=0.1)
        else:
            size_2 = 0.0
            width_2 = 0.0
            thickness_2 = 0.0

        st.markdown("### Вставки каміння")
        stone_sizes = list(STONE_PRICES_USD["Натуральні діаманти"].keys())

        ring_stone_enabled = st.checkbox("Додати діаманти в обручку")
        ring_stone_ring = st.selectbox(
            "В яку обручку додати",
            [1, 2] if use_second_ring else [1],
            disabled=not ring_stone_enabled,
        )
        ring_stone_size = st.selectbox(
            "Розмір діаманта",
            stone_sizes,
            index=1,
            disabled=not ring_stone_enabled,
        )
        ring_stone_qty = st.number_input(
            "Кількість діамантів",
            min_value=0,
            value=0,
            step=1,
            disabled=not ring_stone_enabled,
        )

        st.markdown("### Додатково")
        discount_percent = st.selectbox("Знижка, %", [0, 7, 10, 15, 20])
        coating_usd = st.selectbox("Покриття, $", [0, 50, 100, 200])
        engraving = st.selectbox("Гравіювання, грн", [0, 800, 1500])
        delivery = st.number_input("Доставка, грн", min_value=0.0, value=0.0, step=100.0)

        calculate_btn = st.button("РОЗРАХУВАТИ", use_container_width=True)

    with right:
        current_auto_weight_1 = calc_weight(size_1, width_1, thickness_1)
        current_auto_weight_2 = calc_weight(size_2, width_2, thickness_2) if use_second_ring else 0.0

        if calculate_btn:
            st.session_state.wedding_manual_weight_1 = 0.0
            st.session_state.wedding_manual_weight_2 = 0.0

            technical_text, client_text, poster_data = calculate_wedding_rings({
                "design": design,
                "use_second_ring": use_second_ring,
                "size_1": size_1,
                "width_1": width_1,
                "thickness_1": thickness_1,
                "manual_weight_1": 0.0,
                "size_2": size_2,
                "width_2": width_2,
                "thickness_2": thickness_2,
                "manual_weight_2": 0.0,
                "discount_percent": discount_percent,
                "coating_usd": coating_usd,
                "engraving": engraving,
                "delivery": delivery,
                "ring_stone_enabled": ring_stone_enabled,
                "ring_stone_ring": ring_stone_ring,
                "ring_stone_size": ring_stone_size,
                "ring_stone_qty": ring_stone_qty,
            })

            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.poster_data = poster_data

        st.subheader("📊 Технічний розрахунок")
        st.caption("Тут менеджер може виправити вагу вручну і перерахувати ціну.")

        if use_second_ring:
            weight_col1, weight_col2 = st.columns(2)

            with weight_col1:
                manual_weight_1_right = st.number_input(
                    "Вага виробу 1, г",
                    min_value=0.0,
                    value=st.session_state.get("wedding_manual_weight_1", 0.0) or current_auto_weight_1,
                    step=0.1,
                    format="%.2f",
                    key="wedding_weight_input_1",
                )

            with weight_col2:
                manual_weight_2_right = st.number_input(
                    "Вага виробу 2, г",
                    min_value=0.0,
                    value=st.session_state.get("wedding_manual_weight_2", 0.0) or current_auto_weight_2,
                    step=0.1,
                    format="%.2f",
                    key="wedding_weight_input_2",
                )
        else:
            manual_weight_1_right = st.number_input(
                "Вага виробу, г",
                min_value=0.0,
                value=st.session_state.get("wedding_manual_weight_1", 0.0) or current_auto_weight_1,
                step=0.1,
                format="%.2f",
                key="wedding_weight_input_1",
            )
            manual_weight_2_right = 0.0

        if st.button(
            "ПЕРЕРАХУВАТИ ПО ВАЗІ",
            use_container_width=True,
            key="recalculate_wedding_weight",
        ):
            st.session_state.wedding_manual_weight_1 = manual_weight_1_right
            st.session_state.wedding_manual_weight_2 = manual_weight_2_right

            technical_text, client_text, poster_data = calculate_wedding_rings({
                "design": design,
                "use_second_ring": use_second_ring,
                "size_1": size_1,
                "width_1": width_1,
                "thickness_1": thickness_1,
                "manual_weight_1": manual_weight_1_right,
                "size_2": size_2,
                "width_2": width_2,
                "thickness_2": thickness_2,
                "manual_weight_2": manual_weight_2_right,
                "discount_percent": discount_percent,
                "coating_usd": coating_usd,
                "engraving": engraving,
                "delivery": delivery,
                "ring_stone_enabled": ring_stone_enabled,
                "ring_stone_ring": ring_stone_ring,
                "ring_stone_size": ring_stone_size,
                "ring_stone_qty": ring_stone_qty,
            })

            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.poster_data = poster_data

        st.text_area(
            "Технічний текст",
            value=st.session_state.get("technical_text", ""),
            height=420,
        )

        st.subheader("📋 Текст для клієнта")
        client_text = st.session_state.get("client_text", "")
        st.code(client_text, language=None)
        st.caption("Натисни кнопку у правому верхньому куті блоку, щоб скопіювати текст.")

        st.subheader("🖼️ Картинка для клієнта")
        uploaded_product_image = st.file_uploader(
            "Завантаж фото виробу",
            type=["jpg", "jpeg", "png"],
            key="ring_product_image",
        )

        if uploaded_product_image and st.session_state.get("poster_data"):
            if st.button("Згенерувати картинку для клієнта", use_container_width=True, key="generate_ring_poster"):
                image_buffer = generate_client_image(
                    uploaded_product_image,
                    st.session_state.poster_data,
                )
                st.session_state.generated_client_image = image_buffer.getvalue()

        if st.session_state.get("generated_client_image"):
            st.image(st.session_state.generated_client_image, use_container_width=True)
            st.download_button(
                "Завантажити картинку",
                data=st.session_state.generated_client_image,
                file_name="lana_lona_offer.png",
                mime="image/png",
                use_container_width=True,
                key="download_ring_poster",
            )

        st.subheader("🖼️ Картинка для клієнта")
        uploaded_product_image = st.file_uploader(
            "Завантаж фото виробу",
            type=["jpg", "jpeg", "png"],
            key="wedding_product_image",
        )

        if uploaded_product_image and st.session_state.get("poster_data"):
            if st.button("Згенерувати картинку для клієнта", use_container_width=True, key="generate_wedding_poster"):
                image_buffer = generate_client_image(
                    uploaded_product_image,
                    st.session_state.poster_data,
                )
                st.session_state.generated_client_image = image_buffer.getvalue()

        if st.session_state.get("generated_client_image"):
            st.image(st.session_state.generated_client_image, use_container_width=True)
            st.download_button(
                "Завантажити картинку",
                data=st.session_state.generated_client_image,
                file_name="lana_lona_offer.png",
                mime="image/png",
                use_container_width=True,
                key="download_wedding_poster",
            )


elif st.session_state.screen == "ring":
    st.button("← Назад", on_click=go_start)
    st.title("Калькулятор каблучки")

    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("Дані для прорахунку")
        st.info("Для каблучки робота завжди рахується по 6100 грн/г. Дизайн тут не вибирається.")

        size = st.number_input("Розмір", min_value=1.0, value=16.0, step=0.5)
        width = st.number_input("Ширина, мм", min_value=0.1, value=2.5, step=0.1)
        thickness = st.number_input("Товщина, мм", min_value=0.1, value=1.2, step=0.1)

        st.markdown("### Вставки")
        stone_sizes = list(STONE_PRICES_USD["Натуральні діаманти"].keys())

        main_size = st.selectbox("Основний діамант — розмір", stone_sizes, index=0)
        main_qty = st.number_input("Основний діамант — к-сть", min_value=0, value=0, step=1)

        small_size = st.selectbox("Малі діаманти — розмір", stone_sizes, index=0)
        small_qty = st.number_input("Малі діаманти — к-сть", min_value=0, value=0, step=1)

        st.markdown("### Додатково")
        discount_percent = st.selectbox("Знижка, %", [0, 7, 10, 15, 20])
        coating_usd = st.selectbox("Покриття, $", [0, 50, 100, 200])
        engraving = st.selectbox("Гравіювання, грн", [0, 800, 1500])
        delivery = st.number_input("Доставка, грн", min_value=0.0, value=0.0, step=100.0)

        calculate_btn = st.button("РОЗРАХУВАТИ", use_container_width=True)

    with right:
        current_auto_weight = calc_weight(size, width, thickness)

        if calculate_btn:
            st.session_state.ring_manual_weight = 0.0

            technical_text, client_text, poster_data = calculate_ring({
                "size": size,
                "width": width,
                "thickness": thickness,
                "manual_weight": 0.0,
                "main_size": main_size,
                "main_qty": main_qty,
                "small_size": small_size,
                "small_qty": small_qty,
                "discount_percent": discount_percent,
                "coating_usd": coating_usd,
                "engraving": engraving,
                "delivery": delivery,
            })

            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.poster_data = poster_data

        st.subheader("📊 Технічний розрахунок")
        st.caption("Тут менеджер може виправити вагу вручну і перерахувати ціну.")

        manual_weight_right = st.number_input(
            "Вага виробу, г",
            min_value=0.0,
            value=st.session_state.get("ring_manual_weight", 0.0) or current_auto_weight,
            step=0.1,
            format="%.2f",
            key="ring_weight_input",
        )

        if st.button(
            "ПЕРЕРАХУВАТИ ПО ВАГІ",
            use_container_width=True,
            key="recalculate_ring_weight",
        ):
            st.session_state.ring_manual_weight = manual_weight_right

            technical_text, client_text, poster_data = calculate_ring({
                "size": size,
                "width": width,
                "thickness": thickness,
                "manual_weight": manual_weight_right,
                "main_size": main_size,
                "main_qty": main_qty,
                "small_size": small_size,
                "small_qty": small_qty,
                "discount_percent": discount_percent,
                "coating_usd": coating_usd,
                "engraving": engraving,
                "delivery": delivery,
            })

            st.session_state.technical_text = technical_text
            st.session_state.client_text = client_text
            st.session_state.poster_data = poster_data

        st.text_area(
            "Технічний текст",
            value=st.session_state.get("technical_text", ""),
            height=420,
        )

        st.subheader("📋 Текст для клієнта")
        client_text = st.session_state.get("client_text", "")
        st.code(client_text, language=None)
        st.caption("Натисни кнопку у правому верхньому куті блоку, щоб скопіювати текст.")
