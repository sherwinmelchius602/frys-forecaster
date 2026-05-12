# 🍔 Fry's Burgers — Daily Forecast Dashboard

A data-driven decision tool for Sally Fry's food truck business.  
Built as part of the Capstone Project at **Mahindra University** (SMCC3206, Jan 2026).

---

## What it does

Given today's weather, day type, and festival status — the dashboard:
- **Predicts demand** for all four cities (Hamilton, London, Waterloo, Toronto)
- **Finds the optimal price** ($6–$10) that maximises profit in each city
- **Recommends the best city** to operate in that day
- **Shows breakeven analysis** — how many burgers Sally needs to sell just to cover costs
- **Lets you compare** any two cities head-to-head
- **Exports** the full forecast as a CSV

---

## Project structure

```
frys_forecaster/
│
├── app.py           # Streamlit dashboard (UI only — no logic here)
├── model.py         # All business logic: regression, profit, breakeven
├── requirements.txt # Python dependencies
├── README.md        # This file
└── .gitignore       # Files excluded from GitHub
```

The code is split into two files intentionally:
- `model.py` — the brain. You can read and test it without ever opening the dashboard.
- `app.py` — the face. It only calls functions from `model.py` and displays results.

---

## The model

**Linear Regression** trained on 365 days of Sally's historical sales data.

**Target variable:** Quantity of burgers sold per day

**Features:**
| Feature | Effect |
|---|---|
| Price | −1.94 burgers per $1 increase |
| Rain probability | −27.2 burgers at 100% rain |
| Temperature | −0.26 burgers per °C |
| Festival | +39.3 burgers |
| Weekday (vs weekend) | −7.4 burgers |
| London (vs Hamilton) | +16.5 burgers |
| Waterloo (vs Hamilton) | −9.2 burgers |
| Toronto (vs Hamilton) | +22.8 burgers |

**Model performance:**
- R² training: 0.43
- R² cross-validation: 0.30
- Mean Absolute Error: ±18 burgers
- 89% of predictions land within 30 burgers of actual

---

## How to run locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/frys-forecaster.git
cd frys-forecaster
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the dashboard
```bash
streamlit run app.py
```

The dashboard opens automatically at `http://localhost:8501`

---

## Tech stack

- **Python 3.10+**
- **Streamlit** — dashboard framework
- **Plotly** — interactive charts
- **Pandas / NumPy** — data handling
- **scikit-learn** — linear regression (used offline to train; coefficients are hardcoded)

---

## Case reference

Littleton, J., Wong, S., & Yellin, R. (2016). *Food Truck Forecaster* (Case W16736).  
Ivey Publishing, Richard Ivey School of Business Foundation.
