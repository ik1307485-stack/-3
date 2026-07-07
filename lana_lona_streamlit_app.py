import streamlit as st
from tkinter import ttk, messagebox
import requests

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


def to_float(value):
    return float(value.replace(",", ".").strip())


def money(value):
    return f"{value:,.0f}".replace(",", " ")


def money100(value):
    value = round(value / 100) * 100
    return f"{value:,.0f}".replace(",", " ")


def calc_weight(size, width, thickness):
    w = width / 10
    t = thickness / 10
    length = ((size * 3.14) / 10) + (width / 10) * 3
    return length * w * t * K


def get_work_price(product_type, design):
    if product_type == "Каблучка":
        return WORK_RING
    if design == "Вишиванка":
        return WORK_VYSHYVANKA
    return WORK_INDIVIDUAL


def get_stone_cost(type_box, size_box, qty_entry, usd_rate):
    stone_type = type_box.get()
    stone_size = size_box.get()

    try:
        qty = int(qty_entry.get())
    except:
        qty = 0

    if qty <= 0:
        return 0, 0, "не додано"

    price_usd = STONE_PRICES_USD[stone_type][stone_size]
    total_usd = price_usd * qty
    total_uah = total_usd * usd_rate

    text = f"{stone_type}, {stone_size}, {qty} шт — {total_usd}$"

    return total_usd, total_uah, text


def get_stone_cost_by_type(stone_type, stone_size, qty, usd_rate):
    if qty <= 0:
        return 0, 0

    price_usd = STONE_PRICES_USD[stone_type][stone_size]
    total_usd = price_usd * qty
    total_uah = total_usd * usd_rate
    return total_usd, total_uah


def get_stone_qty(entry):
    try:
        return int(entry.get())
    except:
        return 0


def make_inserts_text(main_size, main_qty, small_size, small_qty):
    parts = []
    if main_qty > 0:
        parts.append(f"{main_size} - {main_qty} шт")
    if small_qty > 0:
        parts.append(f"{small_size} - {small_qty} шт")
    return "; ".join(parts) if parts else "не додано"


def update_mode():
    mode = product_type_var.get()

    if mode == "Пара обручок":
        pair_frame.pack(fill="x", padx=10, pady=5)
        ring_frame.pack_forget()
        stones_frame.pack_forget()
    else:
        pair_frame.pack_forget()
        ring_frame.pack(fill="x", padx=10, pady=5)
        stones_frame.pack(fill="x", padx=10, pady=5)


