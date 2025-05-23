import redis
import json

r = redis.Redis(host='redis', port=6379, decode_responses=True)

def _get_user_key(user_id):
    return f"user:{user_id}"

def save_context(user_id, key, value):
    user_key = _get_user_key(user_id)
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    r.hset(user_key, key, value)

def get_context(user_id):
    user_key = _get_user_key(user_id)
    raw_data = r.hgetall(user_key)
    parsed_data = {}
    for key, val in raw_data.items():
        try:
            parsed_data[key] = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            parsed_data[key] = val
    return parsed_data

def get_extracted_products(user_id: int) -> str:
    context = get_context(user_id)
    products = context.get("products_extracted")
    if not products:
        return "Продукты не найдены."
    if isinstance(products, list):
        return ", ".join(products)
    return str(products)

async def handle_final_list(user_id, combined_list):
    combined_list_str = ", ".join(combined_list)

    save_context(user_id, "final_product_list", combined_list_str)

def get_final_list_from_redis(user_id):
    context = get_context(user_id)
    combined_list_str = context.get("final_product_list") 
    
    if combined_list_str:
        combined_list = combined_list_str.split(", ")
        return combined_list
    return []

def get_provided_recipes(user_id: int) -> str:
    return get_context(user_id).get("provided_recipes", "Рецепты не найдены.")

def reset_context(user_id):
    user_key = _get_user_key(user_id)
    r.delete(user_key)

def set_state(user_id, state):
    save_context(user_id, "state", state)

def get_state(user_id):
    return get_context(user_id).get("state", None)