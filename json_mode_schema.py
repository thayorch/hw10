from litellm import completion
from config import MODEL
import json


# {
#   "order_id": "A-1029",
#   "customer": { "name": "Sarah Johnson", "email": "sj@example.com" },
#   "items": [
#     { "sku": "WB-500", "name": "Water Bottle", "qty": 2, "price": 12.50 },
#     { "sku": "CP-010", "name": "Carrying Pouch", "qty": 1, "price": 5.00 }
#   ],
#   "total": 30.00,
#   "currency": "USD"
# }


schema = {
    "name": "OrderExtraction",
    "schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "customer": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["name", "email"],
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string"},
                        "name": {"type": "string"},
                        "qty": {"type": "integer"},
                        "price": {"type": "number"},
                    },
                    "required": ["sku", "name", "qty", "price"],
                },
            },
            "total": {"type": "number"},
            "currency": {"type": "string"},
        },
        "required": ["order_id", "customer", "items", "total", "currency"],
        "additionalProperties": False,
    },
    "strict": True,
}

messages = [
    {"role": "system", "content": "Return ONLY a JSON object matching the schema."},
    {
        "role": "user",
        "content": "Order A-1029 by Sarah Johnson : 2x Water Bottle ($12.50 each), 1x Carrying Pouch ($5). Total $30.",
    },
]

resp = completion(
    model=MODEL,
    messages=messages,
    response_format={"type": "json_schema", "json_schema": schema},
)
content = resp.choices[0].message["content"]
print("RAW JSON:\n", content)
print("\nParsed:\n", json.dumps(json.loads(content), indent=2))
