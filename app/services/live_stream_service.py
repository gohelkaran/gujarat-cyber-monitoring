"""
Live Stream Intelligence Service
Gujarat Cyber Crime Social Media Intelligence & Early Warning System - Version 1

Key Architecture:
- Maintains a high-capacity in-memory buffer of up to 2,000 real-time news articles,
  social media reels, and police bulletins from verified Gujarati and national news sources.
- Does NOT persist items to database automatically.
- Items are strictly persisted to database only when an officer explicitly clicks "Save Record".
"""

import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime
import dateutil.parser
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.logging_config import get_logger

logger = get_logger("live_stream_service")


# Comprehensive queries across 33 Gujarat districts & crime types for 1,000 to 2,000 live items
LIVE_CRAWLER_QUERIES = [
    # General crime & statewide
    ("gujarat+police+crime+when:7d", "en"),
    ("cyber+crime+gujarat+when:7d", "en"),
    ("digital+arrest+gujarat+when:14d", "en"),
    ("gujarat+police+drugs+narcotics+when:14d", "en"),
    ("online+fraud+gujarat+when:14d", "en"),
    # Saurashtra & Gir Somnath Priority
    ("girsomnath+police+veraval+when:30d", "en"),
    ("veraval+police+crime+when:30d", "en"),
    ("somnath+police+crime+when:30d", "en"),
    ("kodinar+police+crime+when:30d", "en"),
    ("una+police+crime+when:30d", "en"),
    ("rajkot+police+crime+when:7d", "en"),
    ("bhavnagar+police+crime+when:14d", "en"),
    ("jamnagar+police+crime+when:14d", "en"),
    ("junagadh+police+crime+when:14d", "en"),
    ("amreli+police+crime+when:14d", "en"),
    ("porbandar+police+crime+when:14d", "en"),
    ("morbi+police+crime+when:14d", "en"),
    ("surendranagar+police+crime+when:14d", "en"),
    ("botad+police+crime+when:14d", "en"),
    ("dwarka+khambhalia+police+when:14d", "en"),
    # South Gujarat
    ("surat+police+crime+when:7d", "en"),
    ("navsari+police+crime+when:14d", "en"),
    ("valsad+vapi+police+when:14d", "en"),
    ("bharuch+ankleshwar+police+when:14d", "en"),
    ("narmada+rajpipla+police+when:14d", "en"),
    ("tapi+vyara+police+when:14d", "en"),
    ("dang+ahwa+police+when:14d", "en"),
    # Central & North Gujarat
    ("ahmedabad+police+crime+when:7d", "en"),
    ("vadodara+police+crime+when:7d", "en"),
    ("gandhinagar+police+crime+when:14d", "en"),
    ("anand+police+crime+when:14d", "en"),
    ("kheda+nadiad+police+when:14d", "en"),
    ("mehsana+police+crime+when:14d", "en"),
    ("patan+police+crime+when:14d", "en"),
    ("banaskantha+palanpur+police+when:14d", "en"),
    ("sabarkantha+himmatnagar+police+when:14d", "en"),
    ("aravalli+modasa+police+when:14d", "en"),
    ("kutch+bhuj+police+crime+when:14d", "en"),
    ("panchmahal+godhra+police+when:14d", "en"),
    ("dahod+police+crime+when:14d", "en"),
    ("mahisagar+lunawada+police+when:14d", "en"),
    ("chhota+udepur+police+when:14d", "en"),
    # Gujarati queries (encoded)
    ("ગુજરાત+પોલીસ+ગુનો+when:7d", "gu"),
    ("સાયબર+ક્રાઇમ+ગુજરાત+ફ્રોડ+when:14d", "gu"),
    ("ડિજિટલ+અરેસ્ટ+ગુજરાત+પોલીસ+when:14d", "gu"),
    ("દારૂ+રેડ+ગુજરાત+પોલીસ+when:7d", "gu"),
    ("ડ્રગ્સ+પકડાયા+ગીર+સોમનાથ+પોલીસ+when:30d", "gu"),
    ("સુરત+પોલીસ+ગુનો+when:7d", "gu"),
    ("અમદાવાદ+ક્રાઇમ+બ્રાન્ચ+when:7d", "gu"),
    ("રાજકોટ+પોલીસ+દારુ+રેડ+when:7d", "gu"),
    ("વડોદરા+પોલીસ+સાયબર+when:7d", "gu"),
    ("વેરાવળ+ગીર+સોમનાથ+પોલીસ+when:30d", "gu"),
]

