#!/usr/bin/env python3
"""
POS básico en Python (consola) - archivo: pos.py
Requisitos: Python 3.8+
No necesita librerías externas.
"""
import sqlite3
import os
import csv
from datetime import datetime, date

DB_FILE = "pos.db"
RECEIPTS_DIR = "receipts"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT NOT NULL,
        total REAL NOT NULL,
        discount REAL NOT NULL DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        qty INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(sale_id) REFERENCES sales(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    conn.commit()
    conn.close()
    if not os.path.isdir(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR)

# ---------------------------
# Product management (CRUD)
# ---------------------------
def add_product(code, name, price, stock):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO products (code, name, price, stock) VALUES (?, ?, ?, ?)",
                    (code, name, float(price), int(stock)))
        conn.commit()
        print(f"[OK] Producto '{name}' añadido.")
    except sqlite3.IntegrityError:
        print("[ERROR] Ya existe un producto con ese código.")
    finally:
        conn.close()

def list_products():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, code, name, price, stock FROM products ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No hay productos.")
        return
    print(f"{'ID':>3} {'CÓDIGO':<12} {'NOMBRE':<30} {'P. Unit.':>9} {'STOCK':>6}")
    print("-"*65)
    for r in rows:
        print(f"{r[0]:>3} {r[1]:<12} {r[2]:<30} {r[3]:>9.2f} {r[4]:>6}")
    print("-"*65)

def find_product_by_code(code):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, code, name, price, stock FROM products WHERE code = ?", (code,))
    row = cur.fetchone()
    conn.close()
    return row

def update_product(code, name=None, price=None, stock=None):
    prod = find_product_by_code(code)
    if not prod:
        print("[ERROR] Producto no encontrado.")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    new_name = name if name is not None else prod[2]
    new_price = float(price) if price is not None else float(prod[3])
    new_stock = int(stock) if stock is not None else int(prod[4])
    cur.execute("UPDATE products SET name=?, price=?, stock=? WHERE code=?",
                (new_name, new_price, new_stock, code))
    conn.commit()
    conn.close()
    print("[OK] Producto actualizado.")

def delete_product(code):
    prod = find_product_by_code(code)
    if not prod:
        print("[ERROR] Producto no encontrado.")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE code=?", (code,))
    conn.commit()
    conn.close()
    print("[OK] Producto eliminado.")

# ---------------------------
# Sales
# ---------------------------
class CartItem:
    def __init__(self, product_id, code, name, unit_price, qty):
        self.product_id = product_id
        self.code = code
        self.name = name
        self.unit_price = float(unit_price)
        self.qty = int(qty)
    @property
    def subtotal(self):
        return self.unit_price * self.qty

class Cart:
    def __init__(self):
        self.items = []  # list of CartItem
        self.discount = 0.0  # absolute discount amount

    def add_item(self, product_code, qty=1):
        prod = find_product_by_code(product_code)
        if not prod:
            print("[ERROR] Código no encontrado.")
            return False
        product_id, code, name, price, stock = prod[0], prod[1], prod[2], prod[3], prod[4]
        if int(qty) <= 0:
            print("[ERROR] La cantidad debe ser positiva.")
            return False
        if int(qty) > stock:
            print(f"[ERROR] Stock insuficiente. Stock actual: {stock}")
            return False
        # if item exists, increment
        for it in self.items:
            if it.code == product_code:
                if it.qty + int(qty) > stock:
                    print(f"[ERROR] Al sumar, superas el stock (stock={stock}).")
                    return False
                it.qty += int(qty)
                print(f"[OK] Sumado {qty} a '{it.name}'. Nuevo qty: {it.qty}")
                return True
        # else new item
        item = CartItem(product_id, code, name, price, qty)
        self.items.append(item)
        print(f"[OK] Añadido {qty} x '{name}'.")
        return True

    def remove_item(self, product_code):
        for it in self.items:
            if it.code == product_code:
                self.items.remove(it)
                print(f"[OK] Eliminado {it.name} del carrito.")
                return True
        print("[ERROR] Producto no estaba en el carrito.")
        return False

    def change_qty(self, product_code, qty):
        for it in self.items:
            if it.code == product_code:
                if qty <= 0:
                    return self.remove_item(product_code)
                prod = find_product_by_code(product_code)
                if not prod:
                    print("[ERROR] Producto no encontrado.")
                    return False
                stock = prod[4]
                if qty > stock:
                    print(f"[ERROR] Stock insuficiente ({stock}).")
                    return False
                it.qty = qty
                print(f"[OK] Cantidad actualizada: {it.name} -> {qty}")
                return True
        print("[ERROR] Producto no estaba en el carrito.")
        return False

    @property
    def total(self):
        return sum(it.subtotal for it in self.items)

    def apply_discount_percent(self, percent):
        percent = float(percent)
        if not (0 <= percent <= 100):
            print("[ERROR] Porcentaje inválido.")
            return
        self.discount = round(self.total * (percent/100.0), 2)
        print(f"[OK] Aplicado descuento {percent}% -> {self.discount:.2f}€")

    def apply_discount_amount(self, amount):
        amount = float(amount)
        if amount < 0 or amount > self.total:
            print("[ERROR] Importe de descuento inválido.")
            return
        self.discount = round(amount, 2)
        print(f"[OK] Aplicado descuento fijo -> {self.discount:.2f}€")

    def clear(self):
        self.items = []
        self.discount = 0.0

