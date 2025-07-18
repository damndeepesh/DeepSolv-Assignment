from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Brand(Base):
    __tablename__ = 'brands'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), unique=True, index=True, nullable=False)
    brand_text = Column(Text)

    products = relationship('Product', back_populates='brand', cascade="all, delete-orphan")
    hero_products = relationship('HeroProduct', back_populates='brand', cascade="all, delete-orphan")
    policies = relationship('Policy', back_populates='brand', cascade="all, delete-orphan")
    faqs = relationship('FAQ', back_populates='brand', cascade="all, delete-orphan")
    social_handles = relationship('SocialHandle', back_populates='brand', cascade="all, delete-orphan")
    contact_details = relationship('ContactDetail', back_populates='brand', cascade="all, delete-orphan")
    important_links = relationship('ImportantLink', back_populates='brand', cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    shopify_id = Column(String(64))
    title = Column(String(255))
    url = Column(String(255))
    image = Column(String(255))
    price = Column(String(64))
    description = Column(Text)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='products')

class HeroProduct(Base):
    __tablename__ = 'hero_products'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    url = Column(String(255))
    image = Column(String(255))
    price = Column(String(64))
    description = Column(Text)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='hero_products')

class Policy(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(64))
    url = Column(String(255))
    content = Column(Text)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='policies')

class FAQ(Base):
    __tablename__ = 'faqs'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='faqs')

class SocialHandle(Base):
    __tablename__ = 'social_handles'
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(64))
    url = Column(String(255))
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='social_handles')

class ContactDetail(Base):
    __tablename__ = 'contact_details'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(64))
    value = Column(String(255))
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='contact_details')

class ImportantLink(Base):
    __tablename__ = 'important_links'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    url = Column(String(255))
    brand_id = Column(Integer, ForeignKey('brands.id'))
    brand = relationship('Brand', back_populates='important_links') 