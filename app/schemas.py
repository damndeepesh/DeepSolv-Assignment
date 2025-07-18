from pydantic import BaseModel  # type: ignore
from typing import List, Optional, Dict

class Product(BaseModel):
    id: Optional[str]
    title: str
    url: Optional[str]
    image: Optional[str]
    price: Optional[str]
    description: Optional[str]

class Policy(BaseModel):
    type: str  # e.g., privacy, refund
    url: Optional[str]
    content: Optional[str]

class FAQ(BaseModel):
    question: str
    answer: str

class SocialHandle(BaseModel):
    platform: str  # e.g., Instagram, Facebook
    url: str

class ContactDetail(BaseModel):
    type: str  # e.g., email, phone
    value: str

class ImportantLink(BaseModel):
    name: str
    url: str

class BrandInsights(BaseModel):
    product_catalog: List[Product]
    hero_products: List[Product]
    policies: List[Policy]
    faqs: List[FAQ]
    social_handles: List[SocialHandle]
    contact_details: List[ContactDetail]
    brand_text: Optional[str]
    important_links: List[ImportantLink] 