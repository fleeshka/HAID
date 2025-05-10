import pandas as pd

df = pd.read_csv("data/products.csv")

'''converts default price into suitable for comparison format'''
def calculate_unit_price(quantity, unit, price):
    unit = str(unit).strip().lower()

    try:
        quantity = float(str(quantity).replace(',', '.'))
    except:
        return None

    if unit == 'л':
        q = quantity
    elif unit == 'мл':
        q = quantity / 1000
    elif unit == 'кг':
        q = quantity
    elif unit == 'г':
        q = quantity / 1000
    elif unit == 'шт':
        q = quantity
    elif unit == 'пакетиков':
        q = quantity
    elif unit == 'порций - пакетиков по 40 г':
        q = quantity * 40 / 1000
    else:
        return None

    if q == 0:
        return None

    return round(price / q, 2)


'''returns needed products'''
def get_products(
    store=None,
    category=None,
    min_price=None,
    max_price=None,
    available=True,
    type = None,
    need_unit_price = True,
):
    filtered = df.copy()

    if store:
        filtered = filtered[filtered["store"] == store]
    if category:
        filtered = filtered[filtered["category"] == category]
    if min_price is not None:
        filtered = filtered[filtered["price"] >= min_price]
    if max_price is not None:
        filtered = filtered[filtered["price"] <= max_price]
    if available:
        filtered = filtered[filtered["availability"] == "ИСТИНА"]
    if type:
        filtered = filtered[filtered["product_type"] == type]
    if need_unit_price:
        filtered["unit_price"] = filtered.apply(
            lambda row: calculate_unit_price(row["quantity"], row["unit"], row["price"]),
            axis=1
        )

    result = filtered.drop(columns = ['product_id','availability'])

    return result.to_dict(orient="records")

if __name__ == "__main__":
    results = get_products(available=True)
    for item in results:
        print(item)