def calculate():
    try:
        usd_rate = get_usd_rate()

        product_type = product_type_var.get()
        design = design_var.get() if "design_var" in globals() else "Індивідуальний"

        if product_type == "Пара обручок":
            size_1 = to_float(entry_size_1.get())
            width_1 = to_float(entry_width_1.get())
            thickness_1 = to_float(entry_thickness_1.get())

            size_2 = to_float(entry_size_2.get())
            width_2 = to_float(entry_width_2.get())
            thickness_2 = to_float(entry_thickness_2.get())

            weight_1 = calc_weight(size_1, width_1, thickness_1)
            weight_2 = calc_weight(size_2, width_2, thickness_2)
            total_weight = weight_1 + weight_2

            width_text = f"{width_1:g} мм та {width_2:g} мм"
            sizes_text = f"{size_1:g} та {size_2:g}"

            stones_usd = 0
            stones_uah = 0
            inserts_text = "не додано"

        else:
            size = to_float(entry_ring_size.get())
            width = to_float(entry_ring_width.get())
            thickness = to_float(entry_ring_thickness.get())

            weight_1 = calc_weight(size, width, thickness)
            weight_2 = 0
            total_weight = weight_1

            width_text = f"{width:g} мм"
            sizes_text = f"{size:g}"

            main_size = main_stone_size_box.get()
            small_size = small_stone_size_box.get()
            main_qty = get_stone_qty(main_stone_qty_entry)
            small_qty = get_stone_qty(small_stone_qty_entry)
            inserts_text = make_inserts_text(main_size, main_qty, small_size, small_qty)

            # Для технічного розрахунку показуємо натуральні діаманти як базовий варіант
            main_usd, main_uah = get_stone_cost_by_type(
                "Натуральні діаманти", main_size, main_qty, usd_rate
            )
            small_usd, small_uah = get_stone_cost_by_type(
                "Натуральні діаманти", small_size, small_qty, usd_rate
            )

            stones_usd = main_usd + small_usd
            stones_uah = main_uah + small_uah

        delivery = to_float(entry_delivery.get()) if entry_delivery.get().strip() else 0

        coating_usd = float(coating_var.get())
        coating_uah = coating_usd * usd_rate

        engraving = int(engraving_var.get())

        work_per_gram = get_work_price(product_type, design)
        work_cost = total_weight * work_per_gram

        discount_percent = int(discount_var.get())
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

        total = base_total_without_stones + stones_uah

        if product_type == "Каблучка":
            title = "Каблучка індивідуального дизайну ⚜️"
        elif design == "Вишиванка":
            title = "Індивідуальна модель обручок «Вишиванка» ⚜️"
        else:
            title = "Індивідуальна модель обручок ⚜️"

        coating_client = "Без покриття" if coating_usd == 0 else "Родій"

        technical_text = f"""Курс USD: {usd_rate:.2f} грн

Тип виробу:
{product_type}

Вага виробу 1:
{weight_1:.2f} г

Вага виробу 2:
{weight_2:.2f} г

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

        if product_type == "Каблучка":
            variant_totals = {}

            for stone_type in STONE_PRICES_USD.keys():
                main_usd_variant, main_uah_variant = get_stone_cost_by_type(
                    stone_type, main_size, main_qty, usd_rate
                )
                small_usd_variant, small_uah_variant = get_stone_cost_by_type(
                    stone_type, small_size, small_qty, usd_rate
                )
                variant_totals[stone_type] = (
                    base_total_without_stones + main_uah_variant + small_uah_variant
                )

            client_text = f"""{title}

Біле родоване золото 585 проби 💍
Розмір: {sizes_text}
Ширина: {width_text}
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
        else:
            client_text = f"""{title}

Біле родоване золото 585 проби 💍
Розміри: {sizes_text}
Ширина: {width_text}
Покриття: {coating_client}
Середня вага виробу: {total_weight:.1f} г

Середня вартість виробу:
{money100(total)} грн 💎
"""

        technical_output.delete("1.0", tk.END)
        technical_output.insert(tk.END, technical_text)

        client_output.delete("1.0", tk.END)
        client_output.insert(tk.END, client_text)

    except Exception as e:
        messagebox.showerror("Помилка", str(e))


def copy_client_text():
    text = client_output.get("1.0", tk.END)
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo("Готово", "Текст для клієнта скопійовано")



