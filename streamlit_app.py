import streamlit as st
import subprocess
import sys
import requests
import json
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
import app.models as models
from app.schemas import Product, Policy, FAQ, SocialHandle, ContactDetail, ImportantLink
import pandas as pd
import io

st.set_page_config(page_title="Shopify Insights DB Viewer", layout="wide")

API_URL = "http://127.0.0.1:8000"

def fetch_insights_api(website_url):
    try:
        resp = requests.post(f"{API_URL}/fetch-insights", json={"website_url": website_url}, timeout=60)
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, resp.json().get("detail", "Unknown error")
    except Exception as e:
        return None, str(e)

def fetch_competitors_api(website_url):
    try:
        resp = requests.post(f"{API_URL}/competitors", json={"website_url": website_url}, timeout=120)
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, resp.json().get("detail", "Unknown error")
    except Exception as e:
        return None, str(e)

def get_all_brands(db: Session):
    return db.query(models.Brand).all()

def get_brand_insights(db: Session, website_url: str):
    brand = db.query(models.Brand).filter(models.Brand.url == website_url).first()
    if not brand:
        return None
    products = db.query(models.Product).filter(models.Product.brand_id == brand.id).all()
    hero_products = db.query(models.HeroProduct).filter(models.HeroProduct.brand_id == brand.id).all()
    policies = db.query(models.Policy).filter(models.Policy.brand_id == brand.id).all()
    faqs = db.query(models.FAQ).filter(models.FAQ.brand_id == brand.id).all()
    social_handles = db.query(models.SocialHandle).filter(models.SocialHandle.brand_id == brand.id).all()
    contact_details = db.query(models.ContactDetail).filter(models.ContactDetail.brand_id == brand.id).all()
    important_links = db.query(models.ImportantLink).filter(models.ImportantLink.brand_id == brand.id).all()
    return {
        "brand": brand,
        "products": products,
        "hero_products": hero_products,
        "policies": policies,
        "faqs": faqs,
        "social_handles": social_handles,
        "contact_details": contact_details,
        "important_links": important_links,
    }

def show_insights(insights, brand_url=None, filters=None, key_prefix=""):
    if not insights or not insights["brand"]:
        st.warning("No insights found for this brand.")
        return
    if brand_url:
        st.header(f"Brand: {brand_url}")
    st.subheader("Brand Text")
    st.write(insights["brand"].brand_text or "-")
    st.subheader("Product Catalog")
    products = insights["products"]
    df_products = pd.DataFrame([{k: getattr(p, k) for k in ["title", "price", "url", "image"]} for p in products])
    # Filtering
    if filters:
        if filters.get("product_name"):
            df_products = df_products[df_products["title"].str.contains(filters["product_name"], case=False, na=False)]
        if filters.get("min_price") is not None or filters.get("max_price") is not None:
            df_products["price_num"] = pd.to_numeric(df_products["price"], errors="coerce")
            if filters.get("min_price") is not None:
                df_products = df_products[df_products["price_num"] >= filters["min_price"]]
            if filters.get("max_price") is not None:
                df_products = df_products[df_products["price_num"] <= filters["max_price"]]
    st.dataframe(df_products.drop(columns=["price_num"], errors="ignore"))
    # Export buttons for Product Catalog
    csv_products = df_products.to_csv(index=False).encode('utf-8')
    excel_products = io.BytesIO()
    df_products.to_excel(excel_products, index=False, engine='xlsxwriter')
    st.download_button("Download Products as CSV", csv_products, file_name=f"products_{brand_url or 'brand'}.csv", mime="text/csv", key=f"{key_prefix}_products_csv_{brand_url}")
    st.download_button("Download Products as Excel", excel_products.getvalue(), file_name=f"products_{brand_url or 'brand'}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key_prefix}_products_excel_{brand_url}")
    st.subheader("Hero Products")
    st.dataframe([{k: getattr(p, k) for k in ["title", "url", "image"]} for p in insights["hero_products"]])
    st.subheader("Policies")
    st.dataframe([{k: getattr(pol, k) for k in ["type", "url", "content"]} for pol in insights["policies"]])
    st.subheader("FAQs")
    faqs = insights["faqs"]
    df_faqs = pd.DataFrame([{k: getattr(f, k) for k in ["question", "answer"]} for f in faqs])
    if filters and filters.get("faq_query"):
        df_faqs = df_faqs[df_faqs["question"].str.contains(filters["faq_query"], case=False, na=False) | df_faqs["answer"].str.contains(filters["faq_query"], case=False, na=False)]
    st.dataframe(df_faqs)
    # Export buttons for FAQs
    csv_faqs = df_faqs.to_csv(index=False).encode('utf-8')
    excel_faqs = io.BytesIO()
    df_faqs.to_excel(excel_faqs, index=False, engine='xlsxwriter')
    st.download_button("Download FAQs as CSV", csv_faqs, file_name=f"faqs_{brand_url or 'brand'}.csv", mime="text/csv", key=f"{key_prefix}_faqs_csv_{brand_url}")
    st.download_button("Download FAQs as Excel", excel_faqs.getvalue(), file_name=f"faqs_{brand_url or 'brand'}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key_prefix}_faqs_excel_{brand_url}")
    st.subheader("Social Handles")
    st.dataframe([{k: getattr(s, k) for k in ["platform", "url"]} for s in insights["social_handles"]])
    st.subheader("Contact Details")
    st.dataframe([{k: getattr(c, k) for k in ["type", "value"]} for c in insights["contact_details"]])
    st.subheader("Important Links")
    st.dataframe([{k: getattr(l, k) for k in ["name", "url"]} for l in insights["important_links"]])
    # Analytics
    st.markdown("---")
    st.subheader("Summary & Analytics")
    st.write(f"Total Products: {len(products)}")
    st.write(f"Total FAQs: {len(faqs)}")
    st.write(f"Total Policies: {len(insights['policies'])}")
    st.write(f"Total Social Handles: {len(insights['social_handles'])}")
    st.write(f"Total Contact Details: {len(insights['contact_details'])}")
    st.write(f"Total Important Links: {len(insights['important_links'])}")
    st.bar_chart(pd.DataFrame({"count": [len(products), len(faqs), len(insights['policies'])]}, index=["Products", "FAQs", "Policies"]))
    safe_brand_url = (brand_url or 'brand').replace('https://', '').replace('/', '_') if brand_url else f'brand_{id(insights)}'
    st.download_button(
        label="Download Insights as JSON",
        data=json.dumps({
            k: [vars(x) for x in v] if isinstance(v, list) else (vars(v) if v else None)
            for k, v in insights.items()
        }, default=str),
        file_name=f"insights_{safe_brand_url}.json",
        mime="application/json",
        key=f"{key_prefix}_insights_json_{safe_brand_url}"
    )

