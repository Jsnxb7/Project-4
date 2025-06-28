import streamlit as st
import pandas as pd
import json

def run_dashboard():
    # Load aggregated credit transaction views
    with open('aggregated_credit_transactions.json', 'r') as f:
        data = json.load(f)

    df_account = pd.DataFrame(data['account_wise'])
    df_month = pd.DataFrame(data['month_wise'])
    df_account_month = pd.DataFrame(data['account_month_wise'])

    # Load population-based summary
    pop_txn_df = pd.read_json('populated_district_txn_summary.json')

    # Sidebar View Options
    st.sidebar.title("Transaction View Options")

    view_option = st.sidebar.radio(
        "Select View",
        [
            "Account-wise",
            "Month-wise",
            "Account + Month-wise",
            "Population-Based Summary",
            "Loans in High-Crime Districts",
            "Profiles by Payment Category",
            "Loan Payment Status Profiles",
            "Owners with Loans by District",
            "Card Type Debt Rates",
            "Loan Repayment: Mid Age vs Adult"
        ]
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("❌ Kill Streamlit Server"):
        st.warning("Shutting down the server...")
        import os
        import sys
        import threading

        def stop():
            os._exit(0)

        threading.Thread(target=stop).start()



    st.title("📊 Aggregated Credit Transactions Dashboard")

    # View 1: Account-wise
    if view_option == "Account-wise":
        st.subheader("🔹 Account-wise Credit Summary")
        st.dataframe(df_account)
        st.bar_chart(df_account.set_index("account_id"))

    # View 2: Month-wise
    elif view_option == "Month-wise":
        st.subheader("🔹 Month-wise Credit Summary")
        st.dataframe(df_month)
        st.bar_chart(df_month.set_index("month"))

    # View 3: Account + Month-wise
    elif view_option == "Account + Month-wise":
        st.subheader("🔹 Account + Month-wise Credit Summary")

        accounts = sorted(df_account_month['account_id'].unique())
        months = sorted(df_account_month['month'].unique())
        selected_account = st.selectbox("Filter by Account ID", ["All"] + accounts)
        selected_month = st.selectbox("Filter by Month", ["All"] + months)

        filtered_df = df_account_month.copy()
        if selected_account != "All":
            filtered_df = filtered_df[filtered_df['account_id'] == selected_account]
        if selected_month != "All":
            filtered_df = filtered_df[filtered_df['month'] == selected_month]

        st.dataframe(filtered_df)
        if not filtered_df.empty:
            st.bar_chart(
                filtered_df.set_index("month")["total_credit"]
                if selected_account != "All"
                else filtered_df.set_index("account_id")["total_credit"]
            )

    # View 4: Population-Based Summary
    elif view_option == "Population-Based Summary":
        st.subheader("🏙️ Transaction Summary for Top & Bottom Populated Districts (Last 3 Months)")
        st.dataframe(pop_txn_df)

        credit_data = pop_txn_df[pop_txn_df['type'] == 'CREDIT']
        debit_data = pop_txn_df[pop_txn_df['type'] == 'DEBIT']

        st.markdown("### 🔹 Credit Amount Comparison")
        st.bar_chart(credit_data.set_index("group")["amount"])

        st.markdown("### 🔹 Debit Amount Comparison")
        st.bar_chart(debit_data.set_index("group")["amount"])

    elif view_option == "Loans in High-Crime Districts":
        st.subheader("🚨 Loans Issued in Districts with >6000 Crimes in 1995")

        try:
            crime_loans_df = pd.read_json("loans_in_high_crime_districts.json")
            st.dataframe(crime_loans_df)

            st.bar_chart(crime_loans_df.set_index("A2")["loan_count"])
        except FileNotFoundError:
            st.error("JSON file not found. Please run the analysis and generate 'loans_in_high_crime_districts.json' first.")

    elif view_option == "Profiles by Payment Category":
        st.subheader("📊 Category-wise Customer Profile Analysis")
        st.markdown("Shows customer profiles from **districts** where **maximum money** was paid for:")
        st.markdown("**Insurance, Household, Leasing, Loan**")

        try:
            with open("category_wise_customer_profiles.json", "r") as f:
                profile_data = json.load(f)
        except FileNotFoundError:
            st.error("Profile data JSON not found. Please run the analysis script first.")
            st.stop()

        category = st.selectbox("Select Category", list(profile_data.keys()))

        data = profile_data[category]

        st.subheader(f"🏙️ District: {data['district_name']} (ID: {data['district_id']})")
        st.write(f"💰 Total Amount Paid: **{data['total_amount_paid']:,.2f}**")
        st.write(f"👥 Number of Customers: **{data['num_customers']}**")

        customer_df = pd.DataFrame(data["customers"])
        st.dataframe(customer_df)

        st.markdown("### 📈 Demographic Breakdown")

        col1, col2 = st.columns(2)

        with col1:
            gender_counts = customer_df['gender'].value_counts()
            st.subheader("By Gender")
            st.bar_chart(gender_counts)

        with col2:
            age_group_counts = customer_df['age_levels'].value_counts()
            st.subheader("By Age Group")
            st.bar_chart(age_group_counts)

    elif view_option == "Loan Payment Status Profiles":
        st.subheader("🏦 Customer Profiles by Loan Payment Status")
        st.markdown("""
        Profiles are categorized into 4 loan statuses:
        - **A**: Finished – No issues  
        - **B**: Finished – Loan not paid  
        - **C**: Running – OK  
        - **D**: Running – In debt
        """)

        try:
            with open("loan_status_customer_profiles.json", "r") as f:
                loan_profiles = json.load(f)
        except FileNotFoundError:
            st.error("Loan profile data not found. Please run the analysis script first.")
            st.stop()

        selected_status = st.selectbox("Select Loan Status", ["A", "B", "C", "D"], index=0)
        selected_data = loan_profiles[selected_status]

        st.success(f"**{selected_status}** → {selected_data['status_meaning']}")
        st.write(f"👥 **Total Customers**: {selected_data['num_customers']}")

        # Load customer profile data
        profile_df = pd.DataFrame(selected_data["customers"])

        if profile_df.empty:
            st.warning("No customer data available for this loan status.")
            st.stop()

        # Show full customer datas
        st.dataframe(profile_df)

        # District Socio-Economic Summary
        st.markdown("### 🏙️ District Socio-Economic Summary")

        # Ensure numeric types
        profile_df["average_salary"] = pd.to_numeric(profile_df["average_salary"], errors='coerce')
        profile_df["unemployment_95"] = pd.to_numeric(profile_df["unemployment_95"], errors='coerce')
        profile_df["unemployment_96"] = pd.to_numeric(profile_df["unemployment_96"], errors='coerce')
        profile_df["crimes_95"] = pd.to_numeric(profile_df["crimes_95"], errors='coerce')

        district_summary = profile_df.groupby("district_name").agg({
            "average_salary": "mean",
            "unemployment_95": "mean",
            "unemployment_96": "mean",
            "crimes_95": "mean",
            "client_id": "count"
        }).rename(columns={"client_id": "num_customers"}).reset_index()


        st.dataframe(district_summary)

        # Visualization: Salary, Unemployment, Crimes by District
        st.markdown("### 📈 Visual Insights")
        with st.expander("📊 Compare Socio-Economic Indicators"):
            st.bar_chart(district_summary.set_index("district_name")[["average_salary", "unemployment_95", "crimes_95"]])

        # Demographics Section
        st.markdown("### 📊 Demographics Distribution")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("By Gender")
            gender_dist = profile_df["gender"].value_counts()
            st.bar_chart(gender_dist)

        with col2:
            st.subheader("By Age Group")
            age_group_dist = profile_df["age_levels"].value_counts()
            st.bar_chart(age_group_dist)

        # District Count Summary
        st.markdown("### 📍 Customer Count by District")
        district_counts = profile_df["district_name"].value_counts().sort_values(ascending=False)
        st.bar_chart(district_counts)

    elif view_option == "Owners with Loans by District":
        st.subheader("🏦 Owners Issuing Permanent Orders and Taking Loans by District")

        try:
            with open("owners_loan_by_district.json", "r") as f:
                owners_loan_data = json.load(f)
        except FileNotFoundError:
            st.error("owners_loan_by_district.json not found. Please run the preprocessing script.")
            st.stop()

        df_owners_loans = pd.DataFrame(owners_loan_data)
        st.dataframe(df_owners_loans)

        st.bar_chart(df_owners_loans.set_index("district_name")["num_owners_with_loans"])

    elif view_option == "Card Type Debt Rates":
        st.subheader("💳 Debt Rates by Card Type")
        st.markdown("Comparison of how many cardholders (Classic, Junior, Gold) are in **loan default (status D)**.")

        try:
            with open("card_debt_rate.json", "r") as f:
                card_debt_data = json.load(f)
        except FileNotFoundError:
            st.error("Debt rate data not found. Please run the analysis script first.")
            st.stop()

        df_debt = pd.DataFrame(card_debt_data)
        st.dataframe(df_debt)

        st.markdown("### 📊 Debt Rate (%) Comparison")
        st.bar_chart(df_debt.set_index("card_type")["debt_rate (%)"])

        st.markdown("### 📈 Absolute Counts")
        st.bar_chart(df_debt.set_index("card_type")[["total_holders", "num_in_debt"]])

    elif view_option == "Loan Repayment: Mid Age vs Adult":
        st.subheader("👥 Loan Repayment Performance: Mid Age vs Adults")
        st.markdown("Loan repayment status comparison for customers categorized by **age_levels**.")

        try:
            with open("loan_repayment_by_age.json", "r") as f:
                age_repay_data = json.load(f)
        except FileNotFoundError:
            st.error("Data file not found. Please run the analysis script first.")
            st.stop()

        abs_df = pd.DataFrame(age_repay_data["absolute"]).set_index("age_levels")
        pct_df = pd.DataFrame(age_repay_data["percentages"]).set_index("age_levels")

        st.markdown("### 🔢 Absolute Loan Status Counts")
        st.dataframe(abs_df)
        st.bar_chart(abs_df)

        st.markdown("### 📊 Percentage Distribution of Loan Status")
        st.dataframe(pct_df)
        st.bar_chart(pct_df)

if __name__ == "__main__":
    run_dashboard()
