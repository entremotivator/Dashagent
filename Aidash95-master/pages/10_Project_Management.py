import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from utils.auth import require_auth
from utils.gsheet_manager import get_sheets_manager
from components.data_scanner_ui import DataScannerUI
from io import BytesIO
from fpdf import FPDF # For PDF export

@require_auth
def main():
    st.title("📋 Project Management Suite")
    st.markdown("Comprehensive project tracking and management with Google Sheets integration")
    
    # Initialize sheets manager
    sheets_manager = get_sheets_manager()
    
    # Check for global credentials
    if not st.session_state.get("global_gsheets_creds"):
        st.error("🔑 Google Sheets credentials not found. Please upload your service account JSON in the sidebar.")
        st.info("💡 Use the sidebar to upload your service account JSON file for full functionality.")
        st.stop()
    
    # Initialize default configuration if not present
    initialize_default_config()
    
    # Auto-load data on app start
    auto_load_project_data(sheets_manager)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", "📋 Project List", "📈 Analytics", "➕ Add Project", "⚙️ Settings", "🔍 Data Scanner"
    ])
    
    with tab1:
        render_overview_tab(sheets_manager)
    
    with tab2:
        render_project_list_tab(sheets_manager)
    
    with tab3:
        render_analytics_tab(sheets_manager)
    
    with tab4:
        render_add_project_tab(sheets_manager)
    
    with tab5:
        render_settings_tab(sheets_manager)
    
    with tab6:
        render_data_scanner_tab()

def initialize_default_config():
    """Initialize default configuration values for projects"""
    if 'project_sheet_url' not in st.session_state:
        st.session_state.project_sheet_url = "" # User should configure this
    
    if 'project_worksheet_name' not in st.session_state:
        st.session_state.project_worksheet_name = ""
    
    if 'project_auto_load_enabled' not in st.session_state:
        st.session_state.project_auto_load_enabled = True
    
    if 'project_last_auto_load' not in st.session_state:
        st.session_state.project_last_auto_load = None

def auto_load_project_data(sheets_manager):
    """Automatically load project data if conditions are met"""
    try:
        if not st.session_state.get('project_auto_load_enabled', True):
            return
        
        if ('project_data' in st.session_state and 
            st.session_state.project_data is not None and
            'project_last_auto_load' in st.session_state and
            st.session_state.project_last_auto_load):
            
            time_since_load = datetime.now() - st.session_state.project_last_auto_load
            if time_since_load.total_seconds() < 300:  # 5 minutes cache
                return
        
        sheet_url = st.session_state.get('project_sheet_url', '')
        worksheet_name = st.session_state.get('project_worksheet_name', '')
        
        if not sheet_url:
            return
        
        with st.spinner("🔄 Auto-loading project data..."):
            df = sheets_manager.get_sheet_data(
                sheet_id=sheet_url,
                worksheet_name=worksheet_name if worksheet_name else None,
                use_cache=True
            )
            
            if df is not None and not df.empty:
                st.session_state.project_data = df
                st.session_state.project_last_auto_load = datetime.now()
                
                success_placeholder = st.empty()
                success_placeholder.success(f"✅ Auto-loaded {len(df):,} project records")
                import time
                time.sleep(3)
                success_placeholder.empty()
            else:
                st.warning("⚠️ Auto-load: No project data found or sheet is empty")
                
    except Exception as e:
        st.error(f"❌ Auto-load failed: {str(e)}")

def force_reload_project_data(sheets_manager):
    """Force reload of project data"""
    try:
        sheet_url = st.session_state.get('project_sheet_url', '')
        worksheet_name = st.session_state.get('project_worksheet_name', '')
        
        if not sheet_url:
            st.error("❌ No sheet URL configured for projects")
            return
        
        with st.spinner("🔄 Reloading project data..."):
            sheets_manager.clear_cache()
            
            df = sheets_manager.get_sheet_data(
                sheet_id=sheet_url,
                worksheet_name=worksheet_name if worksheet_name else None,
                use_cache=False
            )
            
            if df is not None and not df.empty:
                st.session_state.project_data = df
                st.session_state.project_last_auto_load = datetime.now()
                st.success(f"✅ Reloaded {len(df):,} project records")
                st.rerun()
            else:
                st.error("❌ No project data found or sheet is empty")
                
    except Exception as e:
        st.error(f"❌ Error reloading data: {str(e)}")

