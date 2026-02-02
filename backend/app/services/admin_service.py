from app.extensions import db
from app.models.user_model import User
from app.models.sql_order_model import Order
from app.models.sql_order_model import OrderItem


def get_recent_orders_for_admin(limit: int = 50):
    q = (
        db.session.query(Order, User)
        .join(User, User.id == Order.user_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for order, user in q:
        items = (
            db.session.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

        results.append({
            "order_id": order.id,
            "created_at": order.created_at,
            "total": float(order.total_amount or 0),
            "user_first_name": user.first_name,
            "user_last_name": user.last_name,
            "items": [
                {
                    "name": it.name,
                    "variant_label": it.variant_label,
                    "qty": it.qty,
                }
                for it in items
            ],
        })

    return results