def commit_sale(cart: Cart):
    if not cart.items:
        print("[ERROR] Carrito vacío.")
        return None
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec='seconds')
    total = cart.total
    discount = cart.discount
    final_total = round(total - discount, 2)
    if final_total < 0:
        final_total = 0.0
    cur.execute("INSERT INTO sales (datetime, total, discount) VALUES (?, ?, ?)",
                (now, final_total, discount))
    sale_id = cur.lastrowid
    # Insert items and decrement stock
    for it in cart.items:
        cur.execute("INSERT INTO sale_items (sale_id, product_id, qty, unit_price) VALUES (?, ?, ?, ?)",
                    (sale_id, it.product_id, it.qty, it.unit_price))
        # decrement stock
        cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (it.qty, it.product_id))
    conn.commit()
    conn.close()
    # generate receipt file
    filename = save_receipt(sale_id, cart, now, final_total)
    print(f"[OK] Venta registrada (ID: {sale_id}). Total: {final_total:.2f}€. Recibo: {filename}")
    return sale_id

def save_receipt(sale_id, cart: Cart, dt_iso, final_total):
    dt = datetime.fromisoformat(dt_iso)
    fname = f"receipt_{sale_id}_{dt.strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(RECEIPTS_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("----- RECIBO -----\n")
        f.write(f"Venta ID: {sale_id}\n")
        f.write(f"Fecha: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-"*30 + "\n")
        for it in cart.items:
            f.write(f"{it.qty} x {it.name} @ {it.unit_price:.2f} = {it.subtotal:.2f}\n")
        f.write("-"*30 + "\n")
        f.write(f"SUBTOTAL: {cart.total:.2f}\n")
        f.write(f"DESCUENTO: {cart.discount:.2f}\n")
        f.write(f"TOTAL: {final_total:.2f}\n")
        f.write("-"*30 + "\n")
    return path

# ---------------------------
# Reports
# ---------------------------
def report_sales_by_date(target_date: date):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    start = datetime.combine(target_date, datetime.min.time()).isoformat()
    end = datetime.combine(target_date, datetime.max.time()).isoformat()
    cur.execute("SELECT id, datetime, total, discount FROM sales WHERE datetime BETWEEN ? AND ? ORDER BY datetime",
                (start, end))
    sales = cur.fetchall()
    if not sales:
        print("No hay ventas en esa fecha.")
        conn.close()
        return
    print(f"Ventas para {target_date.isoformat()}:")
    total_sum = 0.0
    for s in sales:
        print(f"ID {s[0]}  {s[1]}  TOTAL: {s[2]:.2f}  DESC: {s[3]:.2f}")
        total_sum += float(s[2])
    print("-"*40)
    print(f"TOTAL DEL DÍA: {total_sum:.2f}")
    conn.close()

def export_sales_csv(target_date: date, out_file="sales_report.csv"):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    start = datetime.combine(target_date, datetime.min.time()).isoformat()
    end = datetime.combine(target_date, datetime.max.time()).isoformat()
    cur.execute("""
        SELECT s.id, s.datetime, s.total, s.discount, si.product_id, p.code, p.name, si.qty, si.unit_price
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
        LEFT JOIN products p ON p.id = si.product_id
        WHERE s.datetime BETWEEN ? AND ?
        ORDER BY s.datetime
    """, (start, end))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No hay ventas para exportar.")
        return
    with open(out_file, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["sale_id", "datetime", "sale_total", "sale_discount", "product_id", "product_code", "product_name", "qty", "unit_price"])
        writer.writerows(rows)
    print(f"[OK] Exportado a {out_file}")

# ---------------------------
# Simple CLI
# ---------------------------
def pause():
    input("Pulsa ENTER para continuar...")

def show_menu():
    print("\n--- POS - Menú ---")
    print("1) Listar productos")
    print("2) Añadir producto")
    print("3) Actualizar producto")
    print("4) Eliminar producto")
    print("5) Iniciar venta (carrito)")
    print("6) Reporte ventas por fecha")
    print("7) Exportar ventas CSV por fecha")
    print("0) Salir")

