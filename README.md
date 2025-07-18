# Shopify Store Insights-Fetcher

A robust, scalable, and maintainable backend system to fetch, structure, and analyze insights from any Shopify store—**without using the official Shopify API**. Features a modern FastAPI backend, SQLAlchemy ORM, and a beautiful Streamlit UI for demo and analytics.

---

## 🚀 Features Checklist

### **Mandatory Requirements**
- [x] **Python** implementation
- [x] **FastAPI** backend (RESTful, async, robust)
- [x] **SQLAlchemy ORM** for persistence (SQLite for demo, MySQL-ready)
- [x] **Demoable API** (Postman/curl/Streamlit UI)
- [x] **OOP, SOLID, clean code, deduplication**
- [x] **Pydantic models** for validation/serialization
- [x] **Edge-case and error handling** (401, 500, 400, etc.)
- [x] **Fetches and structures all required insights:**
  - [x] Product Catalog
  - [x] Hero Products
  - [x] Privacy Policy
  - [x] Return/Refund Policies
  - [x] FAQs (all flows)
  - [x] Social Handles
  - [x] Contact Details
  - [x] Brand Text
  - [x] Important Links
- [x] **No Shopify API used** (scrapes public endpoints only)
- [x] **Returns JSON Brand Context**

### **Bonus Features**
- [x] **Competitor Analysis** (web search, fetch/store competitor insights)
- [x] **SQL DB Persistence** (all data stored via SQLAlchemy)
- [x] **Streamlit UI** (modern, interactive, analytics-ready)
- [x] **Advanced filtering, analytics, and export (CSV/Excel/JSON)**
- [x] **Competitor comparison and side-by-side analytics**

---

## 🏗️ Project Structure

```
DeepSolvAssignement/
├── app/
│   ├── main.py              # FastAPI entrypoint & API logic
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── services/
│   │   ├── shopify_scraper.py  # Core scraping logic
│   │   └── utils.py            # Mapping & helpers
│   ├── db/
│   │   └── database.py      # SQLAlchemy DB setup
│   └── api/
│       └── endpoints.py     # (Optional modular API)
├── streamlit_app.py         # Streamlit UI for demo/analytics
├── requirements.txt         # All dependencies
└── README.md
```

---

## ⚡️ Quickstart

### 1. **Install dependencies**
```bash
pip install -r requirements.txt --break-system-packages
```

### 2. **Create the database**
```bash
python3 -c 'from app.db.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)'
```

### 3. **Start the FastAPI server**
```bash
uvicorn app.main:app --reload
```

### 4. **Run the Streamlit UI**
```bash
streamlit run streamlit_app.py
```

- Use the UI to fetch, save, browse, filter, analyze, and export insights.
- The FastAPI server must be running in a separate terminal.

---

## 🛠️ API Endpoints

### **POST /fetch-insights**
Fetch and save insights for a Shopify store.
```json
{
  "website_url": "https://memy.co.in"
}
```
Returns: JSON Brand Context (products, policies, faqs, etc.)

### **GET /insights**
Retrieve saved insights for a brand.
```
/insights?website_url=https://memy.co.in&limit=10&offset=0&product_title=shirt&faq_limit=5&faq_query=return
```
Supports pagination and filtering for products and FAQs.

### **POST /competitors**
Find competitors for a brand, fetch and save their insights.
```json
{
  "website_url": "https://memy.co.in"
}
```
Returns: List of competitor brands and their insights.

---

## 🎨 Streamlit UI Features
- Fetch and save insights/competitors for any Shopify URL
- Browse, filter, and analyze all saved brands
- Advanced analytics, filtering, and visualizations
- Competitor comparison (side-by-side)
- Export to CSV/Excel/JSON for products and FAQs
- Robust error handling and user feedback

---

## 📝 Notes
- **No Shopify API used**: All data is scraped from public endpoints.
- **MySQL-ready**: To use MySQL, update the connection string in `app/db/database.py`.
- **Extensible**: Add more analytics, export, or competitor logic as needed.

---

## 🛠️ Troubleshooting

- **DB errors (e.g., no such table):**  
  Run the DB creation command above after any model changes or if the DB file is missing.
- **Competitor search returns no results:**  
  This depends on search engine results and public `/products.json` endpoints. Try with a different brand or increase the number of URLs checked.
- **Export to Excel fails:**  
  Ensure `XlsxWriter` is installed (included in requirements.txt).
- **FastAPI server not running:**  
  Start it manually with `uvicorn app.main:app --reload`.

---

## 👏 Credits
- Developed by Deepesh Gupta
- Assignment for DeepSolv
