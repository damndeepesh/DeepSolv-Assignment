import logging
import re
from fastapi import FastAPI, HTTPException, Depends  # type: ignore
from pydantic import BaseModel  # type: ignore
from sqlalchemy.orm import Session
from app.schemas import BrandInsights
from app.services.shopify_scraper import ShopifyScraper
from app.services.utils import (
    map_products, map_hero_products, map_policies, map_faqs,
    map_social_handles, map_contact_details, map_important_links
)
from app.db.database import SessionLocal
import app.models as models
import asyncio
import httpx  # type: ignore
from typing import List
from urllib.parse import quote
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class InsightsRequest(BaseModel):
    website_url: str

def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'([\da-z.-]+)\.([a-z.]{2,6})'  # domain
        r'([/\w .-]*)*/?$'  # path
    )
    return re.match(regex, url) is not None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Shopify Store Insights-Fetcher is running."}

@app.post("/fetch-insights", response_model=BrandInsights)
async def fetch_insights(request: InsightsRequest, db: Session = Depends(get_db)):
    # Input validation
    if not is_valid_url(request.website_url):
        logger.warning(f"Invalid URL received: {request.website_url}")
        raise HTTPException(status_code=400, detail="Invalid website_url format.")
    if not ("shopify" in request.website_url or request.website_url.endswith(".myshopify.com") or request.website_url.endswith(".com") or request.website_url.endswith(".in")):
        logger.warning(f"URL does not appear to be a Shopify store: {request.website_url}")
        raise HTTPException(status_code=400, detail="Provided URL does not appear to be a Shopify store.")
    scraper = ShopifyScraper(request.website_url)
    try:
        (
            products_raw, hero_raw, policies_raw, faqs_raw,
            social_raw, contact_raw, brand_text, important_links_raw
        ) = await asyncio.gather(
            scraper.fetch_product_catalog(),
            scraper.fetch_hero_products(),
            scraper.fetch_policies(),
            scraper.fetch_faqs(),
            scraper.fetch_social_handles(),
            scraper.fetch_contact_details(),
            scraper.fetch_brand_text(),
            scraper.fetch_important_links()
        )
        if not products_raw:
            logger.error(f"No products found or website not accessible: {request.website_url}")
            raise HTTPException(status_code=401, detail="Website not found or no products available.")
        # Ensure all *_raw variables are lists for mapping functions
        if not isinstance(products_raw, list):
            products_raw = []
        if not isinstance(hero_raw, list):
            hero_raw = []
        if not isinstance(policies_raw, list):
            policies_raw = []
        if not isinstance(faqs_raw, list):
            faqs_raw = []
        if not isinstance(social_raw, list):
            social_raw = []
        if not isinstance(contact_raw, list):
            contact_raw = []
        if not isinstance(important_links_raw, list):
            important_links_raw = []
        # Persist to DB
        brand = db.query(models.Brand).filter(models.Brand.url == request.website_url).first()
        if not brand:
            brand = models.Brand(url=request.website_url, brand_text=brand_text)
            db.add(brand)
            db.commit()
            db.refresh(brand)
        else:
            brand.brand_text = brand_text
            # Delete old related data
            db.query(models.Product).filter(models.Product.brand_id == brand.id).delete()
            db.query(models.HeroProduct).filter(models.HeroProduct.brand_id == brand.id).delete()
            db.query(models.Policy).filter(models.Policy.brand_id == brand.id).delete()
            db.query(models.FAQ).filter(models.FAQ.brand_id == brand.id).delete()
            db.query(models.SocialHandle).filter(models.SocialHandle.brand_id == brand.id).delete()
            db.query(models.ContactDetail).filter(models.ContactDetail.brand_id == brand.id).delete()
            db.query(models.ImportantLink).filter(models.ImportantLink.brand_id == brand.id).delete()
            db.commit()
        # Add new related data
        for p in map_products(products_raw, request.website_url):
            db.add(models.Product(
                shopify_id=p.id,
                title=p.title,
                url=p.url,
                image=p.image,
                price=p.price,
                description=p.description,
                brand_id=brand.id
            ))
        for hp in map_hero_products(hero_raw):
            db.add(models.HeroProduct(
                title=hp.title,
                url=hp.url,
                image=hp.image,
                price=hp.price,
                description=hp.description,
                brand_id=brand.id
            ))
        for pol in map_policies(policies_raw):
            db.add(models.Policy(
                type=pol.type,
                url=pol.url,
                content=pol.content,
                brand_id=brand.id
            ))
        for faq in map_faqs(faqs_raw):
            db.add(models.FAQ(
                question=faq.question,
                answer=faq.answer,
                brand_id=brand.id
            ))
        for s in map_social_handles(social_raw):
            db.add(models.SocialHandle(
                platform=s.platform,
                url=s.url,
                brand_id=brand.id
            ))
        for c in map_contact_details(contact_raw):
            db.add(models.ContactDetail(
                type=c.type,
                value=c.value,
                brand_id=brand.id
            ))
        for l in map_important_links(important_links_raw):
            db.add(models.ImportantLink(
                name=l.name,
                url=l.url,
                brand_id=brand.id
            ))
        db.commit()
        return BrandInsights(
            product_catalog=map_products(products_raw, request.website_url),
            hero_products=map_hero_products(hero_raw),
            policies=map_policies(policies_raw),
            faqs=map_faqs(faqs_raw),
            social_handles=map_social_handles(social_raw),
            contact_details=map_contact_details(contact_raw),
            brand_text=brand_text,
            important_links=map_important_links(important_links_raw)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Internal error for {request.website_url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/competitors")
async def get_competitors(request: InsightsRequest, db: Session = Depends(get_db)):
    """
    Given a website_url, find competitor Shopify stores, fetch/store their insights, and return them.
    """
    from urllib.parse import urlparse
    query = f"sites like {request.website_url} OR {request.website_url} competitors shopify"
    search_url = f"https://duckduckgo.com/html/?q={quote(query)}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(search_url)
            html = resp.text
        import re
        urls = re.findall(r'href="(https?://[^"]+)"', html)
        # Remove duplicates and the original URL
        possible_urls = []
        seen = set()
        for u in urls:
            base = u.split("?")[0].rstrip("/")
            if base != request.website_url and base not in seen:
                possible_urls.append(base)
                seen.add(base)
        # Confirm Shopify stores by checking /products.json
        shopify_urls = []
        for u in possible_urls[:40]:  # Check up to 40 URLs for better coverage
            try:
                check_url = u if u.startswith("http") else f"https://{u}"
                logger.info(f"Checking {check_url}/products.json for Shopify competitor...")
                products_url = check_url.rstrip("/") + "/products.json"
                check_resp = await httpx.AsyncClient().get(products_url, timeout=5)
                if check_resp.status_code == 200 and 'products' in check_resp.text:
                    logger.info(f"Found Shopify competitor: {check_url}")
                    shopify_urls.append(check_url)
            except Exception as e:
                logger.warning(f"Error checking {check_url}: {e}")
                continue
            if len(shopify_urls) >= 5:
                break
        competitor_insights = []
        for url in shopify_urls:
            competitor_request = InsightsRequest(website_url=url)
            try:
                insights = await fetch_insights(competitor_request, db)
                competitor_insights.append({"website_url": url, "insights": insights.dict()})
            except Exception as e:
                logger.warning(f"Failed to fetch insights for competitor {url}: {e}")
        return {"competitors": competitor_insights}
    except Exception as e:
        logger.exception(f"Competitor analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Competitor analysis failed.")

@app.get("/insights", response_model=BrandInsights)
def get_insights(
    website_url: str,
    limit: int = 20,
    offset: int = 0,
    product_title: str = None,
    faq_limit: int = 20,
    faq_offset: int = 0,
    faq_query: str = None,
    db: Session = Depends(get_db)
):
    brand = db.query(models.Brand).filter(models.Brand.url == website_url).first()
    if not brand:
        raise HTTPException(status_code=404, detail="No insights found for this website_url.")
    # Products pagination/filtering
    products_query = db.query(models.Product).filter(models.Product.brand_id == brand.id)
    if product_title:
        products_query = products_query.filter(models.Product.title.ilike(f"%{product_title}%"))
    products = products_query.offset(offset).limit(limit).all()
    # FAQs pagination/filtering
    faqs_query = db.query(models.FAQ).filter(models.FAQ.brand_id == brand.id)
    if faq_query:
        faq_query_str = f"%{faq_query}%"
        faqs_query = faqs_query.filter(
            (models.FAQ.question.ilike(faq_query_str)) | (models.FAQ.answer.ilike(faq_query_str))
        )
    faqs = faqs_query.offset(faq_offset).limit(faq_limit).all()
    hero_products = db.query(models.HeroProduct).filter(models.HeroProduct.brand_id == brand.id).all()
    policies = db.query(models.Policy).filter(models.Policy.brand_id == brand.id).all()
    social_handles = db.query(models.SocialHandle).filter(models.SocialHandle.brand_id == brand.id).all()
    contact_details = db.query(models.ContactDetail).filter(models.ContactDetail.brand_id == brand.id).all()
    important_links = db.query(models.ImportantLink).filter(models.ImportantLink.brand_id == brand.id).all()
    from app.schemas import Product, Policy, FAQ, SocialHandle, ContactDetail, ImportantLink
    return BrandInsights(
        product_catalog=[Product(
            id=p.shopify_id,
            title=p.title,
            url=p.url,
            image=p.image,
            price=p.price,
            description=p.description
        ) for p in products],
        hero_products=[Product(
            id=None,
            title=hp.title,
            url=hp.url,
            image=hp.image,
            price=hp.price,
            description=hp.description
        ) for hp in hero_products],
        policies=[Policy(
            type=pol.type,
            url=pol.url,
            content=pol.content
        ) for pol in policies],
        faqs=[FAQ(
            question=f.question,
            answer=f.answer
        ) for f in faqs],
        social_handles=[SocialHandle(
            platform=s.platform,
            url=s.url
        ) for s in social_handles],
        contact_details=[ContactDetail(
            type=c.type,
            value=c.value
        ) for c in contact_details],
        brand_text=brand.brand_text,
        important_links=[ImportantLink(
            name=l.name,
            url=l.url
        ) for l in important_links]
    ) 