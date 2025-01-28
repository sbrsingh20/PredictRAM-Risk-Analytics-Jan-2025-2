import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Read data from the original Excel file
file_path = "merged_stock_data_with_categories_in_cells_nov2024.xlsx"
df = pd.read_excel(file_path)

# Read data from the additional Excel file with calculated metrics
metrics_file_path = "calculated_stock_metrics_full.xlsx"
metrics_df = pd.read_excel(metrics_file_path)

# Categories and risk thresholds from the original code
risk_categories = {
    "Market Risk": {
        "Volatility": (0.1, 0.2),
        "Beta": (0.5, 1.5),
        "Correlation with ^NSEI": (0.7, 1),
    },
    "Financial Risk": {
        "debtToEquity": (0.5, 1.5),
        "currentRatio": (1.5, 2),
        "quickRatio": (1, 1.5),
        "Profit Margins": (20, 30),
        "returnOnAssets": (10, 20),
        "returnOnEquity": (15, 25),
    },
    "Liquidity Risk": {
        "Volume": (1_000_000, float('inf')),
        "Average Volume": (500_000, 1_000_000),
        "marketCap": (10_000_000_000, float('inf')),
    },
}

def categorize_risk(value, thresholds):
    """Categorizes risk based on predefined thresholds."""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "Data not available"

    if value < thresholds[0]:
        return "Good"
    elif thresholds[0] <= value <= thresholds[1]:
        return "Neutral"
    else:
        return "Bad"

def get_risk_color(risk_level):
    """Returns the color associated with a risk level."""
    if risk_level == "Good":
        return "green"
    elif risk_level == "Neutral":
        return "yellow"
    elif risk_level == "Bad":
        return "red"
    else:
        return "black"

def calculate_risk_parameters(stock_symbols):
    """Calculates and categorizes risk parameters for a given stock portfolio."""
    results = []
    stock_scores = {}
    category_scores = {category: 0 for category in risk_categories}
    total_portfolio_score = 0

    # Iterate over each stock symbol
    for stock_symbol in stock_symbols:
        # Get data from Excel file
        stock_info = df[df['Stock Symbol'] == stock_symbol]

        if stock_info.empty:
            print(f"No data found for stock symbol: {stock_symbol}")
            continue

        stock_info = stock_info.iloc[0]  # Get the first row for the stock

        # Initialize summary for the stock
        total_stock_score = 0
        summary = {category: {'Good': 0, 'Neutral': 0, 'Bad': 0, 'Data not available': 0} for category in risk_categories}

        # Process each risk category and its parameters
        for category, parameters in risk_categories.items():
            for param, thresholds in parameters.items():
                value = stock_info.get(param)

                if value is not None:
                    risk_level = categorize_risk(value, thresholds)
                    summary[category][risk_level] += 1
                    results.append({
                        'Stock Symbol': stock_symbol,
                        'Category': category,
                        'Parameter': param,
                        'Value': value,
                        'Risk Level': risk_level,
                        'Color': get_risk_color(risk_level)
                    })

                    if risk_level == "Good":
                        category_scores[category] += 1
                        total_portfolio_score += 1
                        total_stock_score += 1
                    elif risk_level == "Bad":
                        category_scores[category] -= 1
                        total_portfolio_score -= 1
                        total_stock_score -= 1
                else:
                    results.append({
                        'Stock Symbol': stock_symbol,
                        'Category': category,
                        'Parameter': param,
                        'Value': 'Data not available',
                        'Risk Level': 'Data not available',
                        'Color': 'black'
                    })
                    summary[category]['Data not available'] += 1

        stock_scores[stock_symbol] = total_stock_score  # Save the score for the stock

    return results, category_scores, stock_scores, total_portfolio_score

# Streamlit UI components
st.title("Stock Risk Analysis Dashboard")

# Dropdown to select stocks
selected_stocks = st.multiselect(
    "Select stocks",
    options=df['Stock Symbol'].unique(),
    default=df['Stock Symbol'].unique()[0]
)

# Calculate risk parameters for the selected stocks
results, category_scores, stock_scores, total_portfolio_score = calculate_risk_parameters(selected_stocks)

# Display the summary
st.subheader("Summary")
summary_text = f"Total Portfolio Score: {total_portfolio_score}\n"
for category, score in category_scores.items():
    summary_text += f"{category}: {score}\n"
st.text(summary_text)

# Add Risk Meter (Example for one stock)
def plot_risk_meter(stock_symbol):
    stock_info = df[df['Stock Symbol'] == stock_symbol].iloc[0]
    stock_score = stock_scores.get(stock_symbol, 0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stock_score,
        gauge={
            "axis": {"range": [None, 5]},
            "bar": {"color": "black"},
            "steps": [
                {"range": [0, 2], "color": "green"},
                {"range": [2, 4], "color": "yellow"},
                {"range": [4, 5], "color": "red"},
            ],
        },
        title={"text": f"Risk Meter for {stock_symbol}"},
    ))
    st.plotly_chart(fig)

# Display risk meters for selected stocks
for stock_symbol in selected_stocks:
    plot_risk_meter(stock_symbol)

# Display Pie Charts for Risk Distribution
def plot_risk_pie_chart(category):
    filtered_results = [r for r in results if r['Category'] == category]
    risk_levels = ['Good', 'Neutral', 'Bad', 'Data not available']
    counts = {risk: 0 for risk in risk_levels}

    for result in filtered_results:
        counts[result['Risk Level']] += 1

    fig = px.pie(names=risk_levels, values=list(counts.values()), title=f"{category} Risk Distribution")
    st.plotly_chart(fig)

# Display pie charts for each risk category
for category in risk_categories.keys():
    plot_risk_pie_chart(category)

# Radar Chart for Stock Metrics Comparison
def plot_radar_chart(stock_symbols):
    radar_data = metrics_df[metrics_df['Stock Symbol'].isin(stock_symbols)]

    if not radar_data.empty:
        radar_metrics = ['Annualized Alpha (%)', 'Sharpe Ratio (Daily)', 'Beta', 'Volatility', 'Profit Margins']
        
        # Check if all radar metrics columns are present in the data
        existing_columns = [col for col in radar_metrics if col in radar_data.columns]

        if not existing_columns:
            st.warning("None of the radar metrics are available in the dataset.")
            return
        
        # Filter the data to include only existing columns in radar_metrics
        radar_data = radar_data[["Stock Symbol"] + existing_columns]

        fig = go.Figure()

        # Adding data for each stock
        for stock in stock_symbols:
            stock_data = radar_data[radar_data['Stock Symbol'] == stock].drop(columns="Stock Symbol")
            fig.add_trace(go.Scatterpolar(
                r=stock_data.iloc[0],
                theta=existing_columns,
                fill='toself',
                name=stock
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
            ),
            showlegend=True,
            title="Radar Chart for Stock Metrics Comparison"
        )
        st.plotly_chart(fig)

# Display Radar Chart for selected stocks
plot_radar_chart(selected_stocks)

# Additional Investment Score Visualization
investment_data = [{"Stock Symbol": stock, "Investment Score": score} for stock, score in stock_scores.items()]
investment_df = pd.DataFrame(investment_data)
fig = px.bar(investment_df, x="Stock Symbol", y="Investment Score", title="Investment Scores for Selected Stocks")
st.plotly_chart(fig)
