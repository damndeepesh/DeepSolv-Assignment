from app.schemas import Product, Policy, FAQ, SocialHandle, ContactDetail, ImportantLink
from typing import List, Dict, Any

def map_products(products_raw: List[Dict[str, Any]], base_url: str) -> List[Product]:
    def get_image_src(p):
        # Try main image
        if p.get('image') and p['image'].get('src'):
            return p['image']['src']
        # Try images list
        if p.get('images') and isinstance(p['images'], list) and len(p['images']) > 0:
            for img in p['images']:
                if img.get('src'):
                    return img['src']
        # Try variant image_id
        if p.get('variants') and p.get('images'):
            for v in p['variants']:
                image_id = v.get('image_id')
                if image_id:
                    for img in p['images']:
                        if img.get('id') == image_id and img.get('src'):
                            return img['src']
        return None
    return [Product(
        id=str(p.get('id', '')),
        title=p.get('title', ''),
        url=f"{base_url}/products/{p.get('handle', '')}" if p.get('handle') else None,
        image=get_image_src(p),
        price=str(p.get('variants', [{}])[0].get('price', '')) if p.get('variants') else None,
        description=p.get('body_html', '')
    ) for p in products_raw]

def map_hero_products(hero_raw: List[Dict[str, Any]]) -> List[Product]:
    return [Product(
        id=None,
        title=p.get('title', ''),
        url=p.get('url'),
        image=p.get('image'),
        price=None,
        description=None
    ) for p in hero_raw]

def map_policies(policies_raw: List[Dict[str, Any]]) -> List[Policy]:
    return [Policy(
        type=p.get('type', ''),
        url=p.get('url'),
        content=p.get('content')
    ) for p in policies_raw]

def map_faqs(faqs_raw: List[Dict[str, Any]]) -> List[FAQ]:
    return [FAQ(
        question=f.get('question', ''),
        answer=f.get('answer', '')
    ) for f in faqs_raw]

def map_social_handles(social_raw: List) -> List[SocialHandle]:
    result = []
    for s in social_raw:
        if isinstance(s, dict):
            result.append(SocialHandle(
                platform=s.get('platform', ''),
                url=s.get('url', '')
            ))
        elif isinstance(s, str):
            result.append(SocialHandle(
                platform='',
                url=s
            ))
    return result

def map_contact_details(contact_raw: List) -> List[ContactDetail]:
    result = []
    for c in contact_raw:
        if isinstance(c, dict):
            result.append(ContactDetail(
                type=c.get('type', ''),
                value=c.get('value', '')
            ))
        elif isinstance(c, str):
            result.append(ContactDetail(
                type='',
                value=c
            ))
    return result

def map_important_links(important_links_raw: List) -> List[ImportantLink]:
    result = []
    for l in important_links_raw:
        if isinstance(l, dict):
            result.append(ImportantLink(
                name=l.get('name', ''),
                url=l.get('url', '')
            ))
        elif isinstance(l, str):
            result.append(ImportantLink(
                name='',
                url=l
            ))
    return result 