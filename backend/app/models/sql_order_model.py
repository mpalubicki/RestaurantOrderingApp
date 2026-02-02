from datetime import datetime, timezone
from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = db.relationship("User", backref=db.backref("orders", lazy=True))

    status = db.Column(db.String(50), nullable=False, default="created")  # created, paid, preparing, ready, delivered, cancelled

    currency = db.Column(db.String(3), nullable=False, default="GBP")
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Order {self.id} user={self.user_id} status={self.status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    order = db.relationship("Order", back_populates="order_items")

    menu_item_id = db.Column(db.String(64), nullable=False)
    variant_id = db.Column(db.String(64), nullable=False)

    name = db.Column(db.String(255), nullable=False)
    variant_label = db.Column(db.String(255), nullable=False)

    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f"<OrderItem {self.id} order={self.order_id} {self.name} x{self.qty}>"

