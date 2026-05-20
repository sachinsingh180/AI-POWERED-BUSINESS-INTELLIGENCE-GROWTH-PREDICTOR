import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from io import BytesIO

# --- PDF GENERATION IMPORTS ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. DATABASE SETUP & AUTOMATIC SAMPLE DATA LOGIC ---
def init_db():
    conn = sqlite3.connect('finance_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            revenue REAL,
            expenses REAL,
            goal REAL
        )
    ''')
    
    # Check if database is empty, if yes, insert 4 months of sample data automatically
    c.execute('SELECT COUNT(*) FROM financials')
    if c.fetchone()[0] == 0:
        sample_records = [
            ('Jan 2026', 45000.0, 30000.0, 20000.0),
            ('Feb 2026', 58000.0, 32000.0, 25000.0),
            ('Mar 2026', 52000.0, 35000.0, 25000.0),
            ('Apr 2026', 65000.0, 31000.0, 30000.0)
        ]
        c.executemany('INSERT INTO financials (month, revenue, expenses, goal) VALUES (?, ?, ?, ?)', sample_records)
        
    conn.commit()
    conn.close()

def save_to_db(month, revenue, expenses, goal):
    conn = sqlite3.connect('finance_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO financials (month, revenue, expenses, goal) VALUES (?, ?, ?, ?)', 
              (month, revenue, expenses, goal))
    conn.commit()
    conn.close()

def fetch_db_data():
    conn = sqlite3.connect('finance_data.db')
    df = pd.read_sql_query("SELECT * FROM financials ORDER BY id ASC", conn)
    conn.close()
    return df

init_db()

TEMP_CSV_PATH = "saved_temp_data.csv"

# --- 2. ADVANCED PDF FUNCTION (UNIVERSAL CONDITIONAL COLOR BARS) ---
def generate_customer_pdf_report(dataframe, cust_col, rev_col, exp_col):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1A365D'), spaceAfter=5
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4A5568'), spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionTitle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#2B6CB0'), spaceBefore=12, spaceAfter=8
    )
    body_style = ParagraphStyle(
        'InvoiceBody', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#2D3748'), leading=14
    )
    
    story.append(Paragraph("📊 SmartBiz AI - Universal Data Audit Report", title_style))
    story.append(Paragraph(f"Custom Performance Analysis for Top {len(dataframe)} Profiles with Dynamic Formats", subtitle_style))
    story.append(Spacer(1, 10))
    
    table_data = [[str(cust_col).upper(), str(rev_col).upper(), str(exp_col).upper(), 'NET OUTPUT']]
    
    total_revenue = 0
    total_expenses = 0
    total_profit = 0
    
    profits_list = []
    for _, row in dataframe.iterrows():
        r = float(row[rev_col]) if pd.notnull(row[rev_col]) else 0.0
        e = float(row[exp_col]) if pd.notnull(row[exp_col]) else 0.0
        profits_list.append(r - e)
        
    max_p_val = max(profits_list) if profits_list else 0
    min_p_val = min(profits_list) if profits_list else 0
    
    max_cust_name = ""
    min_cust_name = ""
    
    cell_style = ParagraphStyle('CellS', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#2D3748'))
    high_style = ParagraphStyle('HighS', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')
    low_style = ParagraphStyle('LowS', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')
    
    t_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#CBD5E0')),
    ]
    
    row_idx = 1
    for _, row in dataframe.iterrows():
        cust_name = str(row[cust_col])
        rev = float(row[rev_col]) if pd.notnull(row[rev_col]) else 0.0
        exp = float(row[exp_col]) if pd.notnull(row[exp_col]) else 0.0
        profit = rev - exp
        
        total_revenue += rev
        total_expenses += exp
        total_profit += profit
        
        p_text = f"₹{profit:,.2f}"
        
        if profit == max_p_val and max_cust_name == "":
            max_cust_name = cust_name
            t_styles.append(('BACKGROUND', (3, row_idx), (3, row_idx), colors.HexColor('#2F855A')))
            p_paragraph = Paragraph(f"{p_text} (MAX)", high_style)
        elif profit == min_p_val and min_cust_name == "":
            min_cust_name = cust_name
            t_styles.append(('BACKGROUND', (3, row_idx), (3, row_idx), colors.HexColor('#C53030')))
            p_paragraph = Paragraph(f"{p_text} (MIN)", low_style)
        else:
            p_paragraph = Paragraph(p_text, cell_style)
            
        table_data.append([
            Paragraph(cust_name, cell_style),
            Paragraph(f"₹{rev:,.2f}", cell_style),
            Paragraph(f"₹{exp:,.2f}", cell_style),
            p_paragraph
        ])
        row_idx += 1
        
    table_data.append([
        Paragraph('GRAND TOTAL CUMULATIVE', high_style),
        Paragraph(f"₹{total_revenue:,.2f}", high_style),
        Paragraph(f"₹{total_expenses:,.2f}", high_style),
        Paragraph(f"₹{total_profit:,.2f}", high_style)
    ])
    
    t_styles.extend([
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#1A365D')),
    ])
    
    fin_table = Table(table_data, colWidths=[160, 120, 120, 120])
    fin_table.setStyle(TableStyle(t_styles))
    
    story.append(Paragraph("📋 Matrix Process Sheet", section_style))
    story.append(fin_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("🤖 Custom AI Diagnostics & Insights", section_style))
    
    ai_msg = (
        f"Portfolio audit complete for <b>{len(dataframe)} unique profile nodes</b>. "
        f"The aggregate data system generated a gross balance of ₹{total_revenue:,.2f} against outgoings of ₹{total_expenses:,.2f}, "
        f"yielding a cumulative net return of <b>₹{total_profit:,.2f}</b>.<br/><br/>"
        f"🟢 <font color='#2F855A'><b>GREEN BAR MARKER (Top Performance):</b></font> Node <b>{max_cust_name}</b> recorded the highest efficiency "
        f"with an individual net margin score of <b>₹{max_p_val:,.2f}</b>.<br/><br/>"
        f"🔴 <font color='#C53030'><b>RED BAR MARKER (Lowest Performance/Risk):</b></font> Node <b>{min_cust_name}</b> recorded the lowest net margin score "
        f"standing at <b>₹{min_p_val:,.2f}</b>. Optimization recommended for this structural element."
    )
    
    story.append(Paragraph(ai_msg, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- 3. APP LAYOUT ---
st.set_page_config(page_title="AI-Powered BI Tool", layout="wide")
st.title("📊 AI-Powered Business Intelligence & Growth Predictor")

# --- 4. REFRESH PROOF NAVIGATION ---
query_params = st.query_params
if "page" not in query_params:
    st.query_params["page"] = "Manual Entry"
    current_page = "Manual Entry"
else:
    current_page = query_params["page"]

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.header("📥 Data Input Section")
modes = ["Manual Entry", "Bulk CSV Upload"]
default_idx = modes.index(current_page) if current_page in modes else 0

def change_url_param():
    st.query_params["page"] = st.session_state["nav_select"]

app_mode = st.sidebar.selectbox("Choose Mode", modes, index=default_idx, key="nav_select", on_change=change_url_param)

# --- 6. MODE 1: MANUAL ENTRY ---
if app_mode == "Manual Entry":
    st.sidebar.subheader("Manual Financial Entry")
    input_month = st.sidebar.text_input("Month (e.g., May 2026)", "May 2026")
    input_revenue = st.sidebar.number_input("Total Revenue (INR)", min_value=0.0, value=50000.0, step=1000.0)
    input_expenses = st.sidebar.number_input("Total Expenses (INR)", min_value=0.0, value=30000.0, step=1000.0)
    input_goal = st.sidebar.number_input("Target Profit Goal (INR)", min_value=0.0, value=25000.0, step=1000.0)
    
    if st.sidebar.button("💾 Save Record to SQL Database"):
        save_to_db(input_month, input_revenue, input_expenses, input_goal)
        st.sidebar.success(f"Data for {input_month} saved in SQL DB!")
        st.rerun()

    current_profit = input_revenue - input_expenses
    profit_margin = (current_profit / input_revenue) * 100 if input_revenue > 0 else 0
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Current Profit", f"₹{current_profit:,.2f}")
    col_kpi2.metric("Profit Margin", f"{profit_margin:.2f}%")
    col_kpi3.metric("Target Goal", f"₹{input_goal:,.2f}")
    
    st.subheader("🤖 SmartBiz AI Insights")
    if current_profit >= input_goal:
        st.success(f"🎉 Goal Achieved! Profit exceeds target by ₹{current_profit - input_goal:,.2f}.")
    else:
        st.error(f"⚠️ Gap Spotted! Short by ₹{input_goal - current_profit:,.2f}. Suggested: Optimize expenses.")

    st.markdown("---")
    st.subheader("📊 Current Month Visual Analytics")
    col_chart1, col_chart2 = st.columns([1.2, 0.8])
    
    with col_chart1:
        chart_data = pd.DataFrame({
            'Category': ['Revenue', 'Expenses', 'Net Profit'],
            'Amount': [input_revenue, input_expenses, current_profit]
        })
        fig_bar = px.bar(chart_data, x='Category', y='Amount', color='Category', 
                         title="Revenue vs Expense Breakdown", text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        pie_data = pd.DataFrame({
            'Type': ['Expenses', 'Net Profit'],
            'Value': [input_expenses, max(0, current_profit)]
        })
        fig_pie = px.pie(pie_data, values='Value', names='Type', hole=0.4, 
                         title="Profit Distribution", color_discrete_sequence=['#ef553b', '#636efa'])
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Business Growth Timeline (Line Trend from Database)")
    db_df = fetch_db_data()
    if not db_df.empty:
        db_df['Net Profit'] = db_df['revenue'] - db_df['expenses']
        fig_line = px.line(db_df, x='month', y=['revenue', 'expenses', 'Net Profit'], 
                           title="Historical Growth Trend Analysis", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

# --- 7. MODE 2: UNIVERSAL BULK CSV UPLOAD ---
else:
    st.subheader("📂 Bulk CSV Data Upload Mode (Universal Mapping Engine)")
    
    uploaded_file = st.sidebar.file_uploader("Upload any CSV file (Sales, Salary, Fees, etc.)", type=["csv"])
    
    if uploaded_file is not None:
        temp_df = pd.read_csv(uploaded_file)
        temp_df.to_csv(TEMP_CSV_PATH, index=False)
        st.sidebar.success("File locked in system cache!")

    if os.path.exists(TEMP_CSV_PATH):
        raw_df = pd.read_csv(TEMP_CSV_PATH)
        all_columns = list(raw_df.columns)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Map CSV Columns Dynamically")
        
        def guess_index(options, key_words, default=0):
            for i, col in enumerate(options):
                if any(kw in col.lower() for kw in key_words):
                    return i
            return default

        idx_name = guess_index(all_columns, ['name', 'customer', 'employee', 'id', 'client', 'month'])
        idx_rev = guess_index(all_columns, ['revenue', 'salary', 'income', 'earning', 'sales'], 1 if len(all_columns) > 1 else 0)
        idx_exp = guess_index(all_columns, ['expense', 'deductions', 'tax', 'cost', 'loss'], 2 if len(all_columns) > 2 else 0)

        cust_col = st.sidebar.selectbox("Select Name / Identifier Column", all_columns, index=idx_name)
        rev_col = st.sidebar.selectbox("Select Inflow / Revenue / Salary Column", all_columns, index=idx_rev)
        exp_col = st.sidebar.selectbox("Select Outflow / Expense / Tax Column", all_columns, index=idx_exp)
        
        total_rows = len(raw_df)
        row_limit = st.sidebar.slider("Select Number of Records to Analyse", 2, min(total_rows, 200), min(total_rows, 10))
        
        st.write(f"### 📋 Current Active Preview ({row_limit} Rows Loaded)")
        st.dataframe(raw_df.head(row_limit), use_container_width=True)
        
        if cust_col and rev_col and exp_col:
            subset = raw_df.head(row_limit).copy()
            subset[rev_col] = pd.to_numeric(subset[rev_col], errors='coerce').fillna(0)
            subset[exp_col] = pd.to_numeric(subset[exp_col], errors='coerce').fillna(0)
            subset['Net Output'] = subset[rev_col] - subset[exp_col]
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("📄 Export Custom Artifacts")
            
            pdf_data = generate_customer_pdf_report(subset, cust_col, rev_col, exp_col)
            
            st.sidebar.download_button(
                label=f"📥 Download Customized Report",
                data=pdf_data,
                file_name=f"SmartBiz_Universal_Report_{row_limit}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.markdown("---")
            st.subheader(f"📊 Visualized Performance Matrix ({row_limit} Rows)")
            
            m = pd.melt(subset, id_vars=[cust_col], value_vars=[rev_col, exp_col, 'Net Output'],
                        var_name='Category', value_name='Amount')
            
            fig_stable_bar = px.bar(m, x=cust_col, y='Amount', color='Category', barmode='group', 
                                    title=f"Dynamic Performance Analytics Dashboard",
                                    text_auto=True)
            st.plotly_chart(fig_stable_bar, use_container_width=True)
            
            highest_earner = subset.loc[subset['Net Output'].idxmax(), cust_col] if not subset.empty else "N/A"
            st.success(f"🤖 AI Data Feed: Analysis complete! **{highest_earner}** has registered the highest peak efficiency score.")
                
        if st.sidebar.button("🗑️ Clear Cache & Reset Page"):
            if os.path.exists(TEMP_CSV_PATH):
                os.remove(TEMP_CSV_PATH)
            st.query_params["page"] = "Manual Entry"
            st.rerun()
    else:
        st.info("Awaiting Data CSV file upload from the sidebar.")

# --- 8. LIVE DATABASE VIEW AT THE BOTTOM (NEVER EMPTY NOW) ---
st.markdown("---")
st.subheader("📜 Project Database Log (SQL Table)")
try:
    db_df = fetch_db_data()
    if not db_df.empty:
        # Showing logs in reverse order so latest entries appear on top
        st.dataframe(db_df.iloc[::-1], use_container_width=True)
except Exception as e:
    st.write("Database log container active.")