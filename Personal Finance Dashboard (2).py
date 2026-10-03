import io
import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit Page Setup
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Personal Finance Dashboard")
st.write(
    "Upload your bank statement CSV file to automatically categorize expenses, track trends, and analyze spending."
)


# Categorization Logic
def assign_category(description):
    desc = str(description).lower()
    if any(
        word in desc
        for word in ["swiggy", "zomato", "restaurant", "food", "cafe", "dine"]
    ):
        return "Food & Dining"
    elif any(
        word in desc
        for word in [
            "uber",
            "ola",
            "petrol",
            "fuel",
            "cab",
            "auto",
            "metro",
            "rapido",
        ]
    ):
        return "Transport"
    elif any(
        word in desc
        for word in ["amazon", "flipkart", "shopping", "store", "myntra", "mall"]
    ):
        return "Shopping"
    elif any(
        word in desc
        for word in [
            "rent",
            "electricity",
            "bill",
            "water",
            "recharge",
            "wifi",
            "broadband",
        ]
    ):
        return "Bills & Utilities"
    elif any(
        word in desc
        for word in ["netflix", "spotify", "prime", "youtube", "hotstar"]
    ):
        return "Subscriptions"
    elif any(
        word in desc
        for word in ["salary", "stipend", "credit", "interest", "bonus"]
    ):
        return "Income"
    else:
        return "Others"


# 1. File Upload Section
uploaded_file = st.file_uploader(
    "Upload Bank Statement (CSV File)", type=["csv"]
)

if uploaded_file is not None:
    # Read CSV
    df = pd.read_csv(uploaded_file)

    # Standardize column names (case-insensitive strip)
    df.columns = df.columns.str.strip()

    # Ensure required columns exist
    if not {"Date", "Description", "Amount"}.issubset(df.columns):
        st.error(
            "CSV must contain 'Date', 'Description', and 'Amount' columns."
        )
    else:
        # Preprocessing Data
        df["Date"] = pd.to_datetime(df["Date"])
        df["Category"] = df["Description"].apply(assign_category)

        # ------------------- SIDEBAR FILTERS -------------------
        st.sidebar.header("🔍 Filter Options")

        # Category Filter
        all_categories = df["Category"].unique().tolist()
        selected_categories = st.sidebar.multiselect(
            "Select Categories",
            options=all_categories,
            default=all_categories,
        )

        # Date Filter
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        # Apply Filters
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = df[
                (df["Category"].isin(selected_categories))
                & (df["Date"].dt.date >= start_date)
                & (df["Date"].dt.date <= end_date)
            ]
        else:
            filtered_df = df[df["Category"].isin(selected_categories)]

        # ------------------- KEY METRICS -------------------
        total_spend = filtered_df[filtered_df["Category"] != "Income"][
            "Amount"
        ].sum()
        total_income = filtered_df[filtered_df["Category"] == "Income"][
            "Amount"
        ].sum()
        
        summary_df = (
            filtered_df[filtered_df["Category"] != "Income"]
            .groupby("Category")["Amount"]
            .sum()
            .reset_index()
        )

        top_category = (
            summary_df.loc[summary_df["Amount"].idxmax()]["Category"]
            if not summary_df.empty
            else "N/A"
        )

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Total Spent", f"₹{total_spend:,.2f}")
        col_b.metric("Total Income", f"₹{total_income:,.2f}")
        col_c.metric("Top Expense Category", top_category)
        col_d.metric("Total Transactions", len(filtered_df))

        st.markdown("---")

        # ------------------- CHARTS & TABLES -------------------
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📋 Categorized Transactions")
            # Format date for cleaner display
            display_df = filtered_df.copy()
            display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df, use_container_width=True)

            # CSV Download Button
            csv_buffer = io.BytesIO()
            display_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Categorized CSV",
                data=csv_buffer.getvalue(),
                file_name="categorized_finance_summary.csv",
                mime="text/csv",
            )

        with col2:
            st.subheader("📊 Expense Category Breakdown")
            if not summary_df.empty:
                fig_pie = px.pie(
                    summary_df,
                    values="Amount",
                    names="Category",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expense data available for the selected filters.")

        st.markdown("---")

        # ------------------- TIME-SERIES TREND -------------------
        st.subheader("📈 Daily Expense Trend")
        daily_trend = (
            filtered_df[filtered_df["Category"] != "Income"]
            .groupby("Date")["Amount"]
            .sum()
            .reset_index()
        )

        if not daily_trend.empty:
            fig_line = px.line(
                daily_trend,
                x="Date",
                y="Amount",
                title="Spending Over Time",
                markers=True,
                line_shape="spline",
            )
            fig_line.update_traces(line_color="#FF4B4B")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No trend data available.")

else:
    st.info(" Please upload a CSV file to get started.")