def update_configuration(sheets_manager, sheet_url, worksheet_name, auto_load):
    """Update configuration and optionally reload data"""
    try:
        st.session_state.project_sheet_url = sheet_url
        st.session_state.project_worksheet_name = worksheet_name
        st.session_state.project_auto_load_enabled = auto_load
        
        st.success("✅ Project configuration updated!")
        
        if auto_load and sheet_url:
            force_reload_project_data(sheets_manager)
        
    except Exception as e:
        st.error(f"❌ Error updating configuration: {str(e)}")

def create_sample_project_data():
    """Create sample project data for demonstration"""
    return pd.DataFrame({
        'Project Name': ['Website Redesign', 'Marketing Campaign', 'Product Launch', 'Internal Tool Dev', 'Client Onboarding'],
        'Description': ['Revamp company website for modern look', 'Launch new digital marketing ads', 'Introduce new software product to market', 'Develop internal CRM system', 'Streamline new client setup process'],
        'Status': ['In Progress', 'Not Started', 'On Hold', 'Completed', 'In Progress'],
        'Start Date': ['2024-01-01', '2024-02-15', '2024-03-01', '2023-11-01', '2024-04-10'],
        'Due Date': ['2024-06-30', '2024-05-31', '2024-09-30', '2024-02-28', '2024-05-15'],
        'Assigned To': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'Priority': ['High', 'Medium', 'High', 'Low', 'Medium'],
        'Budget': [15000, 8000, 25000, 5000, 3000],
        'Actual Cost': [12000, 0, 5000, 4800, 1000],
        'Notes': ['Focus on UX/UI', 'Needs content strategy', 'Requires extensive testing', 'Deployed successfully', 'Waiting for client data']
    })

