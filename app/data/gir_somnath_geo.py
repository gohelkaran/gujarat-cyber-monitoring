"""
Gir Somnath District Comprehensive Village, Taluka & Police Station Geo-Intelligence Dictionary
Gujarat Cyber Crime Social Media & Early Warning System

Covers all 6 Talukas of Gir Somnath District with:
- Taluka Names (English & Gujarati)
- Key Villages, Coastal Landing Points & Hamlets
- Designated Police Station Jurisdictions
- Operational Security Cluster (Marine/Port, Pilgrimage, Wildlife/Forest, Industrial, Rural/Border)
"""

import re
from typing import Dict, Any, List, Optional

# =============================================================================
# GIR SOMNATH TALUKA & VILLAGE POLICE JURISDICTION MAP
# =============================================================================

GIR_SOMNATH_JURISDICTIONS: Dict[str, Dict[str, Any]] = {
    "Veraval": {
        "gujarati_name": "વેરાવળ",
        "cluster": "Coastal & Marine Headquarters",
        "primary_ps": ["Veraval City Police Station", "Veraval Rural Police Station", "Veraval Marine Police Station"],
        "villages": [
            {"name_en": "Veraval Port / Bunder", "name_gu": "વેરાવળ બંદર", "ps": "Veraval Marine PS", "keywords": ["veraval port", "વેરાવળ બંદર", "બંદર", "fishing harbor", "ખારવાવાડ"]},
            {"name_en": "Bhalka", "name_gu": "ભાલકા", "ps": "Veraval City PS", "keywords": ["bhalka", "ભાલકા", "ભાલકા તીર્થ"]},
            {"name_en": "Inaj", "name_gu": "ઇણાજ", "ps": "Veraval Rural PS", "keywords": ["inaj", "ઇણાજ", "collector office inaj"]},
            {"name_en": "Adri", "name_gu": "આદ્રી", "ps": "Veraval Rural PS", "keywords": ["adri", "આદ્રી", "adri beach"]},
            {"name_en": "Dari", "name_gu": "ડારી", "ps": "Veraval Rural PS", "keywords": ["dari", "ડારી"]},
            {"name_en": "Supasi", "name_gu": "સુપાસી", "ps": "Veraval Rural PS", "keywords": ["supasi", "સુપાસી"]},
            {"name_en": "Govindpara", "name_gu": "ગોવિંદપરા", "ps": "Veraval City PS", "keywords": ["govindpara", "ગોવિંદપરા"]},
            {"name_en": "Navapara", "name_gu": "નવાપરા", "ps": "Veraval City PS", "keywords": ["navapara", "નવાપરા"]},
            {"name_en": "Bhidbhanjan", "name_gu": "ભીડભંજન", "ps": "Veraval City PS", "keywords": ["bhidbhanjan", "ભીડભંજન"]},
            {"name_en": "Patasagar", "name_gu": "પાટસાગર", "ps": "Veraval Rural PS", "keywords": ["patasagar", "પાટસાગર"]},
            {"name_en": "Mithapur", "name_gu": "મીઠાપુર", "ps": "Veraval Rural PS", "keywords": ["mithapur veraval", "મીઠાપુર"]},
            {"name_en": "Savni", "name_gu": "સાવણી", "ps": "Veraval Rural PS", "keywords": ["savni", "સાવણી"]},
            {"name_en": "Bhalpara", "name_gu": "ભાલપરા", "ps": "Veraval Rural PS", "keywords": ["bhalpara", "ભાલપરા"]},
            {"name_en": "Kajli", "name_gu": "કાજલી", "ps": "Veraval Rural PS", "keywords": ["kajli", "કાજલી", "kajli market yard"]}
        ]
    },
    "Somnath": {
        "gujarati_name": "સોમનાથ / પ્રભાસ પાટણ",
        "cluster": "Pilgrimage & Sacred Security Zone",
        "primary_ps": ["Prabhas Patan Police Station", "Somnath Temple Security Unit"],
        "villages": [
            {"name_en": "Prabhas Patan", "name_gu": "પ્રભાસ પાટણ", "ps": "Prabhas Patan PS", "keywords": ["prabhas patan", "પ્રભાસ પાટણ", "પ્રભાસપાટણ"]},
            {"name_en": "Somnath Temple Environs", "name_gu": "સોમનાથ મંદિર પરિસર", "ps": "Prabhas Patan PS", "keywords": ["somnath temple", "સોમનાથ મંદિર", "શ્રી સોમનાથ", "somnath trust", "ત્રિવેણી સંગમ", "triveni sangam"]},
            {"name_en": "Bhalpara Somnath", "name_gu": "ભાલપરા", "ps": "Prabhas Patan PS", "keywords": ["bhalpara", "ભાલપરા"]},
            {"name_en": "Dhamlej Road", "name_gu": "ધામળેજ રોડ", "ps": "Prabhas Patan PS", "keywords": ["dhamlej road", "ધામળેજ રોડ"]},
            {"name_en": "Goras", "name_gu": "ગોરસ", "ps": "Prabhas Patan PS", "keywords": ["goras", "ગોરસ"]},
            {"name_en": "Lati", "name_gu": "લાટી", "ps": "Prabhas Patan PS", "keywords": ["lati", "લાટી"]},
            {"name_en": "Moradiya", "name_gu": "મોરડીયા", "ps": "Prabhas Patan PS", "keywords": ["moradiya", "મોરડીયા"]}
        ]
    },
    "Una": {
        "gujarati_name": "ઉના",
        "cluster": "Interstate & Sensitive Border Hub",
        "primary_ps": ["Una Police Station", "Nava Bandar Marine Police Station"],
        "villages": [
            {"name_en": "Una Town", "name_gu": "ઉના શહેર", "ps": "Una PS", "keywords": ["una", "ઉના", "una town", "ઉના શહેર"]},
            {"name_en": "Delwada", "name_gu": "દેલવાડા", "ps": "Una PS", "keywords": ["delwada", "દેલવાડા", "delvada"]},
            {"name_en": "Nava Bandar", "name_gu": "નવાબંદર", "ps": "Nava Bandar Marine PS", "keywords": ["nava bandar", "નવાબંદર", "નવા બંદર", "navabandar"]},
            {"name_en": "Saiyad Rajpara", "name_gu": "સૈયદ રાજપરા", "ps": "Nava Bandar Marine PS", "keywords": ["saiyad rajpara", "સૈયદ રાજપરા", "rajpara bunder"]},
            {"name_en": "Tad", "name_gu": "તાડ", "ps": "Una PS", "keywords": ["tad village", "તાડ ગામ", r"\btad\b"]},
            {"name_en": "Samter", "name_gu": "સામતેર", "ps": "Una PS", "keywords": ["samter", "સામતેર"]},
            {"name_en": "Sanakhada", "name_gu": "સણખડા", "ps": "Una PS", "keywords": ["sanakhada", "સણખડા"]},
            {"name_en": "Gangda", "name_gu": "ગાંગડા", "ps": "Una PS", "keywords": ["gangda", "ગાંગડા"]},
            {"name_en": "Kandhi", "name_gu": "કાંઢી", "ps": "Una PS", "keywords": ["kandhi", "કાંઢી"]},
            {"name_en": "Vavarda", "name_gu": "વાવરડા", "ps": "Una PS", "keywords": ["vavarda", "વાવરડા"]},
            {"name_en": "Untwala", "name_gu": "ઉંટવાળા", "ps": "Una PS", "keywords": ["untwala", "ઉંટવાળા"]},
            {"name_en": "Diu Checkpost Border", "name_gu": "દીવ ચેકપોસ્ટ બોર્ડર", "ps": "Una PS", "keywords": ["diu border", "દીવ બોર્ડર", "tad checkpost", "દીવ ચેકપોસ્ટ"]}
        ]
    },
    "Kodinar": {
        "gujarati_name": "કોડીનાર",
        "cluster": "Coastal Industrial & Checkpost Corridor",
        "primary_ps": ["Kodinar Police Station", "Ghatwad Police Outpost"],
        "villages": [
            {"name_en": "Kodinar Town", "name_gu": "કોડીનાર શહેર", "ps": "Kodinar PS", "keywords": ["kodinar", "કોડીનાર"]},
            {"name_en": "Ghatwad", "name_gu": "ઘાંટવડ", "ps": "Kodinar PS", "keywords": ["ghatwad", "ઘાંટવડ", "ઘાટવડ", "ghatwad checkpost"]},
            {"name_en": "Mul Dwarka", "name_gu": "મુળ દ્વારકા", "ps": "Kodinar PS", "keywords": ["mul dwarka", "મુળ દ્વારકા", "મૂળ દ્વારકા", "muldwarka port"]},
            {"name_en": "Velva", "name_gu": "વેલવા", "ps": "Kodinar PS", "keywords": ["velva", "વેલવા"]},
            {"name_en": "Devli", "name_gu": "દેવળી", "ps": "Kodinar PS", "keywords": ["devli kodinar", "દેવળી"]},
            {"name_en": "Arnej", "name_gu": "અરણેજ", "ps": "Kodinar PS", "keywords": ["arnej kodinar", "અરણેજ"]},
            {"name_en": "Pedhavada", "name_gu": "પેઢાવડા", "ps": "Kodinar PS", "keywords": ["pedhavada", "પેઢાવડા"]},
            {"name_en": "Chhara", "name_gu": "છારા", "ps": "Kodinar PS", "keywords": ["chhara port", "છારા", "chhara lng"]},
            {"name_en": "Ronaj", "name_gu": "રોણાજ", "ps": "Kodinar PS", "keywords": ["ronaj", "રોણાજ"]},
            {"name_en": "Sindhaj", "name_gu": "સિંધાજ", "ps": "Kodinar PS", "keywords": ["sindhaj", "સિંધાજ"]}
        ]
    },
    "Talala": {
        "gujarati_name": "તાલાલા",
        "cluster": "Gir Forest Wildlife Fringe & Tourism",
        "primary_ps": ["Talala Police Station", "Sasan Gir Forest Police Outpost"],
        "villages": [
            {"name_en": "Talala Town", "name_gu": "તાલાલા શહેર", "ps": "Talala PS", "keywords": ["talala", "તાલાલા", "talala gir", "તાલાલા ગીર"]},
            {"name_en": "Sasan Gir Border", "name_gu": "સાસણ ગીર", "ps": "Talala PS", "keywords": ["sasan gir", "સાસણ ગીર", "સાસણ", "sasan"]},
            {"name_en": "Chitravad", "name_gu": "ચિત્રાવડ", "ps": "Talala PS", "keywords": ["chitravad", "ચિત્રાવડ"]},
            {"name_en": "Borvav", "name_gu": "બોરવાવ", "ps": "Talala PS", "keywords": ["borvav", "બોરવાવ"]},
            {"name_en": "Ankolwadi", "name_gu": "અંકોલવાડી", "ps": "Talala PS", "keywords": ["ankolwadi", "અંકોલવાડી"]},
            {"name_en": "Gundala", "name_gu": "ગુંદાલા", "ps": "Talala PS", "keywords": ["gundala talala", "ગુંદાલા"]},
            {"name_en": "Moruka", "name_gu": "મોરૂકા", "ps": "Talala PS", "keywords": ["moruka", "મોરૂકા"]},
            {"name_en": "Lushala", "name_gu": "લુશાળા", "ps": "Talala PS", "keywords": ["lushala", "લુશાળા"]},
            {"name_en": "Surva", "name_gu": "સુરવા", "ps": "Talala PS", "keywords": ["surva", "સુરવા"]},
            {"name_en": "Hiran Dam Environs", "name_gu": "હિરણ ડેમ", "ps": "Talala PS", "keywords": ["hiran dam", "હિરણ ડેમ", "કમલેશ્વર", "kamleshwar dam"]}
        ]
    },
    "Sutrapada": {
        "gujarati_name": "સુત્રાપાડા",
        "cluster": "Chemical Industrial & Coastal Belt",
        "primary_ps": ["Sutrapada Police Station", "Dhamlej Coastal Outpost"],
        "villages": [
            {"name_en": "Sutrapada Town", "name_gu": "સુત્રાપાડા", "ps": "Sutrapada PS", "keywords": ["sutrapada", "સુત્રાપાડા"]},
            {"name_en": "Dhamlej Port", "name_gu": "ધામળેજ બંદર", "ps": "Sutrapada PS", "keywords": ["dhamlej", "ધામળેજ", "dhamlej port", "ધામળેજ બંદર"]},
            {"name_en": "Prasnavada", "name_gu": "પ્રાસ્લી / પ્રશ્નાવડા", "ps": "Sutrapada PS", "keywords": ["prasnavada", "પ્રશ્નાવડા", "prasli", "પ્રાસ્લી"]},
            {"name_en": "Lakhapadar", "name_gu": "લાખાપાદર", "ps": "Sutrapada PS", "keywords": ["lakhapadar", "લાખાપાદર"]},
            {"name_en": "Moradiya Sutrapada", "name_gu": "મોરડીયા", "ps": "Sutrapada PS", "keywords": ["moradiya sutrapada", "મોરડીયા"]},
            {"name_en": "Vavdi", "name_gu": "વાવડી", "ps": "Sutrapada PS", "keywords": ["vavdi sutrapada", "વાવડી"]},
            {"name_en": "Lodva", "name_gu": "લોડવા", "ps": "Sutrapada PS", "keywords": ["lodva", "લોડવા"]}
        ]
    }
}


