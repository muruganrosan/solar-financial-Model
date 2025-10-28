# python -m streamlit run solar_financials.py
import streamlit as st
import numpy_financial as npf
import pandas as pd
# https://github.com/muruganrosan/solar-financial-Model/blob/main/solar_financial_model.py
# --- Page Config ---
st.set_page_config(page_title="Solar Power Plant Financial Model Dashboard", layout="centered")
st.title("🌞 Solar Power Plant Financial Dashboard")

# ---------------- SIDEBAR INPUTS ----------------
st.sidebar.header("Technical Parameters")
plant_capacity_mw = st.sidebar.number_input("Plant Capacity (AC MW)", value=1.0, step=0.1)
override_dc = st.sidebar.checkbox("Override DC Overloading", value=False)
dc_overload_factor = st.sidebar.number_input("DC Overloading Factor", value=1.2, step=0.05) if override_dc else 1.2
panel_type = st.sidebar.selectbox("Solar Panel Type", ["Bifacial", "Monocrystalline", "Polycrystalline"], index=0)
solar_irradiation = st.sidebar.number_input("Solar Irradiation (kWh/m²/year)", value=1800.0, step=10.0)
performance_ratio = 0.85
efficiency_map = {"Bifacial": 0.23, "Monocrystalline": 0.21, "Polycrystalline": 0.18}
panel_efficiency = efficiency_map[panel_type]
estimated_cuf = (solar_irradiation * performance_ratio) / 8760
st.sidebar.markdown(f"*Estimated CUF:* {estimated_cuf*100:.2f}%")
use_manual_cuf = st.sidebar.checkbox("Override CUF manually", value=False)
cuf = st.sidebar.number_input("CUF (%)", value=estimated_cuf*100, step=0.1)/100 if use_manual_cuf else estimated_cuf

st.sidebar.header("Project Life & Degradation")
project_life = st.sidebar.slider("Project Life (years)", 10, 35, 25)
degradation = st.sidebar.number_input("Annual Degradation (%)", value=0.5, step=0.1)/100

st.sidebar.header("Financial Inputs")
capital_cost_map = {"Bifacial": 55000000, "Monocrystalline": 51000000, "Polycrystalline": 47000000}
capital_cost_per_mw = st.sidebar.number_input("Capital Cost per MW (₹)", value=capital_cost_map[panel_type], step=100000)
tariff = st.sidebar.number_input("Tariff (₹/kWh)", value=3.50, step=0.1)
om_cost_per_mw = st.sidebar.number_input("O&M Cost per MW (Year 1) (₹)", value=300000, step=10000)
om_escalation = st.sidebar.number_input("O&M Escalation Rate (%)", value=5.0, step=0.5)/100

# ---------------- Viability Gap Funding (VGF) ----------------
st.sidebar.header("Viability Gap Funding (Subsidy)")
override_vgf = st.sidebar.checkbox("Override VGF", value=True)
if override_vgf:
    subsidy_amount_per_mw = st.sidebar.number_input(
        "Subsidy Amount per MW (₹)", value=0.0, step=100000.0
    )
else:
    subsidy_amount_per_mw = 0.0

# ---------------- Loan & Tax Inputs ----------------
st.sidebar.header("Loan & Tax Inputs")
loan_percent = st.sidebar.slider("Loan Portion (%)", 0, 100, 70)
loan_interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=10.0, step=0.5)/100
loan_tenure = st.sidebar.number_input("Loan Tenure (Years)", value=10, step=1)
depreciation_rate = st.sidebar.number_input("Depreciation Rate (%)", value=5.28, step=0.1)/100
tax_rate = st.sidebar.number_input("Income Tax Rate (%)", value=25.0, step=1.0)/100

st.sidebar.header("Return Inputs")
return_on_equity = st.sidebar.number_input("Expected Return on Equity (%)", value=14.0, step=0.5)/100

# ---------------- CALCULATIONS ----------------
# Base capital cost
base_capital_cost = capital_cost_per_mw * plant_capacity_mw
capital_cost = base_capital_cost * dc_overload_factor

# Total VGF/subsidy
subsidy_amount = subsidy_amount_per_mw * plant_capacity_mw

# Effective capital cost after VGF
effective_capital_cost = capital_cost - subsidy_amount

# Financing structure
loan_amount = effective_capital_cost * (loan_percent / 100)
equity_amount = effective_capital_cost - loan_amount
cost_of_debt = loan_interest_rate
cost_of_equity = return_on_equity
wacc = (loan_amount / effective_capital_cost) * cost_of_debt * (1 - tax_rate) + \
       (equity_amount / effective_capital_cost) * cost_of_equity

# Energy generation
energy_y1_kwh = plant_capacity_mw * 1000 * 8760 * cuf * dc_overload_factor
om_cost_year1 = om_cost_per_mw * plant_capacity_mw

