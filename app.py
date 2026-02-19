import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="WMS Site Validation Dashboard", layout="wide")

DATA_FILE = 'site_records.csv'

# --- DATA MANAGEMENT FUNCTIONS ---
def load_data():
    # Create a dummy CSV with structure if it doesn't exist
    if not os.path.exists(DATA_FILE):
        data = {
            'Sr_No': [1, 2, 3, 4, 5],
            'Site Name': ['Site-A (North)', 'Site-B (South)', 'Site-C (East)', 'Site-D (West)', 'Site-E (North)'],
            'Validation Report': ['Validated', 'Failed', 'Validated', 'Failed', 'Pending'],
            'Issue Sensors': ['Temp Sensor', 'None', 'Humidity Sensor', 'Pressure Sensor', 'None'],
            'WMS_Type': ['WMS-1', 'WMS-2', 'WMS-1', 'WMS-2', 'WMS-1'],
            'Issue_Description': ['Calibration Drift', 'No Issues', 'Connector Fault', 'Power Failure', 'No Issues'],
            'Date_Logged': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05', '2023-05-12']
        }
        df = pd.DataFrame(data)
        df.to_csv(DATA_FILE, index=False)
    
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Load data
df = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard Overview", "Site Validation & Search"])

# --- PAGE 1: DASHBOARD OVERVIEW ---
if page == "Dashboard Overview":
    st.title("📊 3-Year Data Report Dashboard")
    st.markdown("---")

    # 1. KPI CARDS SECTION
    col1, col2, col3, col4 = st.columns(4)
    
    total_sites = len(df)
    sites_with_issue = df[df['Validation Report'] == 'Failed'].shape[0]
    wms1_issues = df[df['WMS_Type'] == 'WMS-1'].shape[0]
    wms2_issues = df[df['WMS_Type'] == 'WMS-2'].shape[0]

    with col1:
        st.metric(label="Total Sites Monitored", value=total_sites)
    with col2:
        st.metric(label="Sites with Issue", value=sites_with_issue, delta_color="inverse")
    with col3:
        st.metric(label="WMS-1 Units", value=wms1_issues)
    with col4:
        st.metric(label="WMS-2 Units", value=wms2_issues)

    st.markdown("---")

    # 2. CHARTS SECTION
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Issue Analysis by Sensor Type")
        # Filter only failed/issue sites for analysis
        issue_df = df[df['Issue Sensors'] != 'None']
        if not issue_df.empty:
            fig_sensor = px.pie(issue_df, names='Issue Sensors', title='Distribution of Faulty Sensors')
            st.plotly_chart(fig_sensor, use_container_width=True)
        else:
            st.info("No sensor issues found.")

    with c2:
        st.subheader("WMS-1 vs WMS-2 Failure Analysis")
        # Compare WMS types involved in failures
        if not issue_df.empty:
            fig_wms = px.histogram(issue_df, x='WMS_Type', color='Validation Report', barmode='group', title="Failures by WMS Type")
            st.plotly_chart(fig_wms, use_container_width=True)
        else:
            st.info("No data to compare.")

    # 3. CORRELATION & TOP ISSUES
    st.subheader("Failure Correlation: Top Issues")
    if not issue_df.empty:
        top_issues = issue_df['Issue_Description'].value_counts().reset_index()
        top_issues.columns = ['Issue Description', 'Count']
        
        fig_bar = px.bar(top_issues, x='Issue Description', y='Count', color='Count', title="Top Reported Issues")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("System is running smoothly with no major issues.")

# --- PAGE 2: SITE VALIDATION & SEARCH ---
elif page == "Site Validation & Search":
    st.title("🔍 Site Validation Details")
    
    # Search Section
    st.subheader("Search Records")
    search_term = st.text_input("Search by Site Name, Sensor, or WMS Type", placeholder="Type to search...")
    
    # Filter Logic
    if search_term:
        # Create a boolean mask for case-insensitive search
        mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    # Display Data Table
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        column_config={
            "Sr_No": st.column_config.NumberColumn("Sr. No.", format="%d"),
            "Date_Logged": st.column_config.DateColumn("Date Logged", format="D MMM YYYY")
        }
    )
    
    st.markdown("---")

    # Add New Record Section
    with st.expander("➕ Add New Site Record"):
        with st.form("add_record_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_site = st.text_input("Site Name")
                new_val = st.selectbox("Validation Report", ["Validated", "Failed", "Pending"])
                new_wms = st.selectbox("WMS Type", ["WMS-1", "WMS-2"])
            with col2:
                new_sensor = st.text_input("Issue Sensors (e.g., Temp Sensor)")
                new_issue_desc = st.text_input("Issue Description")
                submitted = st.form_submit_button("Save Record")

            if submitted:
                if new_site:
                    new_data = {
                        'Sr_No': int(df['Sr_No'].max() + 1),
                        'Site Name': new_site,
                        'Validation Report': new_val,
                        'Issue Sensors': new_sensor if new_sensor else "None",
                        'WMS_Type': new_wms,
                        'Issue_Description': new_issue_desc if new_issue_desc else "No Issues",
                        'Date_Logged': datetime.today().strftime('%Y-%m-%d')
                    }
                    # Append new data (No need for global keyword here)
                    new_row = pd.DataFrame([new_data])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"Record for {new_site} saved successfully!")
                    st.rerun() # Refresh page to show new data
                else:
                    st.error("Site Name is required.")

    # Delete Functionality
    st.subheader("⚠️ Manage Data")
    site_to_delete = st.selectbox("Select Site to Delete", df['Site Name'].unique())
    if st.button("Delete Selected Site"):
        df = df[df['Site Name'] != site_to_delete]
        save_data(df)
        st.warning(f"Deleted {site_to_delete}")
        st.rerun()
