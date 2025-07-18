import httpx  # type: ignore
from typing import List, Dict, Optional
from bs4 import BeautifulSoup  # type: ignore
from bs4.element import Tag  # type: ignore
import re
import logging
import asyncio

logger = logging.getLogger(__name__)

class ShopifyScraper:
    def __init__(self, base_url: str, timeout: float = 8.0, max_retries: int = 2):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries

    async def _get(self, url: str) -> Optional[httpx.Response]:
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return resp
                    else:
                        logger.warning(f"Non-200 response for {url}: {resp.status_code}")
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(f"HTTP error for {url} (attempt {attempt+1}): {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
        logger.error(f"Failed to fetch {url} after {self.max_retries+1} attempts.")
        return None

    async def fetch_product_catalog(self) -> List[Dict]:
        url = f"{self.base_url}/products.json"
        resp = await self._get(url)
        if resp:
            try:
                data = resp.json()
                products = data.get('products', [])
                return products
            except Exception as e:
                logger.error(f"Error parsing product catalog JSON for {url}: {e}")
        return []

    async def fetch_hero_products(self) -> List[Dict]:
        url = self.base_url
        resp = await self._get(url)
        if not resp:
            return []
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            hero_products = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/products/' in href:
                    title = a.get_text(strip=True)
                    # Try to get image if present
                    img = a.find('img')
                    image = None
                    if img and img.has_attr('src'):
                        image = img['src']
                    else:
                        # Try to find sibling or parent image
                        parent_img = a.parent.find('img') if a.parent else None
                        if parent_img and parent_img.has_attr('src'):
                            image = parent_img['src']
                        else:
                            sibling_img = a.find_next_sibling('img')
                            if sibling_img and sibling_img.has_attr('src'):
                                image = sibling_img['src']
                    hero_products.append({
                        'title': title,
                        'url': href if href.startswith('http') else self.base_url + href,
                        'image': image
                    })
            seen = set()
            unique_hero_products = []
            for p in hero_products:
                if p['url'] not in seen:
                    unique_hero_products.append(p)
                    seen.add(p['url'])
            return unique_hero_products
        except Exception as e:
            logger.error(f"Error parsing hero products for {url}: {e}")
            return []

    async def fetch_policies(self) -> List[Dict]:
        policy_types = {
            'privacy': '/policies/privacy-policy',
            'refund': '/policies/refund-policy',
            'shipping': '/policies/shipping-policy',
            'terms': '/policies/terms-of-service',
        }
        results = []
        for ptype, path in policy_types.items():
            url = self.base_url + path
            resp = await self._get(url)
            if resp:
                try:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    content = soup.get_text(separator='\n', strip=True)
                    results.append({
                        'type': ptype,
                        'url': url,
                        'content': content
                    })
                except Exception as e:
                    logger.error(f"Error parsing policy page {url}: {e}")
        return results

    async def fetch_faqs(self) -> List[Dict]:
        faq_paths = ['/pages/faq', '/pages/faqs', '/faq', '/faqs']
        for path in faq_paths:
            url = self.base_url + path
            resp = await self._get(url)
            if resp:
                try:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    faqs = []
                    for item in soup.find_all(class_=['faq', 'faq-item']):
                        q = item.find(['h2', 'h3', 'h4', 'strong'])
                        a = item.find(['p', 'div'])
                        if q and a:
                            faqs.append({'question': q.get_text(strip=True), 'answer': a.get_text(strip=True)})
                    for details in soup.find_all('details'):
                        summary = details.find('summary')
                        if summary:
                            question = summary.get_text(strip=True)
                            answer = details.get_text(strip=True).replace(question, '', 1).strip()
                            faqs.append({'question': question, 'answer': answer})
                    headers = soup.find_all(['h2', 'h3'])
                    for h in headers:
                        next_p = h.find_next_sibling('p')
                        if next_p:
                            faqs.append({'question': h.get_text(strip=True), 'answer': next_p.get_text(strip=True)})
                    if faqs:
                        return faqs
                except Exception as e:
                    logger.error(f"Error parsing FAQ page {url}: {e}")
        return []

    async def fetch_homepage(self) -> Optional[str]:
        url = self.base_url
        resp = await self._get(url)
        if resp:
            return resp.text
        return None

    async def fetch_social_handles(self) -> List[Dict]:
        html = await self.fetch_homepage()
        if not html:
            return []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            social_domains = {
                'instagram': 'instagram.com',
                'facebook': 'facebook.com',
                'twitter': 'twitter.com',
                'tiktok': 'tiktok.com',
                'youtube': 'youtube.com',
                'pinterest': 'pinterest.com',
                'linkedin': 'linkedin.com',
            }
            handles = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                for platform, domain in social_domains.items():
                    if domain in href:
                        handles.append({'platform': platform, 'url': href})
            seen = set()
            unique_handles = []
            for h in handles:
                if h['url'] not in seen:
                    unique_handles.append(h)
                    seen.add(h['url'])
            return unique_handles
        except Exception as e:
            logger.error(f"Error parsing social handles from homepage: {e}")
            return []

    async def fetch_contact_details(self) -> List[Dict]:
        html = await self.fetch_homepage()
        if not html:
            return []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            contacts = []
            email_regex = re.compile(r'[\w\.-]+@[\w\.-]+')
            for text in soup.stripped_strings:
                for match in email_regex.findall(text):
                    contacts.append({'type': 'email', 'value': match})
            phone_regex = re.compile(r'\+?\d[\d\s\-()]{7,}\d')
            for text in soup.stripped_strings:
                for match in phone_regex.findall(text):
                    contacts.append({'type': 'phone', 'value': match})
            seen = set()
            unique_contacts = []
            for c in contacts:
                key = (c['type'], c['value'])
                if key not in seen:
                    unique_contacts.append(c)
                    seen.add(key)
            return unique_contacts
        except Exception as e:
            logger.error(f"Error parsing contact details from homepage: {e}")
            return []

    async def fetch_brand_text(self) -> Optional[str]:
        html = await self.fetch_homepage()
        if not html:
            return None
        try:
            soup = BeautifulSoup(html, 'html.parser')
            about_selectors = [
                {'id': 'about'},
                {'class_': 'about'},
                {'id': 'about-us'},
                {'class_': 'about-us'},
            ]
            for sel in about_selectors:
                tag = soup.find(attrs=sel)
                if tag and hasattr(tag, 'get_text'):
                    return tag.get_text(separator=' ', strip=True)
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta and isinstance(meta, Tag) and 'content' in meta.attrs:
                content = meta.attrs['content']
                if isinstance(content, str):
                    return content
                elif isinstance(content, list) and content:
                    return content[0]
            return None
        except Exception as e:
            logger.error(f"Error parsing brand text from homepage: {e}")
            return None

    async def fetch_important_links(self) -> List[Dict]:
        html = await self.fetch_homepage()
        if not html:
            return []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            important_keywords = ['order', 'track', 'contact', 'blog', 'faq', 'help', 'support']
            links = []
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True).lower()
                href = a['href']
                if any(kw in text for kw in important_keywords):
                    links.append({'name': a.get_text(strip=True), 'url': href if href.startswith('http') else self.base_url + href})
            seen = set()
            unique_links = []
            for l in links:
                if l['url'] not in seen:
                    unique_links.append(l)
                    seen.add(l['url'])
            return unique_links
        except Exception as e:
            logger.error(f"Error parsing important links from homepage: {e}")
            return [] 