def render_overview_tab(sheets_manager):
    """Render project overview dashboard"""
    st.subheader("📊 Project Overview")
    
    with st.expander("⚙️ Data Source Configuration", expanded=False):
        st.info("💡 Data is automatically loaded. Modify settings below if needed.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_sheet_url = st.text_input(
                "Project Sheet URL/ID",
                value=st.session_state.get('project_sheet_url', ''),
                help="Enter your project data Google Sheet URL or ID"
            )
            
            new_worksheet_name = st.text_input(
                "Worksheet Name (optional)",
                value=st.session_state.get('project_worksheet_name', ''),
                placeholder="Projects",
                help="Leave empty for first worksheet"
            )
        
        with col2:
            auto_load = st.checkbox(
                "🔄 Auto-load enabled",
                value=st.session_state.get('project_auto_load_enabled', True),
                help="Automatically load data when app starts"
            )
            
            if st.button("💾 Update Config", type="primary", use_container_width=True):
                update_configuration(sheets_manager, new_sheet_url, new_worksheet_name, auto_load)
            
            if st.button("🔄 Reload Now", use_container_width=True):
                force_reload_project_data(sheets_manager)
    
    if 'project_data' not in st.session_state or st.session_state.project_data is None:
        st.info("📋 No project data loaded yet. Configure your data source above or wait for auto-load.")
        if st.button("Generate Sample Data"):
            st.session_state.project_data = create_sample_project_data()
            st.session_state.project_last_auto_load = datetime.now()
            st.success("Sample project data loaded!")
            st.rerun()
        return
    
    df = st.session_state.project_data
    
    if 'project_last_auto_load' in st.session_state and st.session_state.project_last_auto_load:
        last_update = st.session_state.project_last_auto_load.strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"📅 Last updated: {last_update}")
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Total Projects", len(df))
    
    with col2:
        in_progress = len(df[df['Status'].str.contains('In Progress', case=False, na=False)])
        st.metric("⏳ In Progress", in_progress)
    
    with col3:
        completed = len(df[df['Status'].str.contains('Completed', case=False, na=False)])
        st.metric("✅ Completed", completed)
    
    with col4:
        # Calculate overdue projects
        overdue = 0
        if 'Due Date' in df.columns:
            try:
                df['Due Date'] = pd.to_datetime(df['Due Date'], errors='coerce')
                overdue = len(df[(df['Due Date'] < datetime.now()) & (~df['Status'].str.contains('Completed|Cancelled', case=False, na=False))])
            except:
                pass
        st.metric("🚨 Overdue", overdue)
    
    with col5:
        # Calculate average completion time
        avg_completion_time = "N/A"
        if 'Start Date' in df.columns and 'Due Date' in df.columns and 'Status' in df.columns:
            completed_projects = df[df['Status'].str.contains('Completed', case=False, na=False)].copy()
            try:
                completed_projects['Start Date'] = pd.to_datetime(completed_projects['Start Date'], errors='coerce')
                completed_projects['Due Date'] = pd.to_datetime(completed_projects['Due Date'], errors='coerce')
                
                completed_projects = completed_projects.dropna(subset=['Start Date', 'Due Date'])
                if not completed_projects.empty:
                    completion_durations = (completed_projects['Due Date'] - completed_projects['Start Date']).dt.days
                    if not completion_durations.empty:
                        avg_completion_time = f"{completion_durations.mean():.0f} days"
            except:
                pass
        st.metric("⏱️ Avg Completion", avg_completion_time)
    
    st.divider()
    
    # Recent projects preview
    st.subheader("👀 Recent Projects")
    display_cols = [col for col in ['Project Name', 'Status', 'Due Date', 'Assigned To', 'Priority'] if col in df.columns]
    if not df.empty and display_cols:
        st.dataframe(df[display_cols].head(10), use_container_width=True)
    else:
        st.info("No project data to display.")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Analyze Data", use_container_width=True):
            st.session_state.show_project_scanner = True
            st.rerun()
    
    with col2:
        if st.button("📤 Export CSV", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                csv,
                f"projects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col3:
        if st.button("📄 Export PDF", use_container_width=True):
            pdf_bytes = create_project_pdf(df)
            if pdf_bytes:
                st.download_button(
                    "💾 Download PDF",
                    pdf_bytes,
                    f"project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    "application/pdf"
                )
    
    with col4:
        if st.button("🔄 Refresh Data", use_container_width=True):
            force_reload_project_data(sheets_manager)

def render_project_list_tab(sheets_manager):
    """Render detailed project list with filtering and editing"""
    st.subheader("📋 Project Database")
    
    if 'project_data' not in st.session_state or st.session_state.project_data is None:
        st.warning("⚠️ No project data loaded. Data should auto-load when credentials are configured or generate sample data in Overview tab.")
        if st.button("🔄 Try Loading Data Now"):
            force_reload_project_data(sheets_manager)
        return
    
    df = st.session_state.project_data
    
    # Advanced filtering
    with st.expander("🔍 Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search projects", placeholder="Project name, description...")
        
        with col2:
            status_options = ["All"] + sorted(df['Status'].dropna().unique().tolist()) if 'Status' in df.columns else ["All"]
            selected_status = st.selectbox("Filter by Status", status_options)
        
        with col3:
            priority_options = ["All"] + sorted(df['Priority'].dropna().unique().tolist()) if 'Priority' in df.columns else ["All"]
            selected_priority = st.selectbox("Filter by Priority", priority_options)
        
        col4, col5 = st.columns(2)
        with col4:
            assigned_to_options = ["All"] + sorted(df['Assigned To'].dropna().unique().tolist()) if 'Assigned To' in df.columns else ["All"]
            selected_assigned_to = st.selectbox("Filter by Assigned To", assigned_to_options)
        
        with col5:
            sort_column = st.selectbox("Sort by", df.columns.tolist())
            sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        text_cols = df.select_dtypes(include=['object']).columns
        mask = False
        for col in text_cols:
            mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
        filtered_df = df[mask]
    
    if selected_status != "All" and 'Status' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    
    if selected_priority != "All" and 'Priority' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]
    
    if selected_assigned_to != "All" and 'Assigned To' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Assigned To'] == selected_assigned_to]
    
    # Apply sorting
    if sort_column:
        ascending = sort_order == "Ascending"
        try:
            filtered_df[sort_column] = pd.to_numeric(filtered_df[sort_column], errors='ignore')
            filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
        except:
            filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
    
    st.write(f"📊 Showing {len(filtered_df)} of {len(df)} projects")
    
    # Pagination
    page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)
    total_pages = (len(filtered_df) - 1) // page_size + 1
    
    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        display_df = filtered_df.iloc[start_idx:end_idx]
    else:
        display_df = filtered_df
    
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        num_rows="dynamic",
        key="project_editor"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            save_project_changes(sheets_manager, edited_df, display_df.index)
    with col2:
        if st.button("🗑️ Delete Selected"):
            st.warning("Delete functionality coming soon!")

