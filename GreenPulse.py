# Importing Required Libraries

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import io
import re
import unicodedata
from fpdf import FPDF

# Using Gemini API Key
# --------------------
GEMINI_API_KEY = "APi key"  
genai.configure(api_key=GEMINI_API_KEY)


# API Call Function

def call_gemini_api(prompt_text):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")  # NEW correct 1.5 model
    response = model.generate_content(prompt_text)
    return response.text


# Streamlit App Starts

st.set_page_config(page_title="🌱 GreenPulse: Local Policy Simulator", layout="wide")

st.title("🌱 GreenPulse: Local Policy Simulator")
st.subheader("Build a Greener, Healthier City with Smart Policy Choices")


# Sidebar Inputs
st.sidebar.header("🛠️ Policy Control Panel")

tree_plantation = st.sidebar.slider("🌳 Increase Green Cover (%)", 0, 100, 10)
industrialization = st.sidebar.slider("🏭 Industrial Activity (%)", 0, 100, 50)
environment_budget = st.sidebar.slider("💰 Environment Budget Allocation (%)", 0, 50, 10)

ban_diesel = st.sidebar.checkbox("🚗 Ban Diesel Vehicles")
public_transport = st.sidebar.slider("🚌 Public Transport Investment (%)", 0, 100, 10)
more_parks = st.sidebar.slider("🏞️ Park Land Increase (%)", 0, 50, 5)
industrial_fines = st.sidebar.checkbox("⚙️ Enforce Industrial Pollution Fines")

simulate_clicked = st.sidebar.button("🚀 Simulate")

# --- Session State to Handle Simulate (earlier was showing for a blink)
if "simulate" not in st.session_state:
    st.session_state.simulate = False

if simulate_clicked:
    st.session_state.simulate = True

