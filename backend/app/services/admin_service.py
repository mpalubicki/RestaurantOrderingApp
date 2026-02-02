from app.models.user_model import User
from app.models.sql_order_model import Order
from sqlalchemy.orm import joinedload


def get_recent_orders_for_admin(limit: int = 50):
    orders = (
        Order.query
        .options(joinedload(Order.user), joinedload(Order.order_items))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for order in orders:
        user: User | None = getattr(order, "user", None)

        results.append({
            "order_id": order.id,
            "created_at": order.created_at,
            "total": float(order.total_amount or 0),
            "user_first_name": getattr(user, "first_name", "") if user else "",
            "user_last_name": getattr(user, "last_name", "") if user else "",
            "order_items": [
                {
                    "name": it.name,
                    "variant_label": it.variant_label,
                    "qty": it.qty,
                }
                for it in (order.order_items or [])
            ],
        })

    return results