def render_analytics_tab(sheets_manager):
    """Render project analytics and insights"""
    st.subheader("📈 Project Analytics")
    
    if 'project_data' not in st.session_state or st.session_state.project_data is None:
        st.warning("⚠️ No project data loaded. Data should auto-load when credentials are configured or generate sample data in Overview tab.")
        if st.button("🔄 Try Loading Data Now"):
            force_reload_project_data(sheets_manager)
        return
    
    df = st.session_state.project_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Status' in df.columns:
            status_counts = df['Status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Project Status Distribution",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No 'Status' column found for distribution analysis.")
    
    with col2:
        if 'Priority' in df.columns:
            priority_counts = df['Priority'].value_counts()
            fig = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                title="Projects by Priority",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(xaxis_title="Priority", yaxis_title="Number of Projects")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No 'Priority' column found for analysis.")
    
    st.subheader("📅 Project Timeline & Budget")
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Start Date' in df.columns and 'Due Date' in df.columns and 'Status' in df.columns:
            try:
                df_dates = df.copy()
                df_dates['Start Date'] = pd.to_datetime(df_dates['Start Date'], errors='coerce')
                df_dates['Due Date'] = pd.to_datetime(df_dates['Due Date'], errors='coerce')
                df_dates = df_dates.dropna(subset=['Start Date', 'Due Date'])
                
                if not df_dates.empty:
                    fig = px.timeline(
                        df_dates,
                        x_start="Start Date",
                        x_end="Due Date",
                        y="Project Name",
                        color="Status",
                        title="Project Timeline",
                        color_discrete_map={
                            "Completed": "green",
                            "In Progress": "blue",
                            "Not Started": "gray",
                            "On Hold": "orange",
                            "Cancelled": "red"
                        }
                    )
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No valid date data for timeline.")
            except Exception as e:
                st.error(f"Error creating timeline chart: {str(e)}")
        else:
            st.info("Missing 'Start Date' or 'Due Date' columns for timeline.")
    
    with col2:
        if 'Budget' in df.columns and 'Actual Cost' in df.columns:
            try:
                df_costs = df.copy()
                df_costs['Budget'] = pd.to_numeric(df_costs['Budget'], errors='coerce')
                df_costs['Actual Cost'] = pd.to_numeric(df_costs['Actual Cost'], errors='coerce')
                df_costs = df_costs.dropna(subset=['Budget', 'Actual Cost'])
                
                if not df_costs.empty:
                    fig = go.Figure(data=[
                        go.Bar(name='Budget', x=df_costs['Project Name'], y=df_costs['Budget'], marker_color='#2E86AB'),
                        go.Bar(name='Actual Cost', x=df_costs['Project Name'], y=df_costs['Actual Cost'], marker_color='#A23B72')
                    ])
                    fig.update_layout(barmode='group', title='Budget vs. Actual Cost', yaxis_title='Amount ($)')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No valid budget/cost data.")
            except Exception as e:
                st.error(f"Error creating budget chart: {str(e)}")
        else:
            st.info("Missing 'Budget' or 'Actual Cost' columns for analysis.")

def render_add_project_tab(sheets_manager):
    """Render add new project form"""
    st.subheader("➕ Add New Project")
    
    if 'project_data' not in st.session_state or st.session_state.project_data is None:
        st.warning("⚠️ No project data loaded. Please wait for auto-load or configure data source in Overview tab first.")
        if st.button("🔄 Try Loading Data Now"):
            force_reload_project_data(sheets_manager)
        return
    
    df = st.session_state.project_data
    
    st.markdown("Fill in the project information below:")
    
    with st.form("add_project_form"):
        form_data = {}
        
        # Define common columns and their types/options
        column_configs = {
            'Project Name': {'type': 'text', 'icon': '📋'},
            'Description': {'type': 'textarea', 'icon': '📝'},
            'Status': {'type': 'select', 'options': ['Not Started', 'In Progress', 'Completed', 'On Hold', 'Cancelled'], 'icon': '🏷️'},
            'Start Date': {'type': 'date', 'icon': '📅'},
            'Due Date': {'type': 'date', 'icon': '🗓️'},
            'Assigned To': {'type': 'text', 'icon': '👤'},
            'Priority': {'type': 'select', 'options': ['High', 'Medium', 'Low'], 'icon': '⚡'},
            'Budget': {'type': 'number', 'min_value': 0.0, 'step': 0.01, 'icon': '💰'},
            'Actual Cost': {'type': 'number', 'min_value': 0.0, 'step': 0.01, 'icon': '💸'},
            'Notes': {'type': 'textarea', 'icon': '📄'}
        }
        
        # Create input fields for each column present in the DataFrame
        cols = st.columns(2)
        for i, col in enumerate(df.columns):
            col_lower = col.lower()
            current_col = cols[i % 2]
            
            with current_col:
                config = column_configs.get(col, {'type': 'text', 'icon': '📄'})
                
                if config['type'] == 'text':
                    form_data[col] = st.text_input(f"{config['icon']} {col}")
                elif config['type'] == 'textarea':
                    form_data[col] = st.text_area(f"{config['icon']} {col}")
                elif config['type'] == 'date':
                    form_data[col] = st.date_input(f"{config['icon']} {col}", value=datetime.now().date())
                elif config['type'] == 'number':
                    form_data[col] = st.number_input(f"{config['icon']} {col}", min_value=config['min_value'], step=config['step'])
                elif config['type'] == 'select':
                    # Use existing unique values if available, otherwise use predefined options
                    unique_values = df[col].dropna().unique().tolist() if col in df.columns and not df[col].empty else []
                    options = [""] + sorted(list(set(unique_values + config['options'])))
                    form_data[col] = st.selectbox(f"{config['icon']} {col}", options)
        
        submitted = st.form_submit_button("➕ Add Project", type="primary")
        
        if submitted:
            required_fields = ['Project Name', 'Status', 'Start Date', 'Due Date'] # Example required fields
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                st.error(f"❌ Please fill in required fields: {', '.join(missing_fields)}")
            else:
                try:
                    new_row = []
                    for col in df.columns:
                        value = form_data.get(col, "")
                        if isinstance(value, datetime.date):
                            value = value.strftime("%Y-%m-%d")
                        new_row.append(value)
                    
                    sheet_url = st.session_state.get('project_sheet_url', '')
                    worksheet_name = st.session_state.get('project_worksheet_name', '')
                    
                    if sheets_manager.append_row(sheet_url, new_row, worksheet_name):
                        st.success("✅ Project added successfully!")
                        sheets_manager.clear_cache()
                        import time
                        time.sleep(1)
                        force_reload_project_data(sheets_manager)
                    else:
                        st.error("❌ Failed to add project to sheet")
                        
                except Exception as e:
                    st.error(f"❌ Error adding project: {str(e)}")

def render_data_scanner_tab():
    """Render integrated data scanner for project analysis"""
    st.subheader("🔍 Advanced Project Data Analysis")
    
    if 'project_data' not in st.session_state or st.session_state.project_data is None:
        st.warning("⚠️ No project data loaded. Please wait for auto-load or configure data source in Overview tab first.")
        return
    
    st.session_state.current_df = st.session_state.project_data
    
    scanner_ui = DataScannerUI()
    scanner_ui.render_main_interface()

def render_settings_tab(sheets_manager):
    """Render settings and configuration for projects"""
    st.subheader("⚙️ Settings & Configuration")
    
    st.subheader("🔄 Auto-Load Configuration")
    col1, col2 = st.columns(2)
    with col1:
        auto_load_enabled = st.checkbox(
            "Enable automatic data loading",
            value=st.session_state.get('project_auto_load_enabled', True),
            help="Automatically load data when the app starts"
        )
        refresh_interval = st.selectbox(
            "Auto-refresh interval",
            options=[0, 300, 600, 1800, 3600],
            format_func=lambda x: "Manual" if x == 0 else f"{x//60} minutes",
            index=1,
            help="How often to automatically refresh data (0 = manual only)"
        )
    with col2:
        if st.button("💾 Save Auto-Load Settings", type="primary"):
            st.session_state.project_auto_load_enabled = auto_load_enabled
            st.session_state.project_refresh_interval = refresh_interval # Store for future use
            st.success("✅ Auto-load settings saved!")
    
    st.subheader("📊 Sheet Configuration")
    with st.expander("🔧 Current Configuration", expanded=True):
        if 'project_sheet_url' in st.session_state and st.session_state.project_sheet_url:
            st.info(f"**Sheet URL:** {st.session_state.project_sheet_url}")
            st.info(f"**Worksheet:** {st.session_state.get('project_worksheet_name', 'Default')}")
            if 'project_last_auto_load' in st.session_state and st.session_state.project_last_auto_load:
                last_load = st.session_state.project_last_auto_load.strftime("%Y-%m-%d %H:%M:%S")
                st.info(f"**Last Loaded:** {last_load}")
        else:
            st.warning("No sheet configured")
    
    st.subheader("🗄️ Cache Management")
    cache_info = sheets_manager.get_cache_info()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Cached Sheets", cache_info['cached_sheets'])
    with col2:
        if cache_info['oldest_cache']:
            oldest = datetime.fromtimestamp(cache_info['oldest_cache'])
            st.metric("⏰ Oldest Cache", oldest.strftime("%H:%M:%S"))
        else:
            st.metric("⏰ Oldest Cache", "None")
    with col3:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            sheets_manager.clear_cache()
            st.success("Cache cleared!")
            st.rerun()
    
    st.subheader("✅ Data Validation")
    if 'project_data' in st.session_state and st.session_state.project_data is not None:
        df = st.session_state.project_data
        issues = []
        warnings = []
        
        if 'Project Name' in df.columns:
            if df['Project Name'].isnull().sum() > 0:
                issues.append(f"❌ {df['Project Name'].isnull().sum()} projects missing names.")
            if df['Project Name'].duplicated().sum() > 0:
                warnings.append(f"⚠️ {df['Project Name'].duplicated().sum()} duplicate project names.")
        
        if 'Status' in df.columns:
            if df['Status'].isnull().sum() > 0:
                issues.append(f"❌ {df['Status'].isnull().sum()} projects missing status.")
        
        if 'Start Date' in df.columns and 'Due Date' in df.columns:
            try:
                df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
                df['Due Date'] = pd.to_datetime(df['Due Date'], errors='coerce')
                
                invalid_dates = df['Start Date'].isnull().sum() + df['Due Date'].isnull().sum()
                if invalid_dates > 0:
                    issues.append(f"❌ {invalid_dates} projects with invalid start/due dates.")
                
                overdue_projects = len(df[(df['Due Date'] < datetime.now()) & (~df['Status'].str.contains('Completed|Cancelled', case=False, na=False))])
                if overdue_projects > 0:
                    warnings.append(f"⚠️ {overdue_projects} projects are currently overdue.")
            except:
                issues.append("❌ Date columns could not be parsed correctly.")
        
        if 'Budget' in df.columns and 'Actual Cost' in df.columns:
            if (pd.to_numeric(df['Budget'], errors='coerce') < 0).sum() > 0:
                issues.append("❌ Negative budget values found.")
            if (pd.to_numeric(df['Actual Cost'], errors='coerce') < 0).sum() > 0:
                issues.append("❌ Negative actual cost values found.")
            
            over_budget = len(df[(pd.to_numeric(df['Actual Cost'], errors='coerce') > pd.to_numeric(df['Budget'], errors='coerce')) & (df['Status'].str.contains('Completed', case=False, na=False))])
            if over_budget > 0:
                warnings.append(f"⚠️ {over_budget} completed projects are over budget.")
        
        if issues:
            st.error("**Critical Issues Found:**")
            for issue in issues:
                st.write(issue)
        if warnings:
            st.warning("**Warnings:**")
            for warning in warnings:
                st.write(warning)
        if not issues and not warnings:
            st.success("✅ No data issues found!")
        
        total_checks = 6 # Example count of checks
        passed_checks = total_checks - len(issues) - len(warnings)
        quality_score = (passed_checks / total_checks) * 100
        st.metric("📊 Data Quality Score", f"{quality_score:.1f}%")
    
    st.subheader("📤 Export Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Available Export Formats:**")
        st.write("• CSV (Comma Separated Values)")
        st.write("• PDF (Portable Document Format)")
        st.write("• Excel (Coming Soon)")
    with col2:
        include_charts = st.checkbox("Include charts in PDF", value=True, key="project_export_charts")
        include_summary = st.checkbox("Include summary statistics", value=True, key="project_export_summary")
        if st.button("💾 Save Export Preferences", key="project_save_export_prefs"):
            st.session_state.project_export_include_charts = include_charts
            st.session_state.project_export_include_summary = include_summary
            st.success("✅ Export preferences saved!")

def save_project_changes(sheets_manager, edited_df, original_indices):
    """Save changes back to Google Sheets"""
    try:
        full_df = st.session_state.project_data.copy()
        
        for idx in edited_df.index:
            if idx in original_indices:
                full_df.loc[idx] = edited_df.loc[idx]
        
        sheet_url = st.session_state.get('project_sheet_url', '')
        worksheet_name = st.session_state.get('project_worksheet_name', '')
        
        if sheets_manager.update_sheet_data(sheet_url, full_df, worksheet_name):
            st.session_state.project_data = full_df
            st.session_state.project_last_auto_load = datetime.now()
            st.success("✅ Changes saved to Google Sheets!")
        else:
            st.error("❌ Failed to save changes")
            
    except Exception as e:
        st.error(f"❌ Error saving changes: {str(e)}")

def create_project_pdf(df):
    """Create PDF report of project data"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph("Project Management Report", title_style))
        elements.append(Spacer(1, 20))
        
        summary_style = styles['Normal']
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", summary_style))
        elements.append(Paragraph(f"Total Projects: {len(df)}", summary_style))
        
        if st.session_state.get('project_export_include_summary', True):
            completed_projects = len(df[df['Status'].str.contains('Completed', case=False, na=False)])
            in_progress_projects = len(df[df['Status'].str.contains('In Progress', case=False, na=False)])
            elements.append(Paragraph(f"Completed Projects: {completed_projects}", summary_style))
            elements.append(Paragraph(f"In Progress Projects: {in_progress_projects}", summary_style))
        
        elements.append(Spacer(1, 20))
        
        table_data = [df.columns.tolist()]
        for _, row in df.iterrows():
            table_data.append([str(cell)[:50] for cell in row.tolist()])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return None

if __name__ == "__main__":
    main()