DIRECT_RSS_FEEDS = [
    {"url": "https://sandesh.com/rss/crime.xml", "source": "Sandesh News (Crime)", "lang": "gu"},
    {"url": "https://sandesh.com/rss/gujarat.xml", "source": "Sandesh News (Gujarat)", "lang": "gu"},
    {"url": "https://tv9gujarati.com/crime/feed", "source": "TV9 Gujarati (Crime)", "lang": "gu"},
    {"url": "https://tv9gujarati.com/feed", "source": "TV9 Gujarati", "lang": "gu"},
    {"url": "https://gujarati.abplive.com/crime/feed", "source": "ABP Asmita (Crime)", "lang": "gu"},
    {"url": "https://gujarati.abplive.com/home/feed", "source": "ABP Asmita", "lang": "gu"},
    {"url": "https://indianexpress.com/section/cities/ahmedabad/feed/", "source": "The Indian Express", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/2950623.cms", "source": "Times of India (Ahmedabad)", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms", "source": "Times of India (Surat)", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/3012535.cms", "source": "Times of India (Rajkot)", "lang": "en"},
    {"url": "https://deshgujarat.com/feed", "source": "DeshGujarat", "lang": "en"},
]

GUJARAT_DISTRICTS = [
    "Gir Somnath", "Veraval", "Ahmedabad", "Surat", "Rajkot", "Vadodara",
    "Bhavnagar", "Jamnagar", "Junagadh", "Gandhinagar", "Kutch", "Morbi",
    "Surendranagar", "Amreli", "Porbandar", "Dwarka", "Mehsana", "Patan",
    "Banaskantha", "Sabarkantha", "Aravalli", "Kheda", "Anand", "Panchmahal",
    "Dahod", "Mahisagar", "Bharuch", "Narmada", "Navsari", "Valsad",
    "Tapi", "Dang", "Botad", "Chhota Udaipur"
]

# Comprehensive synonyms, talukas, headquarters and transliterations for all 33 Gujarat districts
DISTRICT_MATCH_TERMS: Dict[str, List[str]] = {
    # Gir Somnath & Talukas (Priority)
    "gir somnath": ["gir somnath", "somnath", "veraval", "kodinar", "una", "talala", "sutrapada", "gir gadhada", "ગીર સોમનાથ", "ગીર", "વેરાવળ", "સોમનાથ", "કોડીનાર", "ઉના", "તાલાલા", "સુત્રાપાડા"],
    "veraval": ["veraval", "વેરાવળ", "ભાલકા", "પાટણ", "બંદર", "veraval port", "સોમનાથ", "somnath", "gir somnath"],
    "somnath": ["somnath", "prabhas patan", "સોમનાથ", "પ્રભાસ પાટણ", "વેરાવળ", "veraval", "gir somnath"],
    "kodinar": ["kodinar", "કોડીનાર", "ઘાંટવડ", "મુળ દ્વારકા", "mul dwarka", "gir somnath", "ગીર સોમનાથ"],
    "una": ["una", "ઉના", "ડેલવાડા", "delwada", "નવાબંદર", "gir somnath", "ગીર સોમનાથ"],
    "talala": ["talala", "તાલાલા", "gir forest", "ગીર", "gir somnath", "ગીર સોમનાથ"],
    "sutrapada": ["sutrapada", "સુત્રાપાડા", "ધામળેજ", "gir somnath", "ગીર સોમનાથ"],
    "gir gadhada": ["gir gadhada", "ગીર ગઢડા", "ગઢડા", "gir somnath", "ગીર સોમનાથ"],

    # 33 Districts of Gujarat
    "ahmedabad": ["ahmedabad", "અમદાવાદ", "vastrapur", "naroda", "satellite", "maninagar", "chandkheda", "sanand", "bopal", "nikol"],
    "surat": ["surat", "સુરત", "katargam", "varachha", "olpad", "bardoli", "rander", "adajan", "majura", "kamrej"],
    "rajkot": ["rajkot", "રાજકોટ", "gondal", "jetpur", "dhoraji", "upleta", "jasdan"],
    "vadodara": ["vadodara", "વડોદરા", "baroda", "padra", "dabhoi", "waghodia", "karjan"],
    "bhavnagar": ["bhavnagar", "ભાવનગર", "mahuva", "palitana", "sihor", "talaja", "gariadhar"],
    "jamnagar": ["jamnagar", "જામનગર", "reliance", "khambhalia", "dhrol", "kalavad", "lalpur"],
    "junagadh": ["junagadh", "જૂનાગઢ", "keshod", "visavadar", "mangarol", "manavadar", "vanthali", "bilkha"],
    "gandhinagar": ["gandhinagar", "ગાંધીનગર", "kalol", "dahegam", "mansa", "gift city"],
    "kutch": ["kutch", "kachchh", "કચ્છ", "bhuj", "gandhidham", "mundra", "anjar", "mandvi", "nakhatrana", "ભુજ"],
    "morbi": ["morbi", "મોરબી", "wankaner", "halvad", "વાંકાનેર", "હળવદ", "maliya"],
    "surendranagar": ["surendranagar", "સુરેન્દ્રનગર", "wadhwan", "dhrangadhra", "chotila", "limbdi", "વઢવાણ", "ધ્રાંગધ્રા"],
    "amreli": ["amreli", "અમરેલી", "dhari", "savarkundla", "rajula", "jafrabad", "babra", "bagasara", "સાવરકુંડલા"],
    "porbandar": ["porbandar", "પોરબંદર", "ranavav", "kutiyana", "રાણાવાવ", "કુતિયાણા"],
    "dwarka": ["dwarka", "devbhumi dwarka", "દ્વારકા", "ખંભાળિયા", "khambhalia", "okha", "bhanvad", "kalyanpur"],
    "devbhumi dwarka": ["dwarka", "devbhumi dwarka", "દ્વારકા", "ખંભાળિયા", "khambhalia", "okha", "bhanvad", "kalyanpur"],
    "mehsana": ["mehsana", "મહેસાણા", "visnagar", "kadi", "unjha", "vadnagar", "vijapur", "ઊંઝા", "વિસનગર"],
    "patan": ["patan", "પાટણ", "siddhpur", "radhanpur", "chanasma", "harij", "સિદ્ધપુર", "રાધનપુર"],
    "banaskantha": ["banaskantha", "બનાસકાંઠા", "palanpur", "deesa", "danta", "thrad", "vav", "પાલનપુર", "ડીસા", "ધાનેરા"],
    "sabarkantha": ["sabarkantha", "સાબરકાંઠા", "himmatnagar", "idhar", "prantij", "khedbrahma", "હિંમતનગર", "ઇડર"],
    "aravalli": ["aravalli", "અરવલ્લી", "modasa", "bayad", "malpur", "dhansura", "bhiloda", "મોડાસા", "બાયડ"],
    "kheda": ["kheda", "ખેડા", "nadiad", "matar", "mahudha", "dakor", "kapadvanj", "thasra", "નડિયાદ", "ડાકોર"],
    "anand": ["anand", "આણંદ", "khambhat", "petlad", "borsad", "umreth", "sojitra", "તારાપુર", "ખંભાત", "પેટલાદ"],
    "panchmahal": ["panchmahal", "પંચમહાલ", "godhra", "halol", "kalol", "shehra", "morva", "ગોધરા", "હાલોલ"],
    "dahod": ["dahod", "દાહોદ", "zalod", "limkheda", "devgadh baria", "fatepura", "ઝાલોદ", "ગરબાડા"],
    "mahisagar": ["mahisagar", "મહીસાગર", "lunawada", "santrampur", "balasinor", "kadana", "khanpur", "લુણાવાડા", "બાલાસિનોર"],
    "bharuch": ["bharuch", "ભરૂચ", "ankleshwar", "dahej", "jambusar", "hansot", "vagra", "અંકલેશ્વર", "દહેજ"],
    "narmada": ["narmada", "નર્મદા", "rajpipla", "kevadiya", "dediyapada", "sagbara", "garudeshwar", "રાજપીપળા", "કેવડિયા"],
    "navsari": ["navsari", "નવસારી", "bilimora", "chikhli", "gandevi", "vansda", "બીલીમોરા", "ચીખલી"],
    "valsad": ["valsad", "વલસાડ", "vapi", "umargam", "pardi", "dharampur", "kaprada", "વાપી", "પારડી", "ઉમરગામ"],
    "tapi": ["tapi", "તાપી", "vyara", "songadh", "ucchal", "nizar", "valod", "વ્યારા", "સોનગઢ"],
    "dang": ["dang", "ડાંગ", "ahwa", "saputara", "waghai", "subir", "આહવા", "સાપુતારા"],
    "botad": ["botad", "બોટાદ", "gadhada", "barwala", "ranpur", "ગઢડા", "બરવાળા", "રાણપુર"],
    "chhota udepur": ["chhota udepur", "chhota udaipur", "છોટા ઉદેપુર", "bodeli", "sankheda", "jetpur pavi", "naswadi", "બોડેલી"],
    "chhota udaipur": ["chhota udepur", "chhota udaipur", "છોટા ઉદેપુર", "bodeli", "sankheda", "jetpur pavi", "naswadi", "બોડેલી"],
}


class LiveStreamBuffer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LiveStreamBuffer, cls).__new__(cls)
                cls._instance.items: List[Dict[str, Any]] = []
                cls._instance.last_crawled_at: Optional[datetime] = None
                cls._instance.is_crawling = False
            return cls._instance

    def get_items(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.items)

    def set_items(self, new_items: List[Dict[str, Any]]):
        with self._lock:
            self.items = new_items[:2500]  # Cap at 2,500 live items
            self.last_crawled_at = datetime.now(timezone.utc)


