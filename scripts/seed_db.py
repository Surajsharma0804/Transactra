"""
Transactra — Database Seeder

Seeds the database with test data from data/seed/products.json.
Creates 3 merchants, their users, and 43+ products with inventory.

Usage:
    python scripts/seed_db.py
    # or: make seed
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings

logger = logging.getLogger("transactra.seed")


async def seed_database() -> None:
    """Seed the database with test merchants, users, and products."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    seed_file = Path(__file__).parent.parent / "data" / "seed" / "products.json"
    if not seed_file.exists():
        logger.error(f"Seed file not found: {seed_file}")
        return

    with open(seed_file) as f:
        merchants_data = json.load(f)

    async with session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            logger.info(f"Database already seeded ({count} users). Skipping.")
            return

        total_products = 0

        for merchant_data in merchants_data:
            # Create merchant user
            user_id = uuid.uuid4()
            merchant_id = uuid.uuid4()
            merchant_key = merchant_data["merchant_key"]
            display_name = merchant_data["display_name"]

            await session.execute(
                text("""
                    INSERT INTO users (user_id, email, display_name, identity_key, status)
                    VALUES (:user_id, :email, :display_name, :identity_key, 'active')
                """),
                {
                    "user_id": user_id,
                    "email": f"{merchant_key}@transactra.test",
                    "display_name": f"{display_name} Owner",
                    "identity_key": f"test_key_{merchant_key}",
                },
            )

            await session.execute(
                text("""
                    INSERT INTO merchants (merchant_id, merchant_key, display_name, owner_user_id, status)
                    VALUES (:merchant_id, :merchant_key, :display_name, :owner_user_id, 'active')
                """),
                {
                    "merchant_id": merchant_id,
                    "merchant_key": merchant_key,
                    "display_name": display_name,
                    "owner_user_id": user_id,
                },
            )

            # Create a merchant agent
            agent_id = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO agents (agent_id, owner_user_id, agent_type, display_name, status)
                    VALUES (:agent_id, :owner_user_id, 'merchant', :display_name, 'active')
                """),
                {
                    "agent_id": agent_id,
                    "owner_user_id": user_id,
                    "display_name": f"{display_name} Agent",
                },
            )

            # Grant merchant capabilities
            for cap in ["search", "manage_catalog", "manage_policy", "approve_offer", "negotiate"]:
                await session.execute(
                    text("""
                        INSERT INTO agent_capabilities (agent_id, capability)
                        VALUES (:agent_id, :capability)
                    """),
                    {"agent_id": agent_id, "capability": cap},
                )

            # Create products and inventory
            for product in merchant_data["products"]:
                product_id = uuid.uuid4()
                await session.execute(
                    text("""
                        INSERT INTO products (
                            product_id, merchant_id, sku, title, description, category,
                            price_paise, currency, attributes, warranty_months, refurbished,
                            shipping_days, shipping_paise, returnable, return_window_days, is_active
                        ) VALUES (
                            :product_id, :merchant_id, :sku, :title, :description, :category,
                            :price_paise, :currency, :attributes::jsonb, :warranty_months, :refurbished,
                            :shipping_days, :shipping_paise, :returnable, :return_window_days, true
                        )
                    """),
                    {
                        "product_id": product_id,
                        "merchant_id": merchant_id,
                        "sku": product["sku"],
                        "title": product["title"],
                        "description": product["description"],
                        "category": product["category"],
                        "price_paise": product["price_paise"],
                        "currency": product["currency"],
                        "attributes": json.dumps(product["attributes"]),
                        "warranty_months": product["warranty_months"],
                        "refurbished": product["refurbished"],
                        "shipping_days": product["shipping_days"],
                        "shipping_paise": product["shipping_paise"],
                        "returnable": product["returnable"],
                        "return_window_days": product["return_window_days"],
                    },
                )

                await session.execute(
                    text("""
                        INSERT INTO inventory (product_id, quantity, reserved)
                        VALUES (:product_id, :quantity, 0)
                    """),
                    {
                        "product_id": product_id,
                        "quantity": product["quantity"],
                    },
                )
                total_products += 1

            logger.info(
                f"Seeded merchant: {display_name} ({len(merchant_data['products'])} products)"
            )

        # Create a test buyer user and agent
        buyer_user_id = uuid.uuid4()
        buyer_agent_id = uuid.uuid4()

        await session.execute(
            text("""
                INSERT INTO users (user_id, email, display_name, identity_key, status)
                VALUES (:user_id, 'buyer@transactra.test', 'Test Buyer', 'test_key_buyer', 'active')
            """),
            {"user_id": buyer_user_id},
        )

        await session.execute(
            text("""
                INSERT INTO agents (agent_id, owner_user_id, agent_type, display_name, status)
                VALUES (:agent_id, :owner_user_id, 'buyer', 'Test Buyer Agent', 'active')
            """),
            {"agent_id": buyer_agent_id, "owner_user_id": buyer_user_id},
        )

        for cap in ["search", "compare", "negotiate", "propose_cart", "request_authorization", "view_proof"]:
            await session.execute(
                text("""
                    INSERT INTO agent_capabilities (agent_id, capability)
                    VALUES (:agent_id, :capability)
                """),
                {"agent_id": buyer_agent_id, "capability": cap},
            )

        await session.commit()
        logger.info(
            f"Seed complete: {len(merchants_data)} merchants, "
            f"{total_products} products, 1 test buyer"
        )

    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    asyncio.run(seed_database())
