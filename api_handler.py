import pandas as pd

df = pd.read_csv("products.csv")

def get_products(
    store=None,
    category=None,
    min_price=None,
    max_price=None,
    available=True,
    type = None
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

    return filtered.to_dict(orient="records")

if __name__ == "__main__":
    results = get_products(available=True)
    for item in results:
        print(item)