if st.session_state.simulate:

    # Calculations
    aqi_change = - (tree_plantation * 1.5) - (public_transport * 0.5)
    if ban_diesel:
        aqi_change -= 20
    if industrial_fines:
        aqi_change -= 10
    aqi_change += (industrialization * 0.3)

    temp_change = - (tree_plantation * 0.2) - (more_parks * 0.3)
    temp_change += (industrialization * 0.1)

    co2_change = - (public_transport * 0.5)
    if ban_diesel:
        co2_change -= 10
    co2_change += (industrialization * 0.5)

    traffic_change = - (public_transport * 0.5)
    if ban_diesel:
        traffic_change -= 10

    # Gamification Score
    score = 100
    score += (tree_plantation * 0.2) + (public_transport * 0.3) + (more_parks * 0.2)
    score -= (industrialization * 0.3)
    if ban_diesel:
        score += 10
    if industrial_fines:
        score += 5
    score = max(0, min(100, score))  # Keep score between 0 and 100

    # --- Results
    st.success(f"🎯 GreenPulse Score: {score:.0f}/100")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted AQI Change", f"{aqi_change:.1f} points")
        st.metric("City Temperature Change", f"{temp_change:.1f}°C")
    with col2:
        st.metric("CO₂ Emissions Change", f"{co2_change:.1f}%")
        st.metric("Traffic Congestion Change", f"{traffic_change:.1f}%")    

    # Metrics of our report
    st.header("📈 Simulation Results")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Predicted AQI Change", value=f"{aqi_change:.1f} points")
        st.metric(label="City Temperature Change", value=f"{temp_change:.1f}°C")
    with col2:
        st.metric(label="CO₂ Emissions Change", value=f"{co2_change:.1f}%")
        st.metric(label="Traffic Congestion Change", value=f"{traffic_change:.1f}%")

    # Bar Chart
    st.subheader("📊 Visualized Outcomes")

    chart_data = pd.DataFrame({
        'Factor': ['AQI', 'Temperature', 'CO2 Emissions', 'Traffic'],
        'Change': [aqi_change, temp_change, co2_change, traffic_change]
    })

    fig = px.bar(chart_data, x='Factor', y='Change', color='Factor', title="Impact of Your Policies")
    st.plotly_chart(fig, use_container_width=True)

    # Pie Chart for Budget
    pie_data = pd.DataFrame({
        'Sector': ['Environment', 'Other Sectors'],
        'Budget Allocation (%)': [environment_budget, 100 - environment_budget]
    })
    fig_pie = px.pie(pie_data, names='Sector', values='Budget Allocation (%)', title="Budget Distribution")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Timeline / Forecast Graph
    st.subheader("📅 Yearly Forecast: Green Cover %")

    years = list(range(2025, 2031))
    green_cover = [30 + (tree_plantation * 0.2) * (i-2025) for i in years]

    forecast_df = pd.DataFrame({'Year': years, 'Green Cover (%)': green_cover})
    fig_forecast = px.line(forecast_df, x="Year", y="Green Cover (%)", title="Projected Green Cover Over Time")
    st.plotly_chart(fig_forecast, use_container_width=True)

    # Folium Map
    st.subheader("🗺️ City Green Cover Map")
    def generate_map():
        city_map = folium.Map(location=[28.6139, 77.2090], zoom_start=12)
        folium.Circle(
            radius=5000,
            location=[28.6139, 77.2090],
            popup="City Center",
            color="green",
            fill=True,
            fill_color="green",
            fill_opacity=0.4
        ).add_to(city_map)
        return city_map

    st_data = st_folium(generate_map(), width=700, height=500)

    # AI Recommendations
    st.subheader("🤖 Smart AI Recommendations")

    prompt = f"""You are a climate policy expert.
Given the following local policy actions:
- Tree Plantation Increase: {tree_plantation}%
- Industrialization Level: {industrialization}%
- Environment Budget: {environment_budget}%
- Ban Diesel Vehicles: {'Yes' if ban_diesel else 'No'}
- Public Transport Investment: {public_transport}%
- Park Land Increase: {more_parks}%
- Industrial Fines: {'Yes' if industrial_fines else 'No'}
Predict and recommend what actions should the policymakers take to maximize health, environmental and economic outcomes. Be direct, clear, and motivating."""

    try:
        ai_response = call_gemini_api(prompt)
        st.success(ai_response)
    except Exception as e:
        st.error(f"Error fetching AI Recommendation: {e}")
     
    #  Download Report
    st.subheader("📄 Save Your Simulation Report")
    report_content = f"""GreenPulse Simulation Report

GreenPulse Score: {score}/100

AQI Change: {aqi_change:.1f}
Temperature Change: {temp_change:.1f}°C
CO2 Emissions Change: {co2_change:.1f}%
Traffic Congestion Change: {traffic_change:.1f}%

Policy Settings:
- Green Cover Increase: {tree_plantation}%
- Industrial Activity: {industrialization}%
- Environment Budget: {environment_budget}%
- Diesel Ban: {"Enabled" if ban_diesel else "Disabled"}
- Public Transport Investment: {public_transport}%
- Park Land Increase: {more_parks}%
- Industrial Fines: {"Enabled" if industrial_fines else "Disabled"}

AI Recommendations:
{ai_response if 'ai_response' in locals() else "AI generation failed."}
"""

    st.download_button(
        label="💾 Download Report",
        data=report_content,
        file_name="greenpulse_report.txt",
        mime="text/plain"
    ) 

    def clean_text_for_pdf(text):
        text = str(text)  # <<< Convert to string first
        text = unicodedata.normalize("NFKD", text)
        emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        return text

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'GreenPulse Simulation Report', ln=True, align='C')
            self.ln(10)

        def chapter_title(self, title):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, title, ln=True)
            self.ln(4)

        def chapter_body(self, body):
            self.set_font('Arial', '', 12)
            self.multi_cell(0, 10, body)
            self.ln()

    def create_pdf(policy_inputs, results, ai_response):
        pdf = PDF()
        pdf.add_page()

        pdf.chapter_title("Policy Settings")
        for key, value in policy_inputs.items():
            pdf.chapter_body(f"{clean_text_for_pdf(key)}: {clean_text_for_pdf(value)}")

        pdf.chapter_title("Simulation Results")
        for key, value in results.items():
            pdf.chapter_body(f"{clean_text_for_pdf(key)}: {clean_text_for_pdf(value)}")

        pdf.chapter_title("AI Recommendations")
        pdf.chapter_body(clean_text_for_pdf(ai_response))

        return pdf.output(dest='S').encode('latin1')

        # Prepare policy inputs and results for PDF
    policy_inputs = {
        "Green Cover Increase (%)": tree_plantation,
        "Industrial Activity (%)": industrialization,
        "Environment Budget (%)": environment_budget,
        "Ban Diesel Vehicles": "Yes" if ban_diesel else "No",
        "Public Transport Investment (%)": public_transport,
        "Park Land Increase (%)": more_parks,
        "Industrial Pollution Fines": "Yes" if industrial_fines else "No"
    }

    results = {
        "AQI Change (points)": round(aqi_change, 1),
        "Temperature Change (°C)": round(temp_change, 1),
        "CO₂ Emissions Change (%)": round(co2_change, 1),
        "Traffic Congestion Change (%)": round(traffic_change, 1),
        "GreenPulse Score": round(score, 1),
    }

    pdf_file = create_pdf(policy_inputs, results, ai_response if 'ai_response' in locals() else "AI generation failed.")

    st.download_button(
        label="⬇️ Download Detailed PDF",
        data=pdf_file,
        file_name="greenpulse_detailed_report.pdf",
        mime="application/pdf",
    )
# If not simulated yet, prompt this
else:
    st.info("👈 Adjust policies and click 'Simulate' to see results!")
