# solar-financial-Model
# 🌞 Solar Power Plant Financial Calculator

An interactive web-based dashboard built with **Streamlit** that enables users to evaluate the **technical and financial feasibility** of solar power plants.  
It allows engineers, consultants, and investors to estimate key financial metrics like IRR, NPV, LCOE, and payback period, along with land and system requirements — all in an easy-to-use interface.

---

## 🚀 Features

- 📈 **Financial Analysis**
  - Calculates **Project IRR**, **Equity IRR**, **NPV**, **LCOE**, and **Payback Period**
  - Models loan repayments, depreciation, tax impact, and O&M escalation
- 🏗️ **Technical Inputs**
  - Choose solar panel type, plant capacity, and irradiation levels
  - Automatic or manual **CUF** (Capacity Utilization Factor)
- 🌍 **Location-Specific Land Requirement**
  - Predefined land area per MW for each Indian state, with manual override
- 🧾 **Cash Flow Table & Download**
  - Year-by-year breakdown of revenue, O&M cost, profits, and discounted cash flows
  - Export results as CSV file
- 🧮 **Dynamic Parameter Control**
  - Fully interactive sidebar for all input assumptions

---

## 🧩 Tech Stack

| Component | Technology |
|------------|-------------|
| Frontend/UI | Streamlit |
| Backend/Computation | Python |
| Financial Calculations | NumPy Financial |
| Data Handling | Pandas |