def main():
    st.title("Shopify Insights Demo UI")
    db = SessionLocal()
    tabs = st.tabs(["Search & Save Insights", "Browse Saved Brands", "Compare Competitors"])
    # --- Tab 1: Search & Save ---
    with tabs[0]:
        st.header("Search Shopify Store Insights")
        url_input = st.text_input("Enter Shopify Store URL", "https://memy.co.in")
        colA, colB = st.columns(2)
        fetch_clicked = colA.button("Fetch & Save Insights")
        comp_clicked = colB.button("Fetch Competitors & Save Insights")
        if fetch_clicked:
            with st.spinner("Fetching insights and saving to DB..."):
                data, err = fetch_insights_api(url_input)
                if err:
                    st.error(f"Error: {err}")
                else:
                    st.success(f"Fetched and saved insights for {url_input}")
                    db.expire_all()  # Refresh session
                    show_insights(get_brand_insights(db, url_input), url_input, key_prefix="tab1")
        if comp_clicked:
            with st.spinner("Fetching competitors and their insights..."):
                data, err = fetch_competitors_api(url_input)
                if err:
                    st.error(f"Error: {err}")
                else:
                    st.success(f"Fetched and saved insights for competitors of {url_input}")
                    db.expire_all()  # Refresh session
                    show_insights(get_brand_insights(db, url_input), url_input, key_prefix="tab1")
    # --- Tab 2: Browse Saved Brands ---
    with tabs[1]:
        st.header("Browse Brands in Database")
        brands = get_all_brands(db)
        if not brands:
            st.info("No brands in database. Use the 'Search & Save Insights' tab to add one.")
        else:
            brand_urls = [b.url for b in brands]
            selected_url = st.selectbox("Select Brand URL", brand_urls)
            st.markdown("**Product Filters**")
            product_name = st.text_input("Product Name Contains", "")
            min_price = st.number_input("Min Price", value=0.0, step=1.0)
            max_price = st.number_input("Max Price", value=0.0, step=1.0)
            if max_price == 0.0:
                max_price = None
            st.markdown("**FAQ Filters**")
            faq_query = st.text_input("FAQ Contains", "")
            filters = {
                "product_name": product_name if product_name else None,
                "min_price": min_price if min_price > 0 else None,
                "max_price": max_price,
                "faq_query": faq_query if faq_query else None,
            }
            if selected_url:
                show_insights(get_brand_insights(db, selected_url), selected_url, filters, key_prefix="tab2")
    # --- Tab 3: Compare Competitors ---
    with tabs[2]:
        st.header("Compare Brand with Competitors")
        brands = get_all_brands(db)
        if not brands:
            st.info("No brands in database. Use the 'Search & Save Insights' tab to add one.")
        else:
            brand_urls = [b.url for b in brands]
            selected_url = st.selectbox("Select Brand to Compare", brand_urls, key="compare_brand")
            if selected_url:
                comp_data, comp_err = fetch_competitors_api(selected_url)
                if comp_err or not comp_data or not comp_data.get("competitors"):
                    st.warning("No competitors found or error fetching competitors.")
                else:
                    comp_urls = [c["website_url"] for c in comp_data["competitors"]]
                    selected_comps = st.multiselect("Select Competitors", comp_urls, default=comp_urls[:1])
                    all_urls = [selected_url] + selected_comps
                    cols = st.columns(len(all_urls))
                    for i, url in enumerate(all_urls):
                        with cols[i]:
                            if url == selected_url:
                                st.markdown(f"**Brand**\n{url}")
                                insights = get_brand_insights(db, url)
                            else:
                                st.markdown(f"**Competitor**\n{url}")
                                insights = get_brand_insights(db, url)
                                if not insights:
                                    api_data, _ = fetch_insights_api(url)
                                    if api_data:
                                        db.expire_all()
                                        insights = get_brand_insights(db, url)
                            if insights:
                                st.write(f"Products: {len(insights['products'])}")
                                st.write(f"FAQs: {len(insights['faqs'])}")
                                st.write(f"Policies: {len(insights['policies'])}")
                                st.write(f"Socials: {len(insights['social_handles'])}")
                                st.write(f"Contact Details: {len(insights['contact_details'])}")
                                st.write(f"Important Links: {len(insights['important_links'])}")
                                st.write(f"Brand Text: {insights['brand'].brand_text[:100] if insights['brand'].brand_text else '-'}...")
                            else:
                                st.warning("No data available.")
    db.close()

if __name__ == "__main__":
    main() 