import pandas as pd
from sklearn.linear_model import LinearRegression

# Load Excel file
df = pd.read_excel(
    "data/Food Truck Forecaster.xlsx",
    sheet_name="Hist_Data",
    header=2
)

# Preview first rows
print(df.head())

# Features
X = df[[
    "Price",
    "Probability of Precipitation",
    "Temperature",
    "Festival",
    "Weekday",
    "London",
    "Waterloo",
    "Toronto"
]]

# Target variable
y = df["Quantity Sold"]

# Train model
model = LinearRegression()
model.fit(X, y)

# Show results
print("\nIntercept:")
print(round(model.intercept_, 4))

print("\nCoefficients:")

for feature, coef in zip(X.columns, model.coef_):
    print(f"{feature}: {round(coef, 4)}")