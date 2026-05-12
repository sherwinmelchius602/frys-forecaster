# model.py
# ─────────────────────────────────────────────────────────────────────────────
# This file contains all the business logic for Fry's Burgers Forecaster.
# It is completely separate from the dashboard — no Streamlit here.
# That way you can test and explain the logic on its own.
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd

# ── 1. REGRESSION COEFFICIENTS ───────────────────────────────────────────────
# These were produced by training a Linear Regression model on 365 days of
# Sally's historical data using sklearn.
#
# How to read them:
#   - INTERCEPT is the baseline prediction when every feature is zero
#   - Each coefficient tells you: "if this feature increases by 1,
#     how many more (or fewer) burgers are sold?"
#
# Example: Price coefficient = -1.9382
#   → Every $1 increase in price → ~2 fewer burgers sold

INTERCEPT = 72.8614

COEFFICIENTS = {
    "Price":        -1.9382,   # higher price = fewer buyers
    "Precip_Prob":  -27.2431,  # higher rain chance = fewer buyers
    "Temperature":  -0.2607,   # colder = slightly fewer buyers
    "Festival":     39.3469,   # festival day = big demand spike
    "Weekday":      -7.3888,   # weekdays sell less than weekends
    "London":       16.5031,   # London sells ~17 more than Hamilton
    "Waterloo":     -9.1535,   # Waterloo sells ~9 fewer than Hamilton
    "Toronto":      22.7715,   # Toronto sells ~23 more than Hamilton
}
# Note: Hamilton has no coefficient because it is the baseline.
# The city dummies (London, Waterloo, Toronto) measure difference FROM Hamilton.


# ── 2. COST STRUCTURE ────────────────────────────────────────────────────────
# From Case Exhibits 1 and 2.

# Food cost per burger = beef + bun + toppings
FOOD_COST = {
    "Hamilton": 2.21 + 0.43 + 0.85,   # $3.49
    "London":   1.30 + 0.25 + 0.50,   # $2.05
    "Waterloo": 1.43 + 0.28 + 0.55,   # $2.26
    "Toronto":  2.60 + 0.50 + 1.00,   # $4.10
}

# Travel cost = distance / fuel efficiency × gas price
# Truck does 5 km per litre, gas = $1.039/litre
TRAVEL_COST = {
    "Hamilton": (5   / 5) * 1.039,    # $1.04
    "London":   (130 / 5) * 1.039,    # $27.01
    "Waterloo": (72  / 5) * 1.039,    # $14.96
    "Toronto":  (70  / 5) * 1.039,    # $14.55
}

PARKING_COST = {
    "Hamilton": 15,
    "London":   0,    # free — Sally's friend's spot
    "Waterloo": 10,
    "Toronto":  25,
}

# Fixed daily cost = travel + parking (does not depend on how many burgers you sell)
FIXED_COST = {
    city: TRAVEL_COST[city] + PARKING_COST[city]
    for city in TRAVEL_COST
}

CITIES = ["Hamilton", "London", "Waterloo", "Toronto"]


# ── 3. CORE FUNCTIONS ────────────────────────────────────────────────────────

def predict_demand(price, city, temperature, precip_prob, festival, weekday):
    """
    Predict how many burgers will sell using the linear regression formula:

        Demand = Intercept
               + (coef_price        × price)
               + (coef_precip       × precip_prob)
               + (coef_temp         × temperature)
               + (coef_festival     × festival)
               + (coef_weekday      × weekday)
               + (coef_city_dummy   × 1 if in that city)

    City dummies: only ONE of London/Waterloo/Toronto is set to 1.
    Hamilton = all three are 0 (it is the baseline).
    """
    london   = 1 if city == "London"   else 0
    waterloo = 1 if city == "Waterloo" else 0
    toronto  = 1 if city == "Toronto"  else 0

    demand = (
        INTERCEPT
        + COEFFICIENTS["Price"]       * price
        + COEFFICIENTS["Precip_Prob"] * precip_prob
        + COEFFICIENTS["Temperature"] * temperature
        + COEFFICIENTS["Festival"]    * festival
        + COEFFICIENTS["Weekday"]     * weekday
        + COEFFICIENTS["London"]      * london
        + COEFFICIENTS["Waterloo"]    * waterloo
        + COEFFICIENTS["Toronto"]     * toronto
    )

    return max(0.0, demand)   # demand can never be negative


