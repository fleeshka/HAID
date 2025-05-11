import numpy as np
from sklearn.neighbors import NearestNeighbors

'''recommends top-k products in category'''
def recommend_top_k(products, category, budget=None, k=3, preferred_store=None):
    filtered = [p for p in products if p['category'] == category and p.get('unit_price') is not None] #get all products in this category

    if budget is not None:
        filtered = [p for p in filtered if p['price'] <= budget] # if exist budget per category
    if preferred_store: #if customer has some preference in stores - preffered will be better
        for p in filtered:
            p['adjusted_unit_price'] = p['unit_price'] * 0.3 if p['store'] == preferred_store else p['unit_price']
    else:
        for p in filtered:
            p['adjusted_unit_price'] = p['unit_price']

    if not filtered:
        return []

    # create array adjusted_by_store_unit_price^2
    X = np.array([[p['adjusted_unit_price']] for p in filtered])
    # fit model to get k near as good products as the best one
    model = NearestNeighbors(n_neighbors=min(k, len(filtered))).fit(X)
    # get top k products in givaen category
    distances, indices = model.kneighbors([[min(X)[0]]])
    # get products itself
    top_in_cat = [filtered[i] for i in indices[0]]
    for p in top_in_cat:
        p.pop('unit_price', None)
        p.pop('adjusted_unit_price', None)
    return top_in_cat

def recommend(products,
                  categories,
                  budget_map=None, # {category:budget for it}
                  preferred_store=None,
                  k=3):
    recs = {}

    for cat in categories:
        budget = budget_map.get(cat) if budget_map else None
        top_items = recommend_top_k(
            products,
            category=cat,
            budget=budget,
            k=k,
            preferred_store=preferred_store
        )
        recs[cat] = top_items

    return recs