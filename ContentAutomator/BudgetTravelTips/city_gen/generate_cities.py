import os
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

INPUT_FILE = "my_own.json"
OUTPUT_ROOT = Path("CheapCity_generated_city_jsons")
MODEL = "gemini-2.5-flash"

START_ID = 2411
END_ID = 2412

NUM_CHILD_PER_SUBTYPE = 4
NUM_INSTAGRAM_PER_SUBTYPE = 4
NUM_POWER_PER_SUBTYPE = 4
NUM_NEW_ATTRACTIONS = 10

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")
genai.configure(api_key=API_KEY)

def run_model(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)
    if response.candidates and response.candidates[0].content.parts:
        text = response.candidates[0].content.parts[0].text.strip()
        return text.strip("```json").strip("```").strip()
    return ""

def run_model_json(prompt: str):
    text = run_model(prompt)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = text.strip().strip("```json").strip("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {}

def clean_duplicates(items, key="name"):
    seen = set()
    unique = []
    for item in items:
        name = item.get(key)
        if name and name not in seen:
            unique.append(item)
            seen.add(name)
    return unique

def save_failed_part(city_id, city_name, part_name, failed_parts_log, failed_log_file):
    failed_parts_log.setdefault(city_id, {"city_name": city_name, "failed_parts": []})
    if part_name not in failed_parts_log[city_id]["failed_parts"]:
        failed_parts_log[city_id]["failed_parts"].append(part_name)
    with open(failed_log_file, "w", encoding="utf-8") as f:
        json.dump(failed_parts_log, f, ensure_ascii=False, indent=2)

def run_part_with_retry(prompt, part_name, city_id, city_name, failed_parts_log, failed_log_file):
    result = run_model_json(prompt)
    if not result:
        time.sleep(random.uniform(1, 2))
        result = run_model_json(prompt)
    if not result:
        save_failed_part(city_id, city_name, part_name, failed_parts_log, failed_log_file)
    return result

def pick_random_subtypes(full_list, n=10):
    return random.sample(full_list, min(n, len(full_list)))

CHILDREN_SUBTYPES = [
    "Theme Parks for Kids","Amusement Rides","Zoos & Petting Zoos","Aquariums",
    "Children’s Museums","Science Centers","Playgrounds & Adventure Parks","Indoor Play Centers",
    "Water Parks for Kids","Circuses & Puppet Theaters","Dinosaur Parks","Fairy Tale Parks",
    "Lego Worlds & Construction Parks","Farm Attractions","Magic & Illusion Shows","Cartoon Meet & Greets",
    "Adventure & Quest Games","Planetariums for Kids","Storytelling Parks","Mini Sports Arenas"
]

INSTAGRAM_SUBTYPES = [
    "Street Art & Murals","Rooftop Views","Iconic Landmarks","Colorful Neighborhoods",
    "Nature Backdrops","Beaches & Coastal Views","Bridges & Overlooks","Hidden Alleys & Courtyards",
    "Historic Architecture","Modern Architecture","Flower Fields & Gardens","Food & Drink Spots",
    "Markets & Bazaars","Desert & Sand Dunes","Unique Hotels & Stays","Infinity Pools",
    "Cultural Installations","Festivals & Events","Iconic Staircases & Pathways","Unusual Natural Wonders"
]

PLACES_OF_POWER_SUBTYPES = [
    "Ancient Temples","Pyramids","Sacred Mountains","Megalithic Sites","Pilgrimage Routes",
    "Monasteries & Hermitages","Holy Springs & Wells","Ancient Cities","Desert Power Sites",
    "Caves & Sanctuaries","Volcanic Zones","Celestial Alignment Sites","Sacred Forests",
    "Monoliths & Rock Formations","Labyrinths","Battlefields of Destiny","Relic Shrines & Tombs",
    "Oracle Sites","Crossroads","Modern Energy Places"
]

PART1_COMBINED_PROMPT = """
You are a professional travel guide AI. Generate a single valid JSON object for the city {city_name}, {country} with the following structure:

{{
  "id": "{cid}",
  "name": "{city_name}",
  "country": "{country}",
  "description": "250–350 words city travel guide covering key highlights, culture, attractions, and travel tips concisely.",
  "themes": ["3–5 thematic keywords"],
  "body_attributes": {{
    "climate": "Short description",
    "best_time_to_visit": "e.g., months or seasons",
    "population": "Number as string",
    "area": "City area in sq km or mi",
    "transport_summary": "Concise description",
    "safety_level": "Low, medium, high",
    "geographical_features": "Brief description"
  }},
  "travel_tips": ["3–4 practical travel tips"],
  "budget_tips": ["3–4 budget tips"],
  "seo": {{
    "seo_title": "Concise SEO title",
    "seo_description": "Short meta description, max 160 chars",
    "keywords": ["3–5 keywords"]
  }},
  "meta": {{
    "continent": "Continent",
    "currency": "Currency",
    "language": "Primary language(s)",
    "time_zone": "Time zone",
    "popular_airlines": ["3–5 main airlines"]
  }},
  "title": "Catchy human-readable travel guide title",
  "images": ["1–2 real URLs from Unsplash/Pexels/Wikimedia"],
  "coordinates": [ {{latitude}}, {{longitude}} ]
}}

RULES:
- Return only JSON, no markdown or explanations.
- All fields must be complete and non-empty.
"""

PROMPT_CHILDREN = """
You are a JSON generator. For {city}, generate {count} unique children's attractions for all subtypes:

{children_subtypes}

Each item must follow this schema:
{{
  "id": "ShortUniqueID",
  "name": "Clear catchy name",
  "short_description": "1–2 sentences",
  "subtype": "Subtype name",
  "address": "Realistic address in {city}",
  "opening_hours": "HH:MM-HH:MM",
  "price_level": "free | cheap | moderate | expensive",
  "images": "1 real URLs from Unsplash/Pexels/Wikimedia",
  "tags": ["2–3 relevant tags"]
}}

Return a single valid JSON object where keys are subtypes.
"""

PROMPT_INSTAGRAM = """
You are a JSON generator. For {city}, generate {count} Instagrammable attractions for all subtypes:

{instagram_subtypes}

Each item must follow this schema:
{{
  "id": "ShortUniqueID",
  "name": "Catchy descriptive name",
  "short_description": "1–2 engaging sentences",
  "subtype": "Subtype name",
  "location_hint": "Neighborhood or landmark",
  "best_time": "Morning / Afternoon / Sunset / Night",
  "images": "1 real URLs from Unsplash/Pexels/Wikimedia",
  "tags": ["2–3 relevant tags"]
}}

Return a single valid JSON object where keys are subtypes.
"""

PROMPT_PLACES_OF_POWER = """
You are a JSON generator. For {city}, generate {count} unique spiritual/cultural attractions for all subtypes:

{power_subtypes}

Each item must follow this schema:
{{
  "id": "ShortUniqueID",
  "name": "Clear reverent name",
  "short_description": "1–2 sentences about spiritual/cultural significance",
  "subtype": "Subtype name",
  "address": "Realistic address in {city}",
  "visiting_hours": "HH:MM-HH:MM",
  "entry_fee": "free | donation | fixed amount",
  "images": "1 real URLs from Unsplash/Pexels/Wikimedia",
  "tags": ["2–3 relevant tags"]
}}

Return a single valid JSON object where keys are subtypes.
"""

PROMPT_NEW_ATTRACTIONS = """
You are a JSON generator. Generate {count} new attractions in {city} (opened in last 5 years).

Return an array:
{{
  "id": "ShortUniqueID",
  "name": "Catchy name",
  "short_description": "1–2 sentences why it's exciting",
  "address": "Plausible address in {city}",
  "opening_hours": "09:00-18:00 or 24/7",
  "price_level": "free | cheap | moderate | expensive",
  "images": "1 real URLs from Unsplash/Pexels/Wikimedia",
  "tags": ["2–3 relevant tags"]
}}
"""

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        cities = {str(item.get("id") or idx): item for idx, item in enumerate(raw, start=1)}
    else:
        cities = {str(k): v for k, v in raw.items()}

    selected = {
        cid: info for cid, info in cities.items()
        if cid.isdigit() and START_ID <= int(cid) <= END_ID
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    FAILED_LOG_FILE = OUTPUT_ROOT / "failed_parts_log.json"
    if FAILED_LOG_FILE.exists():
        with open(FAILED_LOG_FILE, "r", encoding="utf-8") as f:
            failed_parts_log = json.load(f)
    else:
        failed_parts_log = {}

    for cid, info in selected.items():
        city_name = info.get("Name") or info.get("name") or info.get("city") or "Unknown"
        country = info.get("country_name") or info.get("country") or "Unknown Country"
        lat = float(info.get("latitude") or info.get("lat") or 0.0)
        lon = float(info.get("longitude") or info.get("lon") or 0.0)

        out_dir = OUTPUT_ROOT / f"{cid}_{city_name.replace('/', '_')}"
        out_dir.mkdir(parents=True, exist_ok=True)

        part1_file = out_dir / f"{cid}_part1_description.json"
        if not part1_file.exists():
            p1_prompt = PART1_COMBINED_PROMPT.format(city_name=city_name, country=country, cid=cid)
            data = run_part_with_retry(p1_prompt, "Part1_Description", cid, city_name, failed_parts_log, FAILED_LOG_FILE)
            if data:
                data["coordinates"] = [lat, lon]
                with open(part1_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        part2_file = out_dir / f"{cid}_part2_children.json"
        if not part2_file.exists():
            random_children_subtypes = pick_random_subtypes(CHILDREN_SUBTYPES, n=10)
            children_prompt = PROMPT_CHILDREN.format(
                city=city_name,
                count=NUM_CHILD_PER_SUBTYPE,
                children_subtypes="\n".join(f"- {s}" for s in random_children_subtypes)
            )
            children_data = run_part_with_retry(children_prompt, "Part2_Children", cid, city_name, failed_parts_log, FAILED_LOG_FILE)
            if children_data:
                all_children = []
                for subtype, items in children_data.items():
                    for item in items:
                        item["subtype"] = subtype
                    all_children.extend(items)
                all_children = clean_duplicates(all_children)
                with open(part2_file, "w", encoding="utf-8") as f:
                    json.dump({"meta":{"type":"ChildrenAttractions","city":city_name,"city_id":cid},"items":all_children}, f, ensure_ascii=False, indent=2)

        part3_file = out_dir / f"{cid}_part3_instagram.json"
        if not part3_file.exists():
            random_instagram_subtypes = pick_random_subtypes(INSTAGRAM_SUBTYPES, n=10)
            instagram_prompt = PROMPT_INSTAGRAM.format(
                city=city_name,
                count=NUM_INSTAGRAM_PER_SUBTYPE,
                instagram_subtypes="\n".join(f"- {s}" for s in random_instagram_subtypes)
            )
            instagram_data = run_part_with_retry(instagram_prompt, "Part3_Instagram", cid, city_name, failed_parts_log, FAILED_LOG_FILE)
            if instagram_data:
                all_instagram = []
                for subtype, items in instagram_data.items():
                    for item in items:
                        item["subtype"] = subtype
                    all_instagram.extend(items)
                all_instagram = clean_duplicates(all_instagram)
                with open(part3_file, "w", encoding="utf-8") as f:
                    json.dump({"meta":{"type":"InstagramAttractions","city":city_name,"city_id":cid},"items":all_instagram}, f, ensure_ascii=False, indent=2)

        part4_file = out_dir / f"{cid}_part4_places_of_power.json"
        if not part4_file.exists():
            random_power_subtypes = pick_random_subtypes(PLACES_OF_POWER_SUBTYPES, n=10)
            power_prompt = PROMPT_PLACES_OF_POWER.format(
                city=city_name,
                count=NUM_POWER_PER_SUBTYPE,
                power_subtypes="\n".join(f"- {s}" for s in random_power_subtypes)
            )
            power_data = run_part_with_retry(power_prompt, "Part4_PlacesOfPower", cid, city_name, failed_parts_log, FAILED_LOG_FILE)
            if power_data:
                all_power = []
                for subtype, items in power_data.items():
                    for item in items:
                        item["subtype"] = subtype
                    all_power.extend(items)
                all_power = clean_duplicates(all_power)
                with open(part4_file, "w", encoding="utf-8") as f:
                    json.dump({"meta":{"type":"PlacesOfPower","city":city_name,"city_id":cid},"items":all_power}, f, ensure_ascii=False, indent=2)

        part5_file = out_dir / f"{cid}_part5_new_attractions.json"
        if not part5_file.exists():
            new_prompt = PROMPT_NEW_ATTRACTIONS.format(city=city_name, count=NUM_NEW_ATTRACTIONS)
            new_data = run_part_with_retry(new_prompt, "Part5_NewAttractions", cid, city_name, failed_parts_log, FAILED_LOG_FILE)
            if new_data:
                if not isinstance(new_data, list):
                    new_data = []
                new_data = clean_duplicates(new_data)
                with open(part5_file, "w", encoding="utf-8") as f:
                    json.dump({"meta":{"type":"NewAttractions","city":city_name,"city_id":cid},"items":new_data}, f, ensure_ascii=False, indent=2)

        time.sleep(random.uniform(0.8, 1.5))

if __name__ == "__main__":
    main()
