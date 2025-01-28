def categorize_investment(value, thresholds, metric_type):
    """Categorizes investment quality based on predefined thresholds."""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "Data not available"

    # Adjust thresholds based on metric type (e.g., Sharpe Ratio, Drawdown, etc.)
    if metric_type == "positive":
        if value > thresholds[1]:
            return "Excellent"
        elif thresholds[0] <= value <= thresholds[1]:
            return "Good"
        else:
            return "Fair"
    elif metric_type == "negative":
        if value < thresholds[0]:
            return "Excellent"
        elif thresholds[0] <= value <= thresholds[1]:
            return "Good"
        else:
            return "Fair"
    else:
        return "Data not available"

def get_investment_color(investment_level):
    """Returns the color associated with an investment quality level."""
    if investment_level == "Excellent":
        return "green"
    elif investment_level == "Good":
        return "yellow"
    elif investment_level == "Fair":
        return "orange"
    else:
        return "black"

def calculate_investment_parameters(stock_symbols):
    """Calculates and categorizes investment parameters for a given stock portfolio."""
    results = []  # Initialize results here for proper scope
    stock_scores = {}
    total_investment_score = 0

    stock_data = fetch_stock_data(stock_symbols)  # Fetch latest stock data

    for stock_symbol in stock_symbols:
        stock_info = df[df['Stock Symbol'] == stock_symbol]

        if stock_info.empty:
            print(f"No data found for stock symbol: {stock_symbol}")
            continue

        stock_info = stock_info.iloc[0]  # Get the first row for the stock

        # Fetch real-time data from Yahoo Finance (Price, Volume, etc.)
        if stock_symbol in stock_data:
            real_time_data = stock_data[stock_symbol].iloc[-1]
            stock_info['Price'] = real_time_data['Close']
            stock_info['Volume'] = real_time_data['Volume']
        else:
            stock_info['Price'] = 'Data not available'
            stock_info['Volume'] = 'Data not available'

        total_stock_score = 0
        summary = {category: {'Excellent': 0, 'Good': 0, 'Fair': 0, 'Data not available': 0} for category in risk_categories}

        # Process each investment category and its parameters
        for category, parameters in risk_categories.items():
            for param, thresholds in parameters.items():
                value = stock_info.get(param)

                if value is not None:
                    investment_level = categorize_investment(value, thresholds, param)

                    results.append({
                        'Stock Symbol': stock_symbol,
                        'Category': category,
                        'Parameter': param,
                        'Value': value,
                        'Investment Level': investment_level,
                        'Color': get_investment_color(investment_level),
                        'Timestamp': datetime.now()
                    })

                    if investment_level == "Excellent":
                        total_investment_score += 2
                        total_stock_score += 2
                    elif investment_level == "Good":
                        total_investment_score += 1
                        total_stock_score += 1
                    elif investment_level == "Fair":
                        total_investment_score -= 1
                        total_stock_score -= 1

        stock_scores[stock_symbol] = total_stock_score  # Save the score for the stock

    return results, stock_scores, total_investment_score

def update_investment_graph(stock_symbols, metrics_data):
    """Updates the live graph with tick-by-tick data reflecting the investment score."""
    fig = go.Figure()
    time_data = [m["Timestamp"] for m in metrics_data]

    for stock_symbol in stock_symbols:
        stock_metrics = [m for m in metrics_data if m["Stock Symbol"] == stock_symbol]
        for metric in ["Annualized Alpha", "Annualized Volatility", "Sharpe Ratio", "Treynor Ratio", "Sortino Ratio", "Max Drawdown", "R-Squared", "Downside Deviation", "Tracking Error", "VaR (95%)"]:
            metric_data = [m["Value"] for m in stock_metrics if m["Parameter"] == metric]
            fig.add_trace(go.Scatter(
                x=time_data,
                y=metric_data,
                mode='lines+markers',
                name=f"{stock_symbol} - {metric}"
            ))

    fig.update_layout(
        title="Live Investment Metrics Over Time",
        xaxis_title="Time",
        yaxis_title="Value",
        legend_title="Stock Symbol & Metric",
        template="plotly_dark",
        showlegend=True,
        xaxis=dict(tickmode='array', tickvals=time_data),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return fig

@app.callback(
    [Output("investment-graph", "figure"),
     Output("investment-table", "data"),
     Output("investment-table", "columns")],
    [Input("stock-dropdown", "value"),
     Input("interval-component", "n_intervals")]
)
def update_investment_graph(selected_stocks, n_intervals):
    global metrics_data_store  # Use global store for real-time updates
    
    # Calculate metrics and investment parameters
    results, stock_scores, total_investment_score = calculate_investment_parameters(selected_stocks)
    
    # Update metrics data store
    for result in results:
        stock_symbol = result["Stock Symbol"]
        metrics_data_store[stock_symbol].append(result)
    
    # Update the live graph with the new tick-by-tick data
    fig = update_investment_graph(selected_stocks, [m for m in metrics_data_store.values()])

    # Define columns dynamically based on the 'results'
    columns = [{"name": col, "id": col} for col in results[0].keys()] if results else []

    return fig, results, columns

# Update the layout to reflect the "investment" terminology
app.layout = html.Div([
    html.H1("Stock Investment & Metrics Dashboard"),
    
    dcc.Dropdown(
        id="stock-dropdown",
        options=[{"label": symbol, "value": symbol} for symbol in df['Stock Symbol'].unique()],
        multi=True,
        placeholder="Select Stock Symbols"
    ),
    
    dcc.Interval(
        id="interval-component",
        interval=60000,  # Update every minute (60000 ms)
        n_intervals=0
    ),
    
    dcc.Graph(id="investment-graph"),
    
    DataTable(
        id="investment-table",
        columns=[],  # Initially no columns
        data=[],  # Initially, no data is displayed
        style_table={'height': '400px', 'overflowY': 'auto'}
    )
])

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