def build_calculator_interface(default_product_type):
    global pair_frame, ring_frame, stones_frame, product_type_var, design_var, entry_size_1, entry_width_1, entry_thickness_1, entry_size_2, entry_width_2, entry_thickness_2, entry_ring_size, entry_ring_width, entry_ring_thickness, main_stone_type_var, main_stone_type_box, main_stone_size_var, main_stone_size_box, main_stone_qty_entry, small_stone_type_var, small_stone_type_box, small_stone_size_var, small_stone_size_box, small_stone_qty_entry, discount_var, coating_var, engraving_var, entry_delivery, technical_output, client_output

    root.geometry("1050x850")
    if default_product_type == "Пара обручок":
        root.title("Калькулятор обручок")
    else:
        root.title("Калькулятор каблучки")

    tk.Button(
        root,
        text="← Назад",
        command=show_start_screen
    ).pack(anchor="w", padx=10, pady=10)

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    left_frame = tk.Frame(main_frame)
    left_frame.pack(side="left", fill="y", padx=10)

    right_frame = tk.Frame(main_frame)
    right_frame.pack(side="right", fill="both", expand=True, padx=10)

    tk.Label(left_frame, text="Тип прорахунку", font=("Arial", 12, "bold")).pack(anchor="w")

    product_type_var = tk.StringVar(value=default_product_type)

    tk.Label(
        left_frame,
        text=default_product_type,
        font=("Arial", 11)
    ).pack(anchor="w", pady=5)

    design_var = tk.StringVar(value="Вишиванка")

    if default_product_type == "Пара обручок":
        tk.Label(left_frame, text="Дизайн", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 0))

        design_box = ttk.Combobox(
            left_frame,
            textvariable=design_var,
            state="readonly",
            values=["Вишиванка", "Індивідуальний"]
        )
        design_box.pack(fill="x", pady=5)
    else:
        design_var.set("Індивідуальний")

    pair_frame = tk.LabelFrame(left_frame, text="Пара обручок", padx=10, pady=10)

    tk.Label(pair_frame, text="Обручка 1").grid(row=0, column=0, columnspan=2)

    tk.Label(pair_frame, text="Розмір").grid(row=1, column=0)
    entry_size_1 = tk.Entry(pair_frame)
    entry_size_1.insert(0, "19")
    entry_size_1.grid(row=1, column=1)

    tk.Label(pair_frame, text="Ширина").grid(row=2, column=0)
    entry_width_1 = tk.Entry(pair_frame)
    entry_width_1.insert(0, "4")
    entry_width_1.grid(row=2, column=1)

    tk.Label(pair_frame, text="Товщина").grid(row=3, column=0)
    entry_thickness_1 = tk.Entry(pair_frame)
    entry_thickness_1.insert(0, "1")
    entry_thickness_1.grid(row=3, column=1)

    tk.Label(pair_frame, text="Обручка 2").grid(row=4, column=0, columnspan=2, pady=(10, 0))

    tk.Label(pair_frame, text="Розмір").grid(row=5, column=0)
    entry_size_2 = tk.Entry(pair_frame)
    entry_size_2.insert(0, "16")
    entry_size_2.grid(row=5, column=1)

    tk.Label(pair_frame, text="Ширина").grid(row=6, column=0)
    entry_width_2 = tk.Entry(pair_frame)
    entry_width_2.insert(0, "4")
    entry_width_2.grid(row=6, column=1)

    tk.Label(pair_frame, text="Товщина").grid(row=7, column=0)
    entry_thickness_2 = tk.Entry(pair_frame)
    entry_thickness_2.insert(0, "1")
    entry_thickness_2.grid(row=7, column=1)

    ring_frame = tk.LabelFrame(left_frame, text="Каблучка", padx=10, pady=10)

    tk.Label(ring_frame, text="Розмір").grid(row=0, column=0)
    entry_ring_size = tk.Entry(ring_frame)
    entry_ring_size.insert(0, "16")
    entry_ring_size.grid(row=0, column=1)

    tk.Label(ring_frame, text="Ширина").grid(row=1, column=0)
    entry_ring_width = tk.Entry(ring_frame)
    entry_ring_width.insert(0, "4")
    entry_ring_width.grid(row=1, column=1)

    tk.Label(ring_frame, text="Товщина").grid(row=2, column=0)
    entry_ring_thickness = tk.Entry(ring_frame)
    entry_ring_thickness.insert(0, "1.8")
    entry_ring_thickness.grid(row=2, column=1)

    stones_frame = tk.LabelFrame(left_frame, text="Діаманти / каміння", padx=10, pady=10)

    tk.Label(stones_frame, text="Основний діамант").grid(row=0, column=0, columnspan=2)

    tk.Label(stones_frame, text="Розмір").grid(row=1, column=0)
    main_stone_size_var = tk.StringVar(value="1 мм")
    main_stone_size_box = ttk.Combobox(
        stones_frame,
        textvariable=main_stone_size_var,
        state="readonly",
        values=list(STONE_PRICES_USD["Натуральні діаманти"].keys())
    )
    main_stone_size_box.grid(row=1, column=1)

    tk.Label(stones_frame, text="К-сть").grid(row=2, column=0)
    main_stone_qty_entry = tk.Entry(stones_frame)
    main_stone_qty_entry.insert(0, "0")
    main_stone_qty_entry.grid(row=2, column=1)

    tk.Label(stones_frame, text="Малі діаманти").grid(row=3, column=0, columnspan=2, pady=(10, 0))

    tk.Label(stones_frame, text="Розмір").grid(row=4, column=0)
    small_stone_size_var = tk.StringVar(value="1 мм")
    small_stone_size_box = ttk.Combobox(
        stones_frame,
        textvariable=small_stone_size_var,
        state="readonly",
        values=list(STONE_PRICES_USD["Натуральні діаманти"].keys())
    )
    small_stone_size_box.grid(row=4, column=1)

    tk.Label(stones_frame, text="К-сть").grid(row=5, column=0)
    small_stone_qty_entry = tk.Entry(stones_frame)
    small_stone_qty_entry.insert(0, "0")
    small_stone_qty_entry.grid(row=5, column=1)

    tk.Label(left_frame, text="Знижка").pack(anchor="w", pady=(10, 0))
    discount_var = tk.StringVar(value="0")
    discount_box = ttk.Combobox(
        left_frame,
        textvariable=discount_var,
        state="readonly",
        values=["0", "7", "10", "15", "20"]
    )
    discount_box.pack(fill="x")

    tk.Label(left_frame, text="Покриття").pack(anchor="w", pady=(10, 0))
    coating_var = tk.StringVar(value="0")
    coating_box = ttk.Combobox(
        left_frame,
        textvariable=coating_var,
        state="readonly",
        values=["0", "50", "100", "200"]
    )
    coating_box.pack(fill="x")

    tk.Label(left_frame, text="Гравіювання").pack(anchor="w", pady=(10, 0))
    engraving_var = tk.StringVar(value="0")
    engraving_box = ttk.Combobox(
        left_frame,
        textvariable=engraving_var,
        state="readonly",
        values=["0", "800", "1500"]
    )
    engraving_box.pack(fill="x")

    tk.Label(left_frame, text="Доставка, грн").pack(anchor="w", pady=(10, 0))
    entry_delivery = tk.Entry(left_frame)
    entry_delivery.insert(0, "0")
    entry_delivery.pack(fill="x")

    tk.Button(
        left_frame,
        text="РОЗРАХУВАТИ",
        command=calculate,
        bg="#d4af37",
        font=("Arial", 12, "bold")
    ).pack(fill="x", pady=15)

    tk.Button(
        left_frame,
        text="СКОПІЮВАТИ ТЕКСТ КЛІЄНТУ",
        command=copy_client_text
    ).pack(fill="x")

    tk.Label(right_frame, text="📊 Технічний розрахунок", font=("Arial", 13, "bold")).pack(anchor="w")

    technical_output = tk.Text(right_frame, height=20, width=70, font=("Arial", 11))
    technical_output.pack(fill="both", expand=True, pady=5)

    tk.Label(right_frame, text="📋 Текст для клієнта", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10, 0))

    client_output = tk.Text(right_frame, height=12, width=70, font=("Arial", 11))
    client_output.pack(fill="both", expand=True, pady=5)

    update_mode()


def show_start_screen():
    for widget in root.winfo_children():
        widget.destroy()

    root.geometry("500x300")
    root.title("Вибір калькулятора")

    tk.Label(
        root,
        text="Що потрібно прорахувати?",
        font=("Arial", 18, "bold")
    ).pack(pady=40)

    tk.Button(
        root,
        text="Обручки",
        font=("Arial", 16, "bold"),
        width=20,
        height=2,
        bg="#d4af37",
        command=show_wedding_rings_interface
    ).pack(pady=10)

    tk.Button(
        root,
        text="Каблучка",
        font=("Arial", 16, "bold"),
        width=20,
        height=2,
        bg="#d4af37",
        command=show_ring_interface
    ).pack(pady=10)


def show_wedding_rings_interface():
    for widget in root.winfo_children():
        widget.destroy()

    build_calculator_interface("Пара обручок")


def show_ring_interface():
    for widget in root.winfo_children():
        widget.destroy()

    build_calculator_interface("Каблучка")



root = tk.Tk()
show_start_screen()
root.mainloop()
