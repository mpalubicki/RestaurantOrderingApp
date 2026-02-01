from app.extensions import mongo
from bson.objectid import ObjectId


def compute_availability(item: dict) -> dict:
    variants = item.get("variants") or []
    if not variants:
        return {"status": "available", "notes": ""}

    available_variants = [v for v in variants if v.get("available") is True]
    unavailable_variants = [v for v in variants if v.get("available") is False]

    if len(available_variants) == 0:
        return {"status": "unavailable", "notes": "Currently unavailable"}
    if len(unavailable_variants) == 0:
        return {"status": "available", "notes": ""}

    if len(available_variants) == 1:
        label = available_variants[0].get("label") or "selected option"
        return {"status": "limited", "notes": f"Available: {label} only"}

    labels = [(v.get("label") or "option") for v in unavailable_variants]
    return {"status": "limited", "notes": "Unavailable: " + ", ".join(labels)}


def _best_price_display(item: dict) -> dict:
    variants = item.get("variants") or []
    base_price = item.get("base_price")

    if not variants:
        if isinstance(base_price, (int, float)):
            return {"from_price": float(base_price), "to_price": float(base_price), "currency": "GBP"}
        return {"from_price": None, "to_price": None, "currency": "GBP"}

    available_prices = [
        v.get("price") for v in variants
        if v.get("available") is True and isinstance(v.get("price"), (int, float))
    ]
    pool = available_prices if available_prices else [
        v.get("price") for v in variants if isinstance(v.get("price"), (int, float))
    ]

    if not pool:
        return {"from_price": None, "to_price": None, "currency": "GBP"}

    return {"from_price": float(min(pool)), "to_price": float(max(pool)), "currency": "GBP"}


def _is_menu_item_list(key: str, value) -> bool:

    if not isinstance(value, list) or len(value) == 0:
        return False

    if key.startswith("shared_") or key.endswith("_add_ons"):
        return False

    first = value[0]
    if not isinstance(first, dict):
        return False

    has_name = "name" in first
    has_category = "category" in first
    has_variants = "variants" in first

    return has_name and (has_category or has_variants)


def _flatten_menu_docs(docs: list[dict]) -> list[dict]:
    items: list[dict] = []
    for doc in docs:
        extracted = False
        for key, value in doc.items():
            if _is_menu_item_list(key, value):
                items.extend(value)
                extracted = True

        if not extracted and isinstance(doc.get("name"), str):
            items.append(doc)

    return items


def format_menu_item_box(item: dict) -> dict:
    availability = compute_availability(item)
    price = _best_price_display(item)

    shared = (item.get("components") or {}).get("shared") or {}
    dietary = shared.get("dietary") or item.get("dietary") or []
    ingredients = shared.get("ingredients") or item.get("ingredients") or []

    variant_lines = []
    for v in item.get("variants", []) or []:
        variant_lines.append({
            "id": v.get("_id"),
            "label": v.get("label"),
            "price": v.get("price"),
            "available": bool(v.get("available"))
        })

    return {
        "id": item.get("_id"),
        "category": item.get("category") or "Other",
        "title": item.get("name"),
        "description": item.get("description", ""),
        "badges": {
            "dietary": dietary,
            "availability_status": availability["status"]
        },
        "availability": availability,
        "price": price,
        "ingredients_preview": ingredients[:6],
        "variants": variant_lines
    }


def get_menu_boxes(group_by_category: bool = True):
    docs = list(mongo.db.menu_items.find())

    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["_id"] = str(d["_id"])

    items = _flatten_menu_docs(docs)
    boxes = [format_menu_item_box(item) for item in items]

    if not group_by_category:
        return boxes

    grouped: dict[str, list[dict]] = {}
    for box in boxes:
        grouped.setdefault(box["category"], []).append(box)

    for cat in grouped:
        grouped[cat].sort(key=lambda b: (b.get("title") or "").lower())

    PREFERRED_CATEGORY_ORDER = [
        "Starters",
        "Sharing Platters",
        "Salads",
        "Meat",
        "Fish",
        "Pasta",
        "Pizza",
        "Desserts",
        "Soft Drinks",
        "Beer",
        "Wine",
    ]


    def _category_sort_key(category_name: str):
        try:
            return (0, PREFERRED_CATEGORY_ORDER.index(category_name))
        except ValueError:
            return (1, 9999)

    return dict(sorted(grouped.items(), key=lambda kv: _category_sort_key(kv[0])))


