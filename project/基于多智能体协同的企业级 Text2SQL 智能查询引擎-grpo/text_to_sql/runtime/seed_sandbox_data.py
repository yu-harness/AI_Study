"""
Populate a sandbox database with deterministic business-like data.

This is an explicit operator tool. The application does not call it during
startup; pass the configured PostgreSQL URL when preparing the Docker sandbox.
"""

import argparse
import os
from datetime import date, timedelta
from pathlib import Path

try:
    from sqlalchemy import create_engine, text
except ImportError:  # pragma: no cover - script dependency
    def create_engine(*args, **kwargs):
        raise RuntimeError("SQLAlchemy is required to seed sandbox data")

    def text(sql):
        return sql


DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[1] / "data" / "sandbox.sqlite"


DDL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        city TEXT NOT NULL,
        segment TEXT NOT NULL,
        signup_date TEXT NOT NULL,
        active INTEGER NOT NULL,
        channel TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        supplier TEXT NOT NULL,
        launch_date TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        region TEXT NOT NULL,
        channel TEXT NOT NULL,
        CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount REAL NOT NULL,
        CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id),
        CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        paid_amount REAL NOT NULL,
        method TEXT NOT NULL,
        paid_at TEXT NOT NULL,
        refund_amount REAL NOT NULL,
        CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """,
]


POSTGRES_FOREIGN_KEYS = [
    ("fk_orders_user", "orders", "user_id", "users", "id"),
    ("fk_order_items_order", "order_items", "order_id", "orders", "id"),
    ("fk_order_items_product", "order_items", "product_id", "products", "id"),
    ("fk_payments_order", "payments", "order_id", "orders", "id"),
]


REGION_CITIES = {
    "east": ["Shanghai", "Hangzhou", "Nanjing", "Suzhou"],
    "south": ["Guangzhou", "Shenzhen", "Xiamen", "Fuzhou"],
    "north": ["Beijing", "Tianjin", "Qingdao", "Jinan"],
    "west": ["Chengdu", "Chongqing", "Xi'an", "Kunming"],
}
CATEGORIES = ["electronics", "home", "beauty", "sports", "books", "grocery"]
CHANNELS = ["app", "web", "store", "partner"]
SEGMENTS = ["new", "growth", "vip", "enterprise"]
PAYMENT_METHODS = ["card", "wallet", "bank_transfer", "coupon"]


def default_db_url() -> str:
    return "sqlite:///" + DEFAULT_SQLITE_PATH.as_posix()


def seed_database(
    db_url: str,
    user_count: int = 500,
    product_count: int = 120,
    order_count: int = 3000,
    max_items_per_order: int = 4,
    reset: bool = False,
) -> dict:
    """Create tables and insert deterministic sandbox rows."""

    if db_url.startswith("sqlite:///"):
        sqlite_path = Path(db_url.replace("sqlite:///", "", 1))
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            for ddl in DDL:
                conn.execute(text(ddl))
            if engine.dialect.name == "postgresql":
                _ensure_postgresql_foreign_keys(conn)
            if reset:
                for table in ("payments", "order_items", "orders", "products", "users"):
                    conn.execute(text(f"DELETE FROM {table}"))

            users = _build_users(user_count)
            products = _build_products(product_count)
            orders, items, payments = _build_orders(users, products, order_count, max_items_per_order)

            _insert_many(conn, "users", users)
            _insert_many(conn, "products", products)
            _insert_many(conn, "orders", orders)
            _insert_many(conn, "order_items", items)
            _insert_many(conn, "payments", payments)

        return {
            "users": len(users),
            "products": len(products),
            "orders": len(orders),
            "order_items": len(items),
            "payments": len(payments),
        }
    finally:
        engine.dispose()


def _build_users(count: int) -> list:
    rows = []
    start = date(2024, 1, 1)
    regions = list(REGION_CITIES)
    for idx in range(1, count + 1):
        region = regions[idx % len(regions)]
        cities = REGION_CITIES[region]
        rows.append(
            {
                "id": idx,
                "name": f"user_{idx:04d}",
                "region": region,
                "city": cities[idx % len(cities)],
                "segment": SEGMENTS[idx % len(SEGMENTS)],
                "signup_date": (start + timedelta(days=idx % 720)).isoformat(),
                "active": 0 if idx % 11 == 0 else 1,
                "channel": CHANNELS[idx % len(CHANNELS)],
            }
        )
    return rows


def _build_products(count: int) -> list:
    rows = []
    start = date(2024, 3, 1)
    for idx in range(1, count + 1):
        category = CATEGORIES[idx % len(CATEGORIES)]
        price = round(8.0 + (idx % 37) * 3.7 + (idx % 5) * 0.29, 2)
        rows.append(
            {
                "id": idx,
                "name": f"{category}_sku_{idx:03d}",
                "category": category,
                "price": price,
                "supplier": f"supplier_{(idx % 18) + 1:02d}",
                "launch_date": (start + timedelta(days=idx % 540)).isoformat(),
            }
        )
    return rows


def _build_orders(users: list, products: list, order_count: int, max_items_per_order: int) -> tuple:
    orders = []
    items = []
    payments = []
    product_by_id = {row["id"]: row for row in products}
    start = date(2025, 1, 1)
    item_id = 1
    payment_id = 1
    statuses = ["paid", "paid", "paid", "paid", "paid", "pending", "cancelled", "refunded"]

    for order_id in range(1, order_count + 1):
        user = users[((order_id * 37) % len(users))]
        item_count = 1 + (order_id % max(max_items_per_order, 1))
        amount = 0.0
        for offset in range(item_count):
            product_id = ((order_id * 13 + offset * 7) % len(products)) + 1
            product = product_by_id[product_id]
            quantity = 1 + ((order_id + offset) % 4)
            discount = round(((order_id + offset) % 5) * 0.03, 2)
            line_amount = product["price"] * quantity * (1 - discount)
            amount += line_amount
            items.append(
                {
                    "id": item_id,
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "discount": discount,
                }
            )
            item_id += 1

        status = statuses[order_id % len(statuses)]
        created_at = start + timedelta(days=order_id % 520)
        amount = round(amount, 2)
        orders.append(
            {
                "id": order_id,
                "user_id": user["id"],
                "amount": amount,
                "status": status,
                "created_at": created_at.isoformat(),
                "region": user["region"],
                "channel": CHANNELS[order_id % len(CHANNELS)],
            }
        )

        if status in ("paid", "refunded"):
            refund_amount = round(amount * 0.5, 2) if status == "refunded" else 0.0
            payments.append(
                {
                    "id": payment_id,
                    "order_id": order_id,
                    "paid_amount": amount,
                    "method": PAYMENT_METHODS[order_id % len(PAYMENT_METHODS)],
                    "paid_at": (created_at + timedelta(days=1)).isoformat(),
                    "refund_amount": refund_amount,
                }
            )
            payment_id += 1

    return orders, items, payments


def _insert_many(conn, table: str, rows: list):
    if not rows:
        return
    columns = list(rows[0])
    column_sql = ", ".join(columns)
    value_sql = ", ".join(f":{column}" for column in columns)
    conn.execute(text(f"INSERT INTO {table} ({column_sql}) VALUES ({value_sql})"), rows)


def _ensure_postgresql_foreign_keys(conn):
    for constraint, table, column, referred_table, referred_column in POSTGRES_FOREIGN_KEYS:
        exists = conn.execute(
            text("SELECT 1 FROM pg_constraint WHERE conname = :constraint"),
            {"constraint": constraint},
        ).fetchone()
        if not exists:
            conn.execute(
                text(
                    f"ALTER TABLE {table} ADD CONSTRAINT {constraint} "
                    f"FOREIGN KEY ({column}) REFERENCES {referred_table} ({referred_column})"
                )
            )


def main():
    parser = argparse.ArgumentParser(description="Seed a sandbox database with synthetic business rows.")
    parser.add_argument("--db-url", default=os.environ.get("TEXT2SQL_DB_URL") or default_db_url())
    parser.add_argument("--users", type=int, default=500)
    parser.add_argument("--products", type=int, default=120)
    parser.add_argument("--orders", type=int, default=3000)
    parser.add_argument("--max-items-per-order", type=int, default=4)
    parser.add_argument("--reset", action="store_true", help="Delete existing rows in managed tables first.")
    args = parser.parse_args()

    counts = seed_database(
        args.db_url,
        user_count=args.users,
        product_count=args.products,
        order_count=args.orders,
        max_items_per_order=args.max_items_per_order,
        reset=args.reset,
    )
    print({"db_url": args.db_url, **counts})


if __name__ == "__main__":
    main()
