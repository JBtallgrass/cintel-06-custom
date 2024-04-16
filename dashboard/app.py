# Imports
import requests
from shiny import reactive, render
from shiny.express import ui
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly, render_widget
from scipy import stats
from ipyleaflet import Map
from faicons import icon_svg

# Constants
UPDATE_INTERVAL_SECS: int = 900  # 15 minutes
DEQUE_SIZE: int = 5

# Initialize reactive value
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))
#--------------------------------------------------------------------
# Import API_KEY from config module
from config import API_KEY
def fetch_weather_data(city="Kansas City"):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,  # Use the imported API_KEY
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    return response.json()    

# Reactive calculation for updating weather data
@reactive.calc()
def reactive_calc_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)
    weather_data = fetch_weather_data()  # Fetch real-time weather data
    temp = weather_data["main"]["temp"]  # Get temperature
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_dictionary_entry = {"temp": temp, "timestamp": timestamp}
    reactive_value_wrapper.get().append(new_dictionary_entry)
    deque_snapshot = reactive_value_wrapper.get()
    df = pd.DataFrame(deque_snapshot)
    return deque_snapshot, df, new_dictionary_entry

# Define the Shiny UI Page layout
ui.page_opts(title="PyShiny: Live Weather Data Example", fillable=True)

with ui.sidebar(open="open"):
    ui.h2("Kansas City Weather", class_="text-center")
    ui.p("Real-time weather data for Kansas City.", class_="text-center")
    ui.hr()
    ui.h6("Links:")
    ui.a("GitHub Source", href="https://github.com/JBtallgrass/cintel-06-custom/blob/main/dashboard/app.py", target="_blank")
    ui.a("GitHub App", href="", target="_blank")

with ui.layout_columns():
    with ui.h2("Kansas City Weather: Live Data"):
        @render_widget
        def map_widget(width="50%", height="50%"):
            return Map(center=(39.0997, -94.5786), zoom=10)

    with ui.value_box(showcase=icon_svg("sun"), theme="bg-gradient-blue-purple"):
        "Current Temperature"
        @render.text
        def display_temp():
            _, _, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['temp']} °C"

    with ui.card(full_screen=True):
        ui.card_header("Current Date and Time")
        @render.text
        def display_time():
            _, _, latest_dictionary_entry = reactive_calc_combined()
            return latest_dictionary_entry["timestamp"]

    with ui.card(full_screen=True):
        ui.card_header("Most Recent Readings")
        @render.data_frame
        def display_df():
            _, df, _ = reactive_calc_combined()
            pd.set_option('display.width', None)  # Use maximum width
            return render.DataGrid(df, width="100%")

    with ui.card():
        ui.card_header("Chart with Current Trend")
        @render_plotly
        def display_plot():
            _, df, _ = reactive_calc_combined()
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                fig = px.scatter(df, x="timestamp", y="temp", title="Temperature Readings with Regression Line", labels={"temp": "Temperature (°C)", "timestamp": "Time"}, color_discrete_sequence=["blue"])
                sequence = range(len(df))
                x_vals, y_vals = list(sequence), df["temp"]
                slope, intercept, _, _, _ = stats.linregress(x_vals, y_vals)
                df['best_fit_line'] = [slope * x + intercept for x in x_vals]
                fig.add_scatter(x=df["timestamp"], y=df['best_fit_line'], mode='lines', name='Regression Line')
                fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)")
                return fig
