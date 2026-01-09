from ..extensions import mongo
from bson.objectid import ObjectId

def get_all_menu_items():
    items = list(mongo.db.menu_items.find())
    for item in items:
        item["_id"] = str(item["_id"])  # JSON-safe
    return items
