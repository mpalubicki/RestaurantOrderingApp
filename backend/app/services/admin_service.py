from app.models.user_model import User
from app.models.sql_order_model import Order
from sqlalchemy.orm import joinedload


def _order_to_dict(o: Order) -> dict:
    return {
        "order_id": o.id,
        "created_at": o.created_at,
        "status": o.status,
        "currency": o.currency,
        "total": float(o.total_amount or 0),
        "user_id": o.user_id,
        "user_email": getattr(o.user, "email", None) if getattr(o, "user", None) else None,
        "items": [
            {
                "menu_item_id": oi.menu_item_id,
                "variant_id": oi.variant_id,
                "name": oi.name,
                "variant_label": oi.variant_label,
                "qty": oi.qty,
                "unit_price": float(oi.unit_price or 0),
                "line_total": float(oi.line_total or 0),
            }
            for oi in (o.order_items or [])
        ],
    }


def get_recent_orders_for_admin(limit: int = 50):
    orders = (
        Order.query.options(joinedload(Order.order_items), joinedload(Order.user))
        .order_by(Order.created_at.desc())
        .limit(int(limit))
        .all()
    )
    return [_order_to_dict(o) for o in orders]


def get_order_for_admin(order_id: int) -> dict | None:
    o = (
        Order.query.options(joinedload(Order.order_items), joinedload(Order.user))
        .filter_by(id=int(order_id))
        .first()
    )
    if not o:
        return None
    return _order_to_dict(o)