def detect_gir_somnath_geo(text: str) -> Optional[Dict[str, Any]]:
    """
    Forensically detects if a social media post, headline, or caption references
    any Taluka, village, port, or police jurisdiction in Gir Somnath District.
    Prioritizes specific villages/hamlets over general taluka mentions.
    """
    if not text:
        return None

    text_lower = text.lower()
    matches = []

    # Priority 1: Check village and landing point exact terms (collect all matches)
    for taluka_name, taluka_data in GIR_SOMNATH_JURISDICTIONS.items():
        for village in taluka_data["villages"]:
            for kw in village["keywords"]:
                pattern = rf"\b{re.escape(kw.lower())}\b" if kw.isascii() and len(kw) <= 5 else re.escape(kw.lower())
                m = re.search(pattern, text_lower if kw.isascii() else text)
                if m:
                    # Specificity score: non-generic town keywords get higher priority
                    is_generic_town = kw in ["una", "ઉના", "veraval", "વેરાવળ", "kodinar", "કોડીનાર", "talala", "તાલાલા", "sutrapada", "સુત્રાપાડા"]
                    specificity = len(kw) if not is_generic_town else 1
                    matches.append((
                        specificity,
                        {
                            "is_gir_somnath": True,
                            "taluka": taluka_name,
                            "village": village["name_en"],
                            "village_gu": village["name_gu"],
                            "police_station": village["ps"],
                            "cluster": taluka_data["cluster"],
                            "matched_term": kw,
                            "display_badge": f"{taluka_name} ({village['name_en']})"
                        }
                    ))

    if matches:
        # Return match with highest specificity (e.g. Delwada over Una)
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]

    # Priority 2: Check general taluka names
    general_talukas = {
        "Gir Somnath": ["gir somnath", "girsomnath", "ગીર સોમનાથ", "ગીરસોમનાથ", "ગીર-સોમનાથ"],
        "Veraval": ["veraval", "વેરાવળ"],
        "Somnath": ["somnath", "સોમનાથ"],
        "Una": [r"\buna\b", "ઉના"],
        "Kodinar": ["kodinar", "કોડીનાર"],
        "Talala": ["talala", "તાલાલા"],
        "Sutrapada": ["sutrapada", "સુત્રાપાડા"]
    }

    for taluka_name, terms in general_talukas.items():
        for t in terms:
            pattern = rf"\b{re.escape(t.lower())}\b" if t.isascii() and len(t) <= 5 else re.escape(t.lower())
            if re.search(pattern, text_lower if t.isascii() else text):
                target_t = "Veraval" if taluka_name == "Gir Somnath" else taluka_name
                t_info = GIR_SOMNATH_JURISDICTIONS.get(target_t, GIR_SOMNATH_JURISDICTIONS["Veraval"])
                return {
                    "is_gir_somnath": True,
                    "taluka": taluka_name,
                    "village": f"{taluka_name} Taluka",
                    "village_gu": t_info["gujarati_name"],
                    "police_station": t_info["primary_ps"][0],
                    "cluster": t_info["cluster"],
                    "matched_term": t,
                    "display_badge": f"Gir Somnath ({taluka_name})"
                }

    return None