def calculate_profit(price, city, temperature, precip_prob, festival, weekday):
    """
    Calculate expected profit for one city at one price point.

    Profit = (Price - Food Cost) × Quantity  -  Fixed Cost
              ↑ margin per burger  ↑ burgers     ↑ travel + parking

    Returns a dictionary with price, quantity, revenue, and profit.
    """
    qty    = predict_demand(price, city, temperature, precip_prob, festival, weekday)
    profit = (price - FOOD_COST[city]) * qty - FIXED_COST[city]

    return {
        "price":   round(price, 2),
        "qty":     round(qty, 1),
        "revenue": round(price * qty, 2),
        "profit":  round(profit, 2),
    }


def find_optimal_price(city, temperature, precip_prob, festival, weekday):
    """
    Try every price from $6.00 to $10.00 in $0.05 steps.
    Return whichever price gives the highest profit.

    This is called a grid search — valid here because profit is a
    smooth curve over the price range, so scanning every step works well.
    """
    best_result = {"profit": -np.inf}

    price = 6.00
    while price <= 10.00 + 1e-9:    # small buffer for floating point
        result = calculate_profit(price, city, temperature, precip_prob, festival, weekday)
        if result["profit"] > best_result["profit"]:
            best_result = result
        price = round(price + 0.05, 4)

    return best_result


def get_breakeven_demand(city, price):
    """
    Minimum burgers needed to cover all costs (profit = 0).

    Solving:  (Price - FoodCost) × Qty = FixedCost
              Qty = FixedCost / (Price - FoodCost)
    """
    margin = price - FOOD_COST[city]
    if margin <= 0:
        return float("inf")          # impossible to break even at this price
    return FIXED_COST[city] / margin


def get_price_curve(city, temperature, precip_prob, festival, weekday):
    """
    Build a table of profit at every price from $6 to $10.
    Used for the price sensitivity chart.
    """
    rows = []
    price = 6.00
    while price <= 10.00 + 1e-9:
        result = calculate_profit(price, city, temperature, precip_prob, festival, weekday)
        rows.append({"Price": round(price, 2), "Profit": result["profit"]})
        price = round(price + 0.25, 4)
    return pd.DataFrame(rows)


def compare_all_cities(temperature, precip_prob, festival, weekday):
    """
    Run find_optimal_price for every city.
    Return a single DataFrame with all results + breakeven + viability.
    This is the main function the dashboard calls.
    """
    rows = []

    for city in CITIES:
        opt = find_optimal_price(city, temperature, precip_prob, festival, weekday)
        be  = get_breakeven_demand(city, opt["price"])
        safety = round(opt["qty"]) - be

        # Viability label
        if safety < 0:
            viability = "🔴 Loss territory"
        elif safety < 10:
            viability = "🟡 Tight margin"
        else:
            viability = "🟢 Comfortable"

        rows.append({
            "City":          city,
            "Optimal Price": opt["price"],
            "Pred. Demand":  round(opt["qty"]),
            "Revenue":       opt["revenue"],
            "Profit":        opt["profit"],
            "Breakeven":     round(be, 1),
            "Safety Margin": round(safety, 1),
            "Viability":     viability,
            "Food Cost":     FOOD_COST[city],
            "Fixed Cost":    round(FIXED_COST[city], 2),
        })

    df = pd.DataFrame(rows)
    df["Recommended"] = df["Profit"] == df["Profit"].max()
    return df
