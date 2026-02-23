import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="AI-POWERED BUSINESS INTELLIGENCE", layout="wide")
st.title("🚀 AI-POWERED BUSINESS INTELLIGENCE AND GROWTH PREDICTOR")

# 2. Sidebar (Control Panel)
st.sidebar.header("🕹️ ADVANCED CONTROL PANEL")
app_mode = st.sidebar.selectbox("Select Analysis Mode", ["Manual Entry", "Bulk Data Upload (CSV)"])
st.sidebar.markdown("---")

if app_mode == "Manual Entry":
    # --- INPUT METRICS (Up) ---
    st.sidebar.subheader("📥 Input Metrics")
    revenue = st.sidebar.number_input("Monthly Revenue (₹)", value=850000)
    expenses = st.sidebar.number_input("Monthly Expenses (₹)", value=420000)
    goal = st.sidebar.number_input("Monthly Profit Goal (₹)", value=500000)
    
    st.sidebar.markdown("---")
    
    # --- SYSTEM SETTINGS (down) ---
    st.sidebar.subheader("🛠️ System Settings")
    risk_level = st.sidebar.select_slider("AI Risk Tolerance", options=["Low", "Medium", "High"])

    if st.sidebar.button("🔄 Re-sync AI Engine"):
        st.sidebar.success("Engine Synced!")
    if st.sidebar.button("📊 Growth Trends"):
        st.sidebar.info("Analyzing trends...")
    if st.sidebar.button("📥 Export PDF Report"):
        st.sidebar.warning("Generating...")

    st.sidebar.color_picker("Customize Theme Color", "#00f900")

    # Calculations
    profit = revenue - expenses
    margin = (profit/revenue)*100 if revenue > 0 else 0
    factor = 1.1 if risk_level == "Low" else 1.25 if risk_level == "Medium" else 1.5
    prediction = revenue * factor

    # Metrics Display
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Current Profit")
        st.header(f"₹{profit:,}")
    with c2:
        st.subheader("Profit Margin")
        st.header(f"{round(margin, 1)}%")
    with c3:
        st.subheader("AI Growth Forecast")
        st.header(f"₹{int(prediction):,}")

    # AI Advisory Box
    st.markdown("---")
    st.subheader("🧠 SmartBiz AI Analysis & Advice")
    if profit >= goal:
        st.success(f"✅ GOAL ACHIEVED! Business is stable in {risk_level} risk mode.")
    else:
        st.warning(f"⚠️ GOAL MISSED! AI suggests reducing expenses by ₹{goal-profit:,}.")

    # --- GRAPHS SECTION ---
    st.markdown("---")
    
    # Row 1: Bar Graph aur Line Graph
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Revenue vs Expenses")
        df_bar = pd.DataFrame({"Category": ["Revenue", "Expenses", "Profit"], "Amount": [revenue, expenses, profit]})
        st.plotly_chart(px.bar(df_bar, x="Category", y="Amount", color="Category", template="plotly_dark"), use_container_width=True)
    
    with col2:
        st.subheader("📈 Growth Trend")
        df_line = pd.DataFrame({"Timeline": ["Current", "Predicted"], "Revenue": [revenue, prediction]})
        st.plotly_chart(px.line(df_line, x="Timeline", y="Revenue", markers=True, template="plotly_dark"), use_container_width=True)

    # Row 2: Pie Chart (Bar Graph in down side)
    st.markdown("---")
    st.subheader("🍕 Expense vs Profit Distribution")
    if revenue > 0:
        df_pie = pd.DataFrame({"Type": ["Expenses", "Net Profit"], "Value": [expenses, profit]})
        fig_pie = px.pie(df_pie, names="Type", values="Value", hole=0.4, 
                         color_discrete_sequence=['#ff4b4b', '#00f900'], template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    # CSV Mode
    st.subheader("📁 Bulk Data Analysis Mode")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        st.write(data.head())
        st.line_chart(data.select_dtypes(include=['number']))

st.sidebar.markdown("---")
st.sidebar.write(f"**System Status:** Active | **Risk:** {risk_level if app_mode == 'Manual Entry' else 'N/A'}")