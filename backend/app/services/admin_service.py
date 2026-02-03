from datetime import datetime
from sqlalchemy.orm import joinedload
from ..extensions import db
from ..models.sql_order_model import Order, OrderItem
from ..models.user_model import User


def _order_to_dict(order: Order) -> dict:
    user = order.user 
    items = []
    for it in order.items:
        items.append(
            {
                "id": it.id,
                "menu_item_id": it.menu_item_id,
                "name": it.name,
                "variant": it.variant,
                "quantity": it.quantity,
                "price": float(it.price or 0),
            }
        )

    return {
        "id": order.id,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "status": order.status,
        "total": float(order.total or 0),
        "user_email": getattr(user, "email", None),
        "items": items,
        "user_first_name": getattr(user, "first_name", "") or "",
        "user_last_name": getattr(user, "last_name", "") or "",
        "order_items": items,
    }


def get_recent_orders_for_admin(limit: int = 50) -> list[dict]:
    q = (
        db.session.query(Order)
        .options(joinedload(Order.items), joinedload(Order.user))
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    orders = q.all()
    return [_order_to_dict(o) for o in orders]