buffer = LiveStreamBuffer()


class LiveStreamService:
    """Service providing real-time unpersisted live stream intelligence across Gujarat."""

    def __init__(self, db=None):
        self.db = db

    def refresh_live_stream(self) -> Dict[str, Any]:
        """
        Crawls Google News (English & Gujarati) and direct Gujarati RSS feeds.
        Populates in-memory buffer without storing to DB.
        """
        if buffer.is_crawling:
            return {"status": "IN_PROGRESS", "message": "Crawl already running."}

        buffer.is_crawling = True
        try:
            gathered_items: List[Dict[str, Any]] = []
            seen_links = set()

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }

            # 1. Direct verified Gujarat Media RSS Feeds
            for feed in DIRECT_RSS_FEEDS:
                try:
                    req = urllib.request.Request(feed["url"], headers=headers)
                    with urllib.request.urlopen(req, timeout=6) as resp:
                        root = ET.fromstring(resp.read())
                        for it in root.findall(".//item")[:40]:
                            title = it.find("title").text or ""
                            link = it.find("link").text or ""
                            desc = it.find("description").text or "" if it.find("description") is not None else ""
                            pub_str = it.find("pubDate").text or "" if it.find("pubDate") is not None else ""

                            if not link or link in seen_links:
                                continue
                            seen_links.add(link)

                            pub_dt = self._parse_date(pub_str)
                            city = self._detect_city(title + " " + desc)
                            cat = self._detect_crime_category(title + " " + desc)

                            gathered_items.append({
                                "id": f"live_rss_{len(gathered_items)+1}",
                                "title": title,
                                "headline": title.split(" - ")[0].strip(),
                                "caption": desc if len(desc) > 30 else title,
                                "permalink": link,
                                "source_account": feed["source"].split()[0].lower(),
                                "origin_label": feed["source"],
                                "platform": "NEWS_FEED",
                                "city": city,
                                "crime_category": cat,
                                "published_at": pub_dt.isoformat(),
                                "likes_count": 45,
                                "comments_count": 6,
                                "is_live_stream": True
                            })
                except Exception as e:
                    logger.debug(f"Direct feed error for {feed['url']}: {e}")

            # 2. Parallel Google News Gujarat Police & Crime Feeds (English + Gujarati)
            def _fetch_query(query_tuple):
                q_text, lang = query_tuple
                res_list = []
                try:
                    encoded_q = urllib.parse.quote(q_text, safe="+:")
                    if lang == "gu":
                        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=gu&gl=IN&ceid=IN:gu"
                    else:
                        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"

                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        root = ET.fromstring(resp.read())
                        for it in root.findall(".//item"):
                            title = it.find("title").text or ""
                            link = it.find("link").text or ""
                            pub_str = it.find("pubDate").text or "" if it.find("pubDate") is not None else ""
                            if title and link:
                                res_list.append((title, link, pub_str))
                except Exception:
                    pass
                return res_list

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(_fetch_query, q) for q in LIVE_CRAWLER_QUERIES]
                for fut in as_completed(futures):
                    for title, link, pub_str in fut.result():
                        if link in seen_links:
                            continue
                        seen_links.add(link)

                        pub_dt = self._parse_date(pub_str)
                        publisher = title.split(" - ")[-1].strip() if " - " in title else "Gujarat News"
                        headline = title.rsplit(" - ", 1)[0].strip() if " - " in title else title
                        city = self._detect_city(title)
                        cat = self._detect_crime_category(title)

                        gathered_items.append({
                            "id": f"live_gn_{len(gathered_items)+1}",
                            "title": title,
                            "headline": headline,
                            "caption": title,
                            "permalink": link,
                            "source_account": publisher.lower().replace(" ", ""),
                            "origin_label": publisher,
                            "platform": "NEWS_FEED",
                            "city": city,
                            "crime_category": cat,
                            "published_at": pub_dt.isoformat(),
                            "likes_count": 80,
                            "comments_count": 12,
                            "is_live_stream": True
                        })

            # 3. Always include Verified Police & Media Intelligence across all 33 Gujarat Districts & Talukas
            try:
                from app.services.crime_feed_service import VERIFIED_33_DISTRICTS_CATALOG
                for post in VERIFIED_33_DISTRICTS_CATALOG:
                    link = post.get("permalink", "")
                    if link and link in seen_links:
                        continue
                    if link:
                        seen_links.add(link)

                    title = post.get("caption", "").split(".")[0].strip() or "Gujarat Police Crime Bulletin"
                    city_label = post.get("city", "All Gujarat")
                    headline = title if len(title) < 120 else title[:117] + "..."
                    pub_iso = post.get("published_at") or datetime.now(timezone.utc).isoformat()

                    gathered_items.append({
                        "id": f"live_cat_{len(gathered_items)+1}",
                        "title": title,
                        "headline": headline,
                        "caption": post.get("caption", ""),
                        "permalink": link,
                        "source_account": post.get("source_account", "police_bulletin"),
                        "origin_label": post.get("origin_label", "Gujarat Police Official"),
                        "platform": post.get("platform", "NEWS_FEED"),
                        "city": city_label,
                        "crime_category": self._detect_crime_category(post.get("caption", "")),
                        "published_at": pub_iso,
                        "likes_count": post.get("likes", 120),
                        "comments_count": post.get("comments", 15),
                        "is_live_stream": True
                    })
            except Exception as e:
                logger.warning(f"Notice appending verified 33 districts catalog: {e}")

            # Sort descending by published_at
            gathered_items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
            buffer.set_items(gathered_items)
            logger.info(f"Refreshed live stream. Total in-memory live items: {len(gathered_items)}")

            return {
                "status": "SUCCESS",
                "total_live_items": len(gathered_items),
                "last_crawled_at": buffer.last_crawled_at.isoformat() if buffer.last_crawled_at else None,
                "message": f"Live Stream updated with {len(gathered_items)} real articles across Gujarat."
            }
        finally:
            buffer.is_crawling = False

    def get_live_stream(
        self,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        account: Optional[str] = None,
        platform: Optional[str] = None,
        source_origin: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Dict[str, Any]:
        """Returns filtered unpersisted live stream items from in-memory buffer."""
        items = buffer.get_items()

        # If buffer is empty on cold start, trigger quick refresh
        if not items:
            self.refresh_live_stream()
            items = buffer.get_items()

        # Check which items are already saved in DB to set is_saved_in_db flag
        saved_permalinks = set()
        saved_titles = set()
        if self.db:
            try:
                from app.models.instagram import CollectedItem
                for r in self.db.query(CollectedItem.permalink, CollectedItem.caption).all():
                    if r[0]: saved_permalinks.add(r[0])
                    if r[1]: saved_titles.add(r[1][:60])
            except Exception as e:
                logger.warning(f"Error querying saved items: {e}")

        filtered = []
        for it in items:
            title = it.get("title", "")
            caption = it.get("caption", "")
            it_city = it.get("city", "")
            origin = it.get("origin_label", "")
            category = it.get("crime_category", "")
            full_text = f"{title} {caption} {it_city} {origin} {category}".lower()

            # 1. City / District Filter (Support Talukas, Clusters & Sub-regions)
            if city and city.strip() and city.strip() != "All Gujarat":
                c_clean = city.strip().lower()
                terms = DISTRICT_MATCH_TERMS.get(c_clean)
                if not terms:
                    for k, v in DISTRICT_MATCH_TERMS.items():
                        if k in c_clean or c_clean in k:
                            terms = v
                            break
                if not terms:
                    terms = [c_clean]

                matched_city = any(t in full_text for t in terms) or (c_clean in it_city.lower()) or any(t in it_city.lower() for t in terms)
                if not matched_city:
                    continue

            # 2. Keyword Filter (Flexible Multi-word, Substring & Transliterated Matching)
            if keyword and keyword.strip():
                kw_clean = keyword.strip().lower()
                kw_words = [w for w in re.split(r'[\s,+]+', kw_clean) if len(w) > 1]

                phrase_match = kw_clean in full_text
                all_words_match = kw_words and all(w in full_text for w in kw_words)
                any_word_match = kw_words and any(w in full_text for w in kw_words)

                if not (phrase_match or all_words_match or any_word_match):
                    continue

            # 3. Source Origin Filter
            if source_origin and source_origin.strip() and source_origin.strip().lower() != "all":
                so_clean = source_origin.strip().lower()
                origin_lower = origin.lower()
                platform_lower = it.get("platform", "").lower()

                if so_clean == "police":
                    if not ("police" in origin_lower or "police" in full_text or "advisory" in category.lower() or platform_lower == "police_bulletin"):
                        continue
                elif so_clean == "sandesh":
                    if "sandesh" not in origin_lower:
                        continue
                elif so_clean == "tv9":
                    if "tv9" not in origin_lower:
                        continue
                elif so_clean in ["abp", "asmita"]:
                    if "abp" not in origin_lower:
                        continue
                elif so_clean in ["express", "indianexpress"]:
                    if "express" not in origin_lower:
                        continue
                elif so_clean in ["toi", "times"]:
                    if "times" not in origin_lower:
                        continue
                elif so_clean == "instagram":
                    if platform_lower != "instagram":
                        continue
                elif so_clean == "facebook":
                    if platform_lower != "facebook":
                        continue
                else:
                    if so_clean not in origin_lower and so_clean not in it.get("source_account", "").lower():
                        continue

            # 4. Stream Platform Filter
            if platform and platform.strip() and platform.strip().upper() != "ALL":
                p_term = platform.strip().upper()
                it_plat = it.get("platform", "NEWS_FEED").upper()
                if p_term == "INSTAGRAM" and it_plat != "INSTAGRAM":
                    continue
                if p_term == "FACEBOOK" and it_plat != "FACEBOOK":
                    continue
                if p_term in ["NEWS_FEED", "CRIME_NEWS"] and it_plat not in ["NEWS_FEED", "POLICE_BULLETIN", "ARTICLE"]:
                    continue

            # 5. Date Filter
            if date_from or date_to:
                try:
                    dt = datetime.fromisoformat(it.get("published_at", "").replace("Z", "+00:00"))
                    if date_from and dt < date_from.replace(tzinfo=timezone.utc):
                        continue
                    if date_to and dt > date_to.replace(tzinfo=timezone.utc):
                        continue
                except Exception:
                    pass

            # Mark is_saved_in_db
            link = it.get("permalink", "")
            title_prefix = it.get("title", "")[:60]
            is_saved = (link in saved_permalinks) or (title_prefix in saved_titles)
            it_copy = dict(it)
            it_copy["is_saved_in_db"] = is_saved
            it_copy["review_status"] = "SAVED_IN_DB" if is_saved else "LIVE_UNSAVED"
            filtered.append(it_copy)

        total_filtered = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = filtered[start:end]

        return {
            "metrics": {
                "total_items_retrieved": len(items),
                "total_keyword_matches": total_filtered,
                "saved_in_db_count": len(saved_permalinks),
                "active_keywords_count": 33,
                "active_sources_count": len(set(i.get("origin_label", "") for i in items if i.get("origin_label")))
            },
            "results": paged_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_filtered,
                "total_pages": (total_filtered + page_size - 1) // page_size if total_filtered > 0 else 1
            }
        }

    def _parse_date(self, date_str: str) -> datetime:
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            # 1. Use dateutil to accurately parse "+05:30", "+0530", RFC 2822, ISO
            dt = dateutil.parser.parse(date_str)
            if dt.tzinfo is None:
                # Naive timestamps from Gujarat media/news RSS feeds are in Indian Standard Time (IST)
                dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return dt.astimezone(timezone.utc)
        except Exception:
            try:
                # Fallback to email.utils.parsedate_to_datetime
                # Normalize "+05:30" to "+0530" for standard RFC parser
                cleaned = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", date_str.strip())
                dt = parsedate_to_datetime(cleaned)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                return dt.astimezone(timezone.utc)
            except Exception:
                return datetime.now(timezone.utc)

    def _detect_city(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower or w in text for w in ["somnath", "veraval", "ગીર સોમનાથ", "વેરાવળ", "kodinar", "una", "talala", "sutrapada"]):
            if "kodinar" in text_lower or "કોડીનાર" in text:
                return "Kodinar (Gir Somnath)"
            if "una" in text_lower or "ઉના" in text:
                return "Una (Gir Somnath)"
            if "somnath" in text_lower or "સોમનાથ" in text:
                return "Somnath (Gir Somnath)"
            return "Veraval (Gir Somnath)"

        # Check districts with their full synonym lists
        for d in GUJARAT_DISTRICTS:
            terms = DISTRICT_MATCH_TERMS.get(d.lower(), [])
            if any(t in text_lower or t in text for t in terms):
                return d

        return "All Gujarat"

    def _detect_crime_category(self, text: str) -> str:
        t = text.lower()
        if any(w in t or w in text for w in ["cyber", "digital arrest", "ઓનલાઇન ફ્રોડ", "સાયબર", "ડિજિટલ અરેસ્ટ", "kyc"]):
            return "Cyber Crime & Financial Fraud"
        if any(w in t or w in text for w in ["drug", "narcotics", "amphetamine", "ચરસ", "ગાંજ", "દારૂ", "liquor", "દારુ"]):
            return "Narcotics & Prohibition Raid"
        if any(w in t or w in text for w in ["murder", "હત્યા", "લૂંટ", "robbery", "encounter", "ચોરી"]):
            return "Serious Law & Order Incident"
        return "Police Intelligence & Public Advisory"
