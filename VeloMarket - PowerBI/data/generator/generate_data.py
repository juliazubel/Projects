"""
VeloMarket – synthetic dataset generator for the Power BI portfolio project.

VeloMarket is a fictional omnichannel retailer of bikes, e-bikes, components,
apparel and accessories operating in Poland, Czechia and Germany through
physical stores, own e-commerce sites and a marketplace.

The script produces *raw* source files that intentionally contain realistic
data-quality issues, so that Power Query has real work to do:

  data/raw/sales/sales_YYYY_MM.csv   monthly ERP exports (folder source)
      - SKU in mixed case / with stray spaces
      - duplicated lines re-exported in the following month's file
      - QA test orders (StoreID TEST-01, CustomerID TEST-QA)
      - anonymous walk-in customers (empty CustomerID)
      - a legacy SKU that does not exist in the product master
      - prices in local currency (PLN / CZK / EUR)
  data/raw/products.xlsx             report-style Excel export (title rows,
                                     Category/Subcategory only on first row of a group)
  data/raw/customers.csv             CRM export with history rows (duplicates),
                                     inconsistent country names and city casing
  data/raw/stores.csv                store / channel master
  data/raw/returns.csv               returned order lines
  data/raw/inventory_snapshots.csv   month-end stock per store x SKU (semi-additive)
  data/raw/fx_rates_nbp.csv          monthly avg FX rates, wide, Polish locale (; and ,)
  data/raw/budget.xlsx               finance budget, wide (months as columns),
                                     one sheet per year, Polish labels, total row/column
  data/raw/security_users.csv        user -> country mapping for dynamic RLS

Run:  python generate_data.py          (deterministic – fixed seed)
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

SEED = 2026
rng = np.random.default_rng(SEED)

RAW_DIR = Path(__file__).resolve().parent.parent / "raw"
SALES_DIR = RAW_DIR / "sales"

START_DATE = date(2023, 1, 1)
END_DATE = date(2026, 9, 30)  # last day with sales ("current year in progress")

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
# (category, subcategory, brands, price range PLN, cost ratio range, n products, qty range)
SUBCATEGORIES = [
    ("Bikes", "Road Bikes", ["Velor", "Stravo"], (4200, 15500), (0.58, 0.68), 6, (1, 1)),
    ("Bikes", "Mountain Bikes", ["Tarnik", "Velor", "Stravo"], (3200, 12500), (0.58, 0.68), 7, (1, 1)),
    ("Bikes", "City Bikes", ["UrbanFox", "Tarnik"], (1800, 4200), (0.55, 0.66), 5, (1, 1)),
    ("Bikes", "Kids Bikes", ["UrbanFox", "Tarnik"], (700, 1600), (0.52, 0.62), 4, (1, 1)),
    ("E-Bikes", "E-City", ["UrbanFox", "Velor"], (7200, 12500), (0.64, 0.74), 4, (1, 1)),
    ("E-Bikes", "E-MTB", ["Tarnik", "Stravo"], (12500, 22500), (0.64, 0.74), 4, (1, 1)),
    ("E-Bikes", "E-Trekking", ["Velor", "UrbanFox"], (9000, 15500), (0.64, 0.74), 3, (1, 1)),
    ("Components", "Drivetrain", ["Gearon"], (150, 1500), (0.50, 0.62), 7, (1, 2)),
    ("Components", "Brakes", ["Brakko"], (110, 950), (0.50, 0.62), 5, (1, 2)),
    ("Components", "Wheels", ["Rimline"], (420, 3100), (0.52, 0.64), 5, (1, 2)),
    ("Components", "Tyres & Tubes", ["Rimline", "Gearon"], (30, 320), (0.45, 0.58), 6, (1, 4)),
    ("Apparel", "Jerseys", ["Pedalwear", "NorthKit"], (150, 460), (0.34, 0.48), 6, (1, 3)),
    ("Apparel", "Shorts & Tights", ["Pedalwear", "NorthKit"], (150, 520), (0.34, 0.48), 5, (1, 2)),
    ("Apparel", "Jackets", ["NorthKit"], (260, 950), (0.36, 0.50), 5, (1, 1)),
    ("Apparel", "Gloves", ["Pedalwear"], (50, 210), (0.32, 0.45), 4, (1, 2)),
    ("Accessories", "Helmets", ["SafeRide", "Velor"], (150, 950), (0.40, 0.52), 6, (1, 2)),
    ("Accessories", "Lights", ["Lumo"], (60, 420), (0.38, 0.50), 5, (1, 2)),
    ("Accessories", "Locks", ["SafeRide"], (60, 360), (0.38, 0.50), 4, (1, 1)),
    ("Accessories", "Bottles & Cages", ["Lumo", "Velor"], (20, 95), (0.30, 0.42), 4, (1, 3)),
    ("Accessories", "Bike Computers", ["Lumo"], (320, 1850), (0.55, 0.66), 4, (1, 1)),
    ("Nutrition", "Energy Gels", ["FuelUp"], (6, 16), (0.35, 0.45), 4, (3, 15)),
    ("Nutrition", "Energy Bars", ["FuelUp"], (7, 14), (0.35, 0.45), 4, (3, 12)),
    ("Nutrition", "Isotonic Drinks", ["FuelUp"], (35, 85), (0.35, 0.45), 3, (1, 4)),
]
MODEL_NAMES = ["Aero", "Sprint", "Trail", "Summit", "Ridge", "Comet", "Atlas", "Nova",
               "Vento", "Ranger", "Flow", "Pulse", "Orbit", "Strada", "Glide", "Vector"]
COLORS = ["Black", "White", "Red", "Blue", "Green", "Graphite", "Orange", "Silver"]
CAT_CODE = {"Bikes": "BIK", "E-Bikes": "EBK", "Components": "CMP",
            "Apparel": "APP", "Accessories": "ACC", "Nutrition": "NUT"}
SUB_SUFFIX = {
    "Road Bikes": "Road Bike", "Mountain Bikes": "MTB", "City Bikes": "City Bike",
    "Kids Bikes": "Kids Bike", "E-City": "E-City", "E-MTB": "E-MTB", "E-Trekking": "E-Trekking",
    "Drivetrain": "Groupset", "Brakes": "Brake Set", "Wheels": "Wheelset",
    "Tyres & Tubes": "Tyre", "Jerseys": "Jersey", "Shorts & Tights": "Bib Shorts",
    "Jackets": "Jacket", "Gloves": "Gloves", "Helmets": "Helmet", "Lights": "Light Set",
    "Locks": "U-Lock", "Bottles & Cages": "Bottle", "Bike Computers": "GPS Computer",
    "Energy Gels": "Energy Gel", "Energy Bars": "Energy Bar", "Isotonic Drinks": "Isotonic Mix",
}


def build_products() -> pd.DataFrame:
    rows = []
    counters: dict[str, int] = {}
    for cat, sub, brands, (pmin, pmax), (cmin, cmax), n, qty in SUBCATEGORIES:
        models = rng.choice(MODEL_NAMES, n, replace=False)  # unique product names
        for i in range(n):
            counters[cat] = counters.get(cat, 0) + 1
            sku = f"VM-{CAT_CODE[cat]}-{counters[cat]:04d}"
            brand = brands[i % len(brands)]
            model = models[i]
            tier = rng.choice(["", " Pro", " Sport", " Comp", " Elite"]) if cat in ("Bikes", "E-Bikes", "Components") else ""
            name = f"{brand} {model}{tier} {SUB_SUFFIX[sub]}"
            # price spread inside subcategory (log-uniform)
            price = float(np.exp(rng.uniform(np.log(pmin), np.log(pmax))))
            price = round(price, -1) - 0.01 if price > 100 else round(price, 0) - 0.01
            cost = round(price * rng.uniform(cmin, cmax), 2)
            launch = date(2019, 1, 1) + timedelta(days=int(rng.integers(0, 1400)))
            status, discontinued = "Active", None
            r = rng.random()
            if r < 0.08:  # new product launched during the analysed period
                launch = date(2024, 1, 1) + timedelta(days=int(rng.integers(0, 640)))
            elif r < 0.14:  # discontinued product
                discontinued = date(2024, 6, 1) + timedelta(days=int(rng.integers(0, 400)))
                status = "Discontinued"
            rows.append(dict(
                Category=cat, Subcategory=sub, SKU=sku, ProductName=name, Brand=brand,
                Color=COLORS[rng.integers(len(COLORS))], ListPrice=price, UnitCost=cost,
                LaunchDate=launch, Status=status, Discontinued=discontinued,
                QtyMin=qty[0], QtyMax=qty[1],
                Popularity=float(rng.lognormal(0, 0.6)),
            ))
    # make e-bikes and new products a bit more "hot"
    df = pd.DataFrame(rows)
    df.loc[df.Category == "E-Bikes", "Popularity"] *= 1.2
    return df


# ---------------------------------------------------------------------------
# Stores / channels
# ---------------------------------------------------------------------------
STORES = [
    # StoreID, Name, Channel, City, Country, Code, Currency, Region, OpenDate, Area, base orders/day (2025)
    ("PL-WAW-01", "VeloMarket Warszawa Mokotów", "Store", "Warszawa", "Poland", "PL", "PLN", "Central", date(2019, 3, 15), 1200, 4.6),
    ("PL-WAW-02", "VeloMarket Warszawa Wola", "Store", "Warszawa", "Poland", "PL", "PLN", "Central", date(2021, 5, 1), 900, 3.2),
    ("PL-KRK-01", "VeloMarket Kraków", "Store", "Kraków", "Poland", "PL", "PLN", "South", date(2019, 9, 1), 1100, 3.6),
    ("PL-WRO-01", "VeloMarket Wrocław", "Store", "Wrocław", "Poland", "PL", "PLN", "West", date(2020, 4, 1), 950, 3.1),
    ("PL-GDN-01", "VeloMarket Gdańsk", "Store", "Gdańsk", "Poland", "PL", "PLN", "North", date(2022, 3, 1), 850, 2.6),
    ("PL-POZ-01", "VeloMarket Poznań", "Store", "Poznań", "Poland", "PL", "PLN", "West", date(2023, 6, 1), 800, 2.3),
    ("PL-LDZ-01", "VeloMarket Łódź", "Store", "Łódź", "Poland", "PL", "PLN", "Central", date(2024, 4, 15), 750, 1.9),
    ("PL-WEB-01", "velomarket.pl", "E-commerce", "Warszawa", "Poland", "PL", "PLN", "Online PL", date(2018, 1, 1), None, 11.0),
    ("PL-MKT-01", "Marketplace PL", "Marketplace", "Poznań", "Poland", "PL", "PLN", "Online PL", date(2020, 1, 1), None, 6.0),
    ("CZ-PRG-01", "VeloMarket Praha", "Store", "Praha", "Czechia", "CZ", "CZK", "Czechia", date(2021, 4, 1), 1000, 2.6),
    ("CZ-BRN-01", "VeloMarket Brno", "Store", "Brno", "Czechia", "CZ", "CZK", "Czechia", date(2024, 9, 1), 700, 1.6),
    ("CZ-WEB-01", "velomarket.cz", "E-commerce", "Praha", "Czechia", "CZ", "CZK", "Czechia", date(2021, 1, 1), None, 3.6),
    ("DE-BER-01", "VeloMarket Berlin", "Store", "Berlin", "Germany", "DE", "EUR", "Germany", date(2022, 10, 1), 1100, 2.1),
    ("DE-WEB-01", "velomarket.de", "E-commerce", "Berlin", "Germany", "DE", "EUR", "Germany", date(2022, 6, 1), None, 4.2),
]
STORE_COLS = ["StoreID", "StoreName", "Channel", "City", "Country", "CountryCode", "Currency",
              "Region", "OpenDate", "SalesAreaM2", "BaseOrders"]

CITIES = {
    "Poland": ["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Poznań", "Łódź", "Katowice", "Lublin",
               "Szczecin", "Bydgoszcz", "Białystok", "Rzeszów", "Toruń", "Gdynia", "Bielsko-Biała", "Opole"],
    "Czechia": ["Praha", "Brno", "Ostrava", "Plzeň", "Olomouc", "Liberec"],
    "Germany": ["Berlin", "Potsdam", "Leipzig", "Dresden", "Hamburg", "München"],
}
COUNTRY_VARIANTS = {
    "Poland": ["Poland"] * 8 + ["PL", "Polska", "poland ", " Poland"],
    "Czechia": ["Czechia"] * 6 + ["Czech Republic", "CZ", "Czech Rep."],
    "Germany": ["Germany"] * 6 + ["DE", "Deutschland"],
}

# ---------------------------------------------------------------------------
# FX (PLN per 1 unit of currency) – monthly averages, smooth random walk
# ---------------------------------------------------------------------------


def build_fx(months: list[date]) -> pd.DataFrame:
    n = len(months)
    t = np.linspace(0, 1, n)
    eur_anchor = np.interp(t, [0, 0.25, 0.5, 0.75, 1], [4.71, 4.45, 4.31, 4.27, 4.25])
    czk_anchor = np.interp(t, [0, 0.25, 0.5, 0.75, 1], [0.1965, 0.1860, 0.1720, 0.1705, 0.1712])
    eur = eur_anchor + np.cumsum(rng.normal(0, 0.012, n)) * 0.6
    czk = czk_anchor + np.cumsum(rng.normal(0, 0.0007, n)) * 0.6
    return pd.DataFrame({"MonthStart": months, "EUR": eur.round(4), "CZK": czk.round(4)})


# ---------------------------------------------------------------------------
# Seasonality & mix helpers
# ---------------------------------------------------------------------------
MONTH_SEASON = {1: 0.55, 2: 0.62, 3: 0.92, 4: 1.25, 5: 1.42, 6: 1.36, 7: 1.20, 8: 1.10,
                9: 0.92, 10: 0.76, 11: 1.10, 12: 1.05}
CATEGORY_MIX = {  # base share of "first line" category
    "Bikes": 0.17, "E-Bikes": 0.05, "Components": 0.17, "Apparel": 0.19,
    "Accessories": 0.24, "Nutrition": 0.18,
}
CATEGORY_SEASON = {  # extra seasonal tilt per category
    "Bikes": {3: 1.3, 4: 1.6, 5: 1.6, 6: 1.4, 7: 1.1, 10: 0.6, 11: 0.7, 12: 0.9, 1: 0.5, 2: 0.6},
    "E-Bikes": {3: 1.2, 4: 1.5, 5: 1.5, 6: 1.3, 11: 0.8, 12: 0.9, 1: 0.5, 2: 0.6},
    "Apparel": {9: 1.3, 10: 1.6, 11: 1.6, 12: 1.5, 1: 1.2, 6: 0.8, 7: 0.8},
    "Components": {2: 1.3, 3: 1.4, 4: 1.1},
}
RETURN_RATE = {"Bikes": 0.030, "E-Bikes": 0.025, "Components": 0.040, "Apparel": 0.090,
               "Accessories": 0.030, "Nutrition": 0.005}
RETURN_REASONS = {
    "Apparel": ["Wrong size"] * 6 + ["Changed mind"] * 2 + ["Not as described"],
    "default": ["Defective"] * 3 + ["Damaged in transit"] * 2 + ["Changed mind"] * 2 + ["Not as described"],
}
PRICE_INDEX = {2023: 0.955, 2024: 0.98, 2025: 1.0, 2026: 1.018}


def black_friday(year: int) -> date:
    nov30 = date(year, 11, 30)
    # last Friday of November
    return nov30 - timedelta(days=(nov30.weekday() - 4) % 7)


def trend_factor(d: date, channel: str) -> float:
    years = (d - date(2025, 1, 1)).days / 365.25
    growth = 0.11 if channel != "Store" else 0.03
    return float((1 + growth) ** years)


def weekday_factor(d: date, channel: str, country: str) -> float:
    wd = d.weekday()
    if channel == "Store":
        if wd == 6:  # Sunday trading ban in PL, closed in DE
            return 0.0 if country in ("Poland", "Germany") else 0.7
        return [0.85, 0.85, 0.9, 0.95, 1.1, 1.55][wd]
    return [1.15, 1.05, 1.0, 1.0, 0.95, 0.85, 1.1][wd]


def ramp_up(d: date, open_date: date) -> float:
    if d < open_date:
        return 0.0
    months_open = (d - open_date).days / 30.4
    return float(min(1.0, 0.45 + 0.09 * months_open))


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SALES_DIR.mkdir(parents=True, exist_ok=True)
    for f in SALES_DIR.glob("sales_*.csv"):
        f.unlink()

    products = build_products()
    stores = pd.DataFrame(STORES, columns=STORE_COLS)
    months = [date(y, m, 1) for y in range(2023, 2027) for m in range(1, 13)
              if date(y, m, 1) <= END_DATE]
    fx = build_fx(months)
    fx_lookup = {(r.MonthStart, "EUR"): r.EUR for r in fx.itertuples()}
    fx_lookup.update({(r.MonthStart, "CZK"): r.CZK for r in fx.itertuples()})

    cat_products = {c: products.index[products.Category == c].to_numpy() for c in CATEGORY_MIX}
    attach_pool = products.index[products.Subcategory.isin(["Helmets", "Locks", "Lights", "Bottles & Cages"])].to_numpy()
    p_launch = products.LaunchDate.to_numpy()
    p_disc = products.Discontinued.to_numpy()
    p_pop = products.Popularity.to_numpy()

    # customer pool (pre-allocated arrays)
    cap = 60000
    c_country = np.empty(cap, dtype=object)
    c_signup = np.empty(cap, dtype=object)
    c_churn = np.empty(cap, dtype=object)
    c_weight = np.zeros(cap)
    c_segment = np.empty(cap, dtype=object)
    c_home = np.empty(cap, dtype=object)  # preferred store
    n_cust = 0

    def new_customer(d: date, country: str, store_id: str) -> int:
        nonlocal n_cust
        idx = n_cust
        n_cust += 1
        seg = rng.choice(["Retail", "Club Member", "B2B"], p=[0.84, 0.13, 0.03])
        c_country[idx] = country
        c_signup[idx] = d
        lifetime = rng.exponential(520) if seg != "Retail" else rng.exponential(380)
        c_churn[idx] = d + timedelta(days=int(30 + lifetime))
        w = rng.lognormal(0, 0.9)
        c_weight[idx] = w * (3.0 if seg == "B2B" else 1.6 if seg == "Club Member" else 1.0)
        c_segment[idx] = seg
        c_home[idx] = store_id
        return idx

    lines = []
    order_seq = {}
    d = START_DATE
    while d <= END_DATE:
        season = MONTH_SEASON[d.month]
        bf = black_friday(d.year)
        is_bf = bf <= d <= bf + timedelta(days=3)
        month_start = date(d.year, d.month, 1)
        # active customers per country for repeat orders
        active = {}
        for country in ("Poland", "Czechia", "Germany"):
            idx = np.arange(n_cust)
            if n_cust:
                mask = (c_country[:n_cust] == country) & (c_signup[:n_cust] < d) & (c_churn[:n_cust] > d)
                idx = idx[mask]
            active[country] = idx

        for s in stores.itertuples():
            lam = s.BaseOrders * season * trend_factor(d, s.Channel) * weekday_factor(d, s.Channel, s.Country)
            lam *= ramp_up(d, s.OpenDate)
            if is_bf:
                lam *= 2.6 if s.Channel != "Store" else 1.7
            if d.month == 12 and 10 <= d.day <= 22:
                lam *= 1.25
            n_orders = rng.poisson(lam) if lam > 0 else 0
            for _ in range(n_orders):
                # ---- customer
                cust = None
                if s.Channel == "Store" and rng.random() < 0.30:
                    cust = None  # anonymous walk-in
                else:
                    pool = active[s.Country]
                    p_new = 0.50 - 0.12 * min(1.0, (d - START_DATE).days / 900)
                    if len(pool) < 30 or rng.random() < p_new:
                        cust = new_customer(d, s.Country, s.StoreID)
                    else:
                        w = c_weight[pool]
                        cust = int(pool[rng.choice(len(pool), p=w / w.sum())])
                seg = c_segment[cust] if cust is not None else "Anonymous"

                # ---- order id
                key = d.year
                order_seq[key] = order_seq.get(key, 0) + 1
                order_id = f"SO-{d.year}-{order_seq[key]:06d}"
                if s.Channel == "Store":
                    ship = d
                else:
                    ship = d + timedelta(days=int(rng.integers(1, 5)))

                # ---- lines
                n_lines = rng.choice([1, 2, 3, 4], p=[0.50, 0.28, 0.14, 0.08])
                weights = np.array([CATEGORY_MIX[c] * CATEGORY_SEASON.get(c, {}).get(d.month, 1.0)
                                    * ((1.22 ** ((d - date(2023, 1, 1)).days / 365.25)) if c == "E-Bikes" else 1.0)
                                    for c in CATEGORY_MIX])
                cats = list(CATEGORY_MIX)
                chosen = []
                first_cat = cats[rng.choice(len(cats), p=weights / weights.sum())]
                chosen_cats = [first_cat]
                for _l in range(1, n_lines):
                    if first_cat in ("Bikes", "E-Bikes") and rng.random() < 0.55:
                        chosen_cats.append("__attach__")
                    else:
                        chosen_cats.append(cats[rng.choice(len(cats), p=weights / weights.sum())])
                for c in chosen_cats:
                    pool_p = attach_pool if c == "__attach__" else cat_products[c]
                    avail = pool_p[(p_launch[pool_p] <= d) & np.array([(x is None) or (x > d) for x in p_disc[pool_p]])]
                    if len(avail) == 0:
                        continue
                    pw = p_pop[avail]
                    pi = int(avail[rng.choice(len(avail), p=pw / pw.sum())])
                    if pi in chosen:
                        continue
                    chosen.append(pi)

                for line_no, pi in enumerate(chosen, start=1):
                    p = products.loc[pi]
                    qty = int(rng.integers(p.QtyMin, p.QtyMax + 1))
                    if seg == "B2B":
                        qty = qty * int(rng.integers(2, 6))
                    # discount logic
                    disc = 0.0
                    if is_bf:
                        disc = rng.choice([0.15, 0.2, 0.25, 0.3]) if s.Channel != "Store" else 0.15
                    elif d.month in (9, 10) and p.Category in ("Bikes", "E-Bikes") and rng.random() < 0.4:
                        disc = rng.choice([0.1, 0.15, 0.2])
                    elif d.month == 1 and p.Category == "Apparel" and rng.random() < 0.6:
                        disc = 0.3
                    elif rng.random() < 0.05:
                        disc = rng.choice([0.05, 0.1])
                    if seg == "Club Member":
                        disc = max(disc, 0.05)
                    if seg == "B2B":
                        disc = max(disc, rng.choice([0.08, 0.1, 0.12]))
                    price_pln = p.ListPrice * PRICE_INDEX[d.year]
                    if s.Currency == "PLN":
                        unit_price = round(price_pln, 2)
                    elif s.Currency == "EUR":
                        unit_price = round(price_pln / fx_lookup[(month_start, "EUR")], 2)
                    else:
                        unit_price = float(round(price_pln / fx_lookup[(month_start, "CZK")], 0))
                    lines.append((order_id, line_no, d, ship, s.StoreID,
                                  None if cust is None else f"C{cust + 1:06d}",
                                  p.SKU, qty, unit_price, float(disc), s.Currency, p.Category))
        d += timedelta(days=1)

    sales = pd.DataFrame(lines, columns=["OrderID", "LineNo", "OrderDate", "ShipDate", "StoreID",
                                         "CustomerID", "SKU", "Quantity", "UnitPrice", "DiscountPct",
                                         "Currency", "_Category"])
    print(f"Clean sales lines: {len(sales):,}  orders: {sales.OrderID.nunique():,}  customers: {n_cust:,}")

    # ------------------------------------------------------------------
    # Analytical (clean) values used for budget & inventory generation
    # ------------------------------------------------------------------
    sales["MonthStart"] = sales.OrderDate.map(lambda x: date(x.year, x.month, 1))
    rate = np.where(sales.Currency == "PLN", 1.0,
                    [fx_lookup.get((m, c), 1.0) for m, c in zip(sales.MonthStart, sales.Currency)])
    sales["_NetPLN"] = sales.Quantity * sales.UnitPrice * rate * (1 - sales.DiscountPct)
    country_of_store = stores.set_index("StoreID").Country
    sales["_Country"] = sales.StoreID.map(country_of_store)

    # ------------------------------------------------------------------
    # Returns
    # ------------------------------------------------------------------
    channel_of_store = stores.set_index("StoreID").Channel
    ret_p = sales._Category.map(RETURN_RATE) * np.where(sales.StoreID.map(channel_of_store) == "Store", 1.0, 1.8)
    ret_mask = rng.random(len(sales)) < ret_p
    rets = sales.loc[ret_mask, ["OrderID", "LineNo", "OrderDate", "Quantity", "_Category", "StoreID"]].copy()
    rets["ReturnDate"] = [od + timedelta(days=int(rng.integers(2, 31))) for od in rets.OrderDate]
    rets = rets[rets.ReturnDate <= END_DATE]
    rets["ReturnQty"] = [int(rng.integers(1, q + 1)) for q in rets.Quantity]
    reasons = []
    for cat, sid in zip(rets._Category, rets.StoreID):
        pool = RETURN_REASONS["Apparel"] if cat == "Apparel" else RETURN_REASONS["default"]
        if channel_of_store[sid] == "Store":
            pool = [r for r in pool if r != "Damaged in transit"]
        reasons.append(pool[rng.integers(len(pool))])
    rets["Reason"] = reasons
    rets = rets.sort_values(["ReturnDate", "OrderID", "LineNo"]).reset_index(drop=True)
    rets.insert(0, "ReturnID", [f"RT-{i:06d}" for i in range(1, len(rets) + 1)])
    rets[["ReturnID", "OrderID", "LineNo", "ReturnDate", "ReturnQty", "Reason"]].to_csv(
        RAW_DIR / "returns.csv", index=False, date_format="%Y-%m-%d")

    # ------------------------------------------------------------------
    # Inventory – month-end snapshots per store x SKU
    # ------------------------------------------------------------------
    sales["_SKU"] = sales.SKU
    monthly_units = sales.groupby(["StoreID", "_SKU", "MonthStart"]).Quantity.sum()
    pairs = sales[["StoreID", "_SKU"]].drop_duplicates()
    inv_rows = []
    sku_idx = products.set_index("SKU")
    for m in months:
        snap = date(m.year, m.month, calendar.monthrange(m.year, m.month)[1])
        nxt = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        for sid, sku in pairs.itertuples(index=False):
            p = sku_idx.loc[sku]
            if p.LaunchDate > snap or (p.Discontinued is not None and p.Discontinued + timedelta(days=60) < snap):
                continue
            if stores.set_index("StoreID").OpenDate[sid] > snap:
                continue
            demand = monthly_units.get((sid, sku, nxt), monthly_units.get((sid, sku, m), 0))
            if rng.random() < 0.07:
                qty = 0  # stock-out
            else:
                qty = int(round(demand * rng.uniform(0.6, 1.9) + rng.integers(0, 4)))
            inv_rows.append((snap, sid, sku, qty))
    inventory = pd.DataFrame(inv_rows, columns=["SnapshotDate", "StoreID", "SKU", "StockQty"])
    inventory.to_csv(RAW_DIR / "inventory_snapshots.csv", index=False, date_format="%Y-%m-%d")

    # ------------------------------------------------------------------
    # Budget – based on previous-year actuals x growth target
    # ------------------------------------------------------------------
    sales["_Year"] = sales.OrderDate.map(lambda x: x.year)
    sales["_Month"] = sales.OrderDate.map(lambda x: x.month)
    actual = sales.groupby(["_Country", "_Category", "_Year", "_Month"])._NetPLN.sum()
    country_pl = {"Poland": "Polska", "Czechia": "Czechy", "Germany": "Niemcy"}
    category_pl = {"Bikes": "Rowery", "E-Bikes": "Rowery elektryczne", "Components": "Części",
                   "Apparel": "Odzież", "Accessories": "Akcesoria", "Nutrition": "Odżywki"}
    month_pl = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]
    growth_target = {2024: 1.12, 2025: 1.13, 2026: 1.10}

    wb = Workbook()
    ws_info = wb.active
    ws_info.title = "Notes"
    ws_info["A1"] = "Budżet sprzedaży netto VeloMarket – plik działu Finansów"
    ws_info["A3"] = "Wartości w tys. PLN, po rabatach, przed zwrotami."
    ws_info["A4"] = "Każdy rok w osobnym arkuszu 'Budget RRRR'. Arkusz 'Mapowanie kategorii' zawiera słownik kategorii."
    bold = Font(bold=True)
    head_fill = PatternFill("solid", fgColor="DDEBF7")
    for year, g in growth_target.items():
        ws = wb.create_sheet(f"Budget {year}")
        ws["A1"] = f"Budżet sprzedaży netto – {year} (tys. PLN)"
        ws["A1"].font = Font(bold=True, size=13)
        header = ["Kraj", "Kategoria"] + month_pl + ["Suma"]
        ws.append([])
        ws.append(header)
        for col in range(1, len(header) + 1):
            ws.cell(row=3, column=col).font = bold
            ws.cell(row=3, column=col).fill = head_fill
        col_totals = np.zeros(13)
        for country in ("Poland", "Czechia", "Germany"):
            for cat in CATEGORY_MIX:
                vals = []
                for mth in range(1, 13):
                    base = actual.get((country, cat, year - 1, mth), 0.0)
                    vals.append(round(base * g * rng.uniform(0.96, 1.04) / 1000, 1))
                row = [country_pl[country], category_pl[cat]] + vals + [round(sum(vals), 1)]
                col_totals += np.array(vals + [sum(vals)])
                ws.append(row)
        ws.append(["RAZEM", None] + [round(v, 1) for v in col_totals])
        ws.cell(row=ws.max_row, column=1).font = bold
        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 20
    ws_map = wb.create_sheet("Mapowanie kategorii")
    ws_map.append(["Kategoria PL", "Category"])
    for en, pl in category_pl.items():
        ws_map.append([pl, en])
    wb.save(RAW_DIR / "budget.xlsx")

    # ------------------------------------------------------------------
    # Dirty the sales export & write monthly files
    # ------------------------------------------------------------------
    out = sales[["OrderID", "LineNo", "OrderDate", "ShipDate", "StoreID", "CustomerID", "SKU",
                 "Quantity", "UnitPrice", "DiscountPct", "Currency"]].copy()
    # messy SKUs
    m1 = rng.random(len(out)) < 0.02
    out.loc[m1, "SKU"] = out.loc[m1, "SKU"].str.lower()
    m2 = rng.random(len(out)) < 0.015
    out.loc[m2, "SKU"] = " " + out.loc[m2, "SKU"] + " "
    # legacy SKU not present in the product master
    legacy_idx = rng.choice(out.index[out.OrderDate < date(2023, 4, 1)], 25, replace=False)
    out.loc[legacy_idx, "SKU"] = "VM-OLD-0999"
    out["_File"] = out.OrderDate.map(lambda x: f"sales_{x.year}_{x.month:02d}.csv")
    # duplicates re-exported in the following month's file
    dup = out.sample(frac=0.004, random_state=SEED).copy()

    def next_file(fn: str) -> str:
        y, m = int(fn[6:10]), int(fn[11:13])
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return f"sales_{y}_{m:02d}.csv"

    dup["_File"] = dup._File.map(next_file)
    last_file = f"sales_{END_DATE.year}_{END_DATE.month:02d}.csv"
    valid_files = set(out._File)
    dup = dup[dup._File.isin(valid_files)]
    # QA test orders
    test_rows = []
    for i in range(40):
        td = START_DATE + timedelta(days=int(rng.integers(0, (END_DATE - START_DATE).days)))
        test_rows.append((f"SO-TEST-{i:04d}", 1, td, td, "TEST-01", "TEST-QA",
                          products.SKU.iloc[rng.integers(len(products))], 1, 1.0, 0.0, "PLN",
                          f"sales_{td.year}_{td.month:02d}.csv"))
    test = pd.DataFrame(test_rows, columns=out.columns)
    full = pd.concat([out, dup, test], ignore_index=True)
    full["DiscountPct"] = full.DiscountPct.round(2)
    for fn, g in full.groupby("_File"):
        g = g.drop(columns="_File").sort_values(["OrderDate", "OrderID", "LineNo"])
        g.to_csv(SALES_DIR / fn, index=False, date_format="%Y-%m-%d")
    print(f"Sales files: {full._File.nunique()} (last: {last_file}), raw lines incl. dirt: {len(full):,}")

    # ------------------------------------------------------------------
    # Products (report-style Excel export)
    # ------------------------------------------------------------------
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    ws["A1"] = "VeloMarket – Product Master Export"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = f"Exported from PIM on {datetime(2026, 10, 1, 6, 0):%Y-%m-%d %H:%M}"
    headers = ["Category", "Subcategory", "SKU", "Product Name", "Brand", "Color",
               "List Price (PLN)", "Unit Cost (PLN)", "Launch Date", "Status"]
    ws.append([])
    ws.append(headers)
    for col in range(1, len(headers) + 1):
        ws.cell(row=4, column=col).font = bold
        ws.cell(row=4, column=col).fill = head_fill
    prev_cat, prev_sub = None, None
    for p in products.sort_values(["Category", "Subcategory", "SKU"]).itertuples():
        name = p.ProductName + ("  " if rng.random() < 0.1 else "")
        ws.append([p.Category if p.Category != prev_cat else None,
                   p.Subcategory if p.Subcategory != prev_sub else None,
                   p.SKU, name, p.Brand, p.Color, p.ListPrice, p.UnitCost, p.LaunchDate, p.Status])
        ws.cell(row=ws.max_row, column=9).number_format = "yyyy-mm-dd"
        prev_cat, prev_sub = p.Category, p.Subcategory
    for i, w in enumerate([14, 18, 14, 36, 12, 10, 16, 16, 12, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    wb.create_sheet("Info")["A1"] = "List prices are standard 2025 prices in PLN. Unit cost = standard cost."
    wb.save(RAW_DIR / "products.xlsx")

    # ------------------------------------------------------------------
    # Customers (CRM export with history rows)
    # ------------------------------------------------------------------
    cust_rows = []
    n_never = int(n_cust * 0.04)
    for i in range(n_cust + n_never):
        if i < n_cust:
            country, signup, seg = c_country[i], c_signup[i], c_segment[i]
            home_city = stores.set_index("StoreID").City[c_home[i]]
        else:  # registered but never purchased
            country = rng.choice(["Poland", "Czechia", "Germany"], p=[0.75, 0.13, 0.12])
            signup = START_DATE + timedelta(days=int(rng.integers(0, (END_DATE - START_DATE).days)))
            seg = "Retail"
            home_city = None
        city = home_city if (home_city and rng.random() < 0.55) else CITIES[country][rng.integers(len(CITIES[country]))]
        r = rng.random()
        city_raw = city.lower() if r < 0.06 else city.upper() if r < 0.09 else city
        variants = COUNTRY_VARIANTS[country]
        gender = rng.choice(["M", "F", ""], p=[0.55, 0.38, 0.07])
        birth = "" if rng.random() < 0.08 else int(rng.integers(1955, 2008))
        updated = datetime.combine(signup, datetime.min.time()) + timedelta(hours=int(rng.integers(8, 20)))
        row = [f"C{i + 1:06d}", gender, birth, city_raw, variants[rng.integers(len(variants))], seg,
               signup, rng.choice(["Y", "N"], p=[0.62, 0.38]), updated]
        cust_rows.append(row)
        if rng.random() < 0.015:  # history row: customer moved / changed consent later
            new_city = CITIES[country][rng.integers(len(CITIES[country]))]
            upd2 = updated + timedelta(days=int(rng.integers(30, 600)), hours=3)
            cust_rows.append([row[0], gender, birth, new_city, country, seg, signup,
                              rng.choice(["Y", "N"]), upd2])
    customers = pd.DataFrame(cust_rows, columns=["CustomerID", "Gender", "BirthYear", "City", "Country",
                                                 "Segment", "SignupDate", "MarketingConsent", "UpdatedAt"])
    customers = customers.sample(frac=1.0, random_state=SEED)  # CRM exports are not sorted
    customers["SignupDate"] = customers.SignupDate.map(lambda x: x.strftime("%Y-%m-%d"))
    customers["UpdatedAt"] = customers.UpdatedAt.map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    customers.to_csv(RAW_DIR / "customers.csv", index=False)

    # ------------------------------------------------------------------
    # Stores, FX, security
    # ------------------------------------------------------------------
    stores["SalesAreaM2"] = stores.SalesAreaM2.astype("Int64")
    stores.drop(columns="BaseOrders").to_csv(RAW_DIR / "stores.csv", index=False, date_format="%Y-%m-%d")

    with open(RAW_DIR / "fx_rates_nbp.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write("miesiac;kurs_EUR;kurs_CZK\n")
        for r in fx.itertuples():
            # Polish locale: decimal comma
            f.write(f"{r.MonthStart:%Y-%m};{r.EUR:.4f};{r.CZK:.4f}\n".replace(".", ","))

    pd.DataFrame([
        ("ceo@velomarket.example", "ALL"),
        ("finance@velomarket.example", "ALL"),
        ("manager.pl@velomarket.example", "Poland"),
        ("manager.cz@velomarket.example", "Czechia"),
        ("manager.de@velomarket.example", "Germany"),
        ("director.export@velomarket.example", "Czechia"),
        ("director.export@velomarket.example", "Germany"),
    ], columns=["UserEmail", "Country"]).to_csv(RAW_DIR / "security_users.csv", index=False)

    # ------------------------------------------------------------------
    # Quick sanity summary
    # ------------------------------------------------------------------
    cost = sales.SKU.map(products.set_index("SKU").UnitCost)
    sales["_COGS"] = sales.Quantity * cost
    summary = sales.groupby("_Year").agg(net_pln=("_NetPLN", "sum"), cogs=("_COGS", "sum"),
                                         orders=("OrderID", "nunique"), lines=("OrderID", "size"))
    summary["gm_pct"] = 1 - summary.cogs / summary.net_pln
    print(summary.round(3).to_string())
    print(f"Returns: {len(rets):,}  Inventory rows: {len(inventory):,}  Customers rows: {len(customers):,}")


if __name__ == "__main__":
    main()