# Cash flow initialization
project_cf_list = [-effective_capital_cost]
equity_cf_list = [-equity_amount]
total_cf_list = [-effective_capital_cost]
energy_outputs, om_costs, profits, ebitdas = [], [], [], []

for year in range(1, project_life + 1):
    energy = energy_y1_kwh * ((1 - degradation)**(year-1))
    om_cost = om_cost_year1 * ((1 + om_escalation)**(year-1))
    revenue = energy * tariff
    depreciation = effective_capital_cost * depreciation_rate
    ebitda = revenue - om_cost
    profit = revenue - om_cost - depreciation
    project_cf = ebitda - tax_rate * max(profit, 0)
    interest_payment = loan_amount * loan_interest_rate if year <= loan_tenure else 0
    equity_cf = project_cf - interest_payment
    total_cf = project_cf + equity_cf

    project_cf_list.append(project_cf)
    equity_cf_list.append(equity_cf)
    total_cf_list.append(total_cf)

    energy_outputs.append(energy)
    om_costs.append(om_cost)
    profits.append(profit)
    ebitdas.append(ebitda)

# Discounted cash flows
discounted_project_cf = [cf / ((1 + wacc) ** i) for i, cf in enumerate(project_cf_list)]
discounted_equity_cf = [cf / ((1 + wacc) ** i) for i, cf in enumerate(equity_cf_list)]
discounted_total_cf = [p+e for p,e in zip(discounted_project_cf, discounted_equity_cf)]
cum_discounted_project_cf = pd.Series(discounted_project_cf).cumsum()
cum_discounted_equity_cf = pd.Series(discounted_equity_cf).cumsum()
cum_discounted_total_cf = pd.Series(discounted_total_cf).cumsum()

# Metrics
npv_project = sum(discounted_project_cf)
irr_project = npf.irr(project_cf_list)
total_energy = sum(energy_outputs)
lcoe = sum(project_cf_list[1:]) / total_energy if total_energy > 0 else None
cum_cf = pd.Series(total_cf_list).cumsum()
payback_years = next((i for i, x in enumerate(cum_cf) if x >= 0), None)
feasible = "Yes" if npv_project > 0 else "No"

# --- Project Summary Table ---
st.subheader("📋 Project Summary")

summary_data = {
    "Plant Capacity (AC)": f"{plant_capacity_mw:.2f} MW",
    "DC Overloading Factor": f"{dc_overload_factor:.2f}",
    "CUF": f"{cuf*100:.2f} %",
    "Tariff": f"₹{tariff:.2f} / kWh",
    "Project Life": f"{project_life} years",
    "Annual Degradation": f"{degradation*100:.2f} %",
    "Capital Cost (Base)": f"₹{base_capital_cost:,.0f}",
    "Effective Capital Cost": f"₹{effective_capital_cost:,.0f}",
    "VGF / Subsidy (Total)": f"₹{subsidy_amount:,.0f}",
    "VGF per MW": f"₹{subsidy_amount_per_mw:,.0f} / MW",
    "Loan Portion": f"{loan_percent} %",
    "WACC": f"{wacc*100:.2f} %",
    "Feasibility": feasible,
    "NPV (Project)": f"₹{npv_project:,.0f}",
    "IRR (Project)": f"{irr_project*100:.2f} %",
    "LCOE": f"₹{lcoe:.2f} / kWh",
    "Payback Period": f"{payback_years} years"
}

# Display as two columns
keys = list(summary_data.keys())
values = list(summary_data.values())
mid_index = len(keys)//2
col1, col2 = st.columns(2)

with col1:
    for i in range(mid_index):
        st.markdown(f"**{keys[i]}:** {values[i]}")

with col2:
    for i in range(mid_index, len(keys)):
        st.markdown(f"**{keys[i]}:** {values[i]}")

# --- Detailed Cash Flow Table ---
st.subheader("💰 Project Cash Flow Table")
df = pd.DataFrame({
    "Year": list(range(project_life+1)),
    "Energy Output (kWh)": [0]+[round(e) for e in energy_outputs],
    "O&M Cost (₹)": [0]+[round(c) for c in om_costs],
    "EBITDA (₹)": [0]+[round(e) for e in ebitdas],
    "Profit (₹)": [0]+[round(p) for p in profits],
    "Project CF (₹)": project_cf_list,
    "Equity CF (₹)": equity_cf_list,
    "Total CF (₹)": total_cf_list,
    "Discounted Project CF (₹)": discounted_project_cf,
    "Discounted Equity CF (₹)": discounted_equity_cf,
    "Discounted Total CF (₹)": discounted_total_cf,
    "Cumulative Discounted Project CF (₹)": cum_discounted_project_cf,
    "Cumulative Discounted Equity CF (₹)": cum_discounted_equity_cf,
    "Cumulative Discounted Total CF (₹)": cum_discounted_total_cf
})
st.dataframe(df.style.format("{:,.0f}"))

# --- Download CSV ---
st.subheader("📥 Download Cash Flow CSV")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "solar_project_cashflow.csv", "text/csv")
