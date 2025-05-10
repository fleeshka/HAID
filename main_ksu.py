from pprint import pprint

from api_handler import get_products
from recomender import recommend


def input_categories():
    print("Введите интересующие категории продуктов через запятую (например: молочка, сладкое, мясо):")
    cats = input("> ")
    return [c.strip() for c in cats.split(',') if c.strip()]

def input_budgets(categories):
    budget_map = {}
    print("Есть ли ограничения по бюджету на какие-либо категории? (да/нет)")
    if input("> ").strip().lower() == 'да':
        for cat in categories:
            print(f"Укажите бюджет для категории '{cat}' (или оставьте пустым, если нет ограничения):")
            val = input("> ").replace(',', '.')
            if val:
                try:
                    budget_map[cat] = float(val)
                except ValueError:
                    print("Некорректное значение, пропускаем.")
    return budget_map

def input_preferred_store():
    print("Есть ли у вас любимый магазин? (да/нет)")
    if input("> ").strip().lower() == 'да':
        print("Введите название магазина:")
        return input("> ").strip()
    return None

def main():
    # get products
    products = get_products(need_unit_price=True)

    # get categories
    categories = input_categories()

    # get budget constraints
    budget_map = input_budgets(categories)

    # get best store
    preferred_store = input_preferred_store()

    # number of recomnedation per category
    k = 3

    # do recomendations
    result = recommend(
        products,
        categories=categories,
        budget_map=budget_map,
        preferred_store=preferred_store,
        k=k
    )

    print("\nРезультаты рекомендаций:")
    pprint(result, width=120)

if __name__ == "__main__":
    main()