def handle_add_product():
    code = input("Código: ").strip()
    name = input("Nombre: ").strip()
    price = input("Precio unitario (ej: 3.50): ").strip()
    stock = input("Stock inicial (entero): ").strip()
    try:
        add_product(code, name, float(price), int(stock))
    except Exception as e:
        print("[ERROR] Datos inválidos.", e)

def handle_update_product():
    code = input("Código producto a actualizar: ").strip()
    prod = find_product_by_code(code)
    if not prod:
        print("[ERROR] Producto no encontrado.")
        return
    print(f"Encontrado: {prod[2]} | Precio: {prod[3]} | Stock: {prod[4]}")
    name = input("Nuevo nombre (ENTER para mantener): ").strip() or None
    price = input("Nuevo precio (ENTER para mantener): ").strip() or None
    stock = input("Nuevo stock (ENTER para mantener): ").strip() or None
    try:
        update_product(code, name, price, stock)
    except Exception as e:
        print("[ERROR] Fallo al actualizar.", e)

def handle_delete_product():
    code = input("Código producto a eliminar: ").strip()
    confirm = input("¿Seguro? (s/N): ").strip().lower()
    if confirm == 's':
        delete_product(code)
    else:
        print("Cancelado.")

def handle_sale():
    cart = Cart()
    while True:
        print("\n--- CREAR VENTA ---")
        print("a) Añadir artículo por código")
        print("r) Quitar artículo por código")
        print("c) Cambiar cantidad")
        print("v) Ver carrito")
        print("d) Aplicar descuento")
        print("p) Procesar venta y pagar")
        print("x) Cancelar venta")
        cmd = input("Opción: ").strip().lower()
        if cmd == 'a':
            code = input("Código producto: ").strip()
            qty = input("Cantidad (ENTER=1): ").strip() or "1"
            try:
                cart.add_item(code, int(qty))
            except Exception as e:
                print("[ERROR]", e)
        elif cmd == 'r':
            code = input("Código producto a quitar: ").strip()
            cart.remove_item(code)
        elif cmd == 'c':
            code = input("Código producto: ").strip()
            qty = input("Nueva cantidad: ").strip()
            try:
                cart.change_qty(code, int(qty))
            except Exception as e:
                print("[ERROR]", e)
        elif cmd == 'v':
            if not cart.items:
                print("Carrito vacío.")
            else:
                print("Carrito:")
                for it in cart.items:
                    print(f"{it.qty} x {it.name} @ {it.unit_price:.2f} = {it.subtotal:.2f}")
                print(f"SUBTOTAL: {cart.total:.2f}  DESCUENTO: {cart.discount:.2f}  TOTAL: {cart.total - cart.discount:.2f}")
        elif cmd == 'd':
            typ = input("Tipo (p=porcentaje / a=importe): ").strip().lower()
            if typ == 'p':
                p = input("Porcentaje (0-100): ").strip()
                cart.apply_discount_percent(float(p))
            elif typ == 'a':
                a = input("Importe de descuento: ").strip()
                cart.apply_discount_amount(float(a))
            else:
                print("Tipo inválido.")
        elif cmd == 'p':
            print("Procesando venta...")
            sale_id = commit_sale(cart)
            if sale_id:
                cart.clear()
            break
        elif cmd == 'x':
            confirm = input("Cancelar venta actual? (s/N): ").strip().lower()
            if confirm == 's':
                print("Venta cancelada.")
                break
        else:
            print("Opción inválida.")

def handle_report():
    d = input("Fecha (YYYY-MM-DD) [ENTER=Hoy]: ").strip()
    if not d:
        target = date.today()
    else:
        try:
            target = date.fromisoformat(d)
        except Exception:
            print("Fecha inválida.")
            return
    report_sales_by_date(target)
    pause()

def handle_export_csv():
    d = input("Fecha (YYYY-MM-DD) [ENTER=Hoy]: ").strip()
    if not d:
        target = date.today()
    else:
        try:
            target = date.fromisoformat(d)
        except Exception:
            print("Fecha inválida.")
            return
    out = input("Nombre archivo salida (default: sales_report.csv): ").strip() or "sales_report.csv"
    export_sales_csv(target, out)
    pause()

def main():
    init_db()
    while True:
        show_menu()
        choice = input("Elige opción: ").strip()
        if choice == '1':
            list_products()
            pause()
        elif choice == '2':
            handle_add_product()
            pause()
        elif choice == '3':
            handle_update_product()
            pause()
        elif choice == '4':
            handle_delete_product()
            pause()
        elif choice == '5':
            handle_sale()
            pause()
        elif choice == '6':
            handle_report()
        elif choice == '7':
            handle_export_csv()
        elif choice == '0':
            print("Adiós.")
            break
        else:
            print("Opción inválida.")
            pause()

if __name__ == "__main__":
    main()
