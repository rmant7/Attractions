import requests
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "Qwen/Qwen2.5-1.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)


city="Paris"
def get_wikipedia_extract(city: str, lang: str = "en", sentences: int = 5) -> str:
    url = f"https://{lang}.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "exsentences": sentences,
        "redirects": 1,
        "titles": city
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MyWikipediaBot/1.0; +http://example.com/contact)"
        # You can put your real email or GitHub/repo in the User-Agent – Wikipedia likes that
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()

        data = r.json()
        pages = data["query"]["pages"]

        if "-1" in pages:
            page = pages["-1"]
            if "missing" in page:
                return f"No page found for '{city}'"
            if "invalid" in page:
                return f"Invalid title '{city}'"

        # Take first available page
        page = next(iter(pages.values()))

        if "extract" not in page or not page["extract"]:
            return "No extract available"

        return page["extract"].strip()

    except requests.RequestException as e:
        return f"Error: {str(e)}"


# Test
wiki_text= get_wikipedia_extract(city, sentences=20)



messages = [
    {"role": "system", "content": """You are a talented travel copywriter who creates irresistible, emotional and vivid descriptions for tourism websites.
Your style is warm, exciting, sensory-rich and welcoming.
You highlight atmosphere, views, smells, tastes, emotions, hidden gems.
Use 2nd person ("you"), vivid sensory details, short rhythmic sentences.
End with an invitation to visit.
Output ONLY the rewritten description — no extra text."""},
    {"role": "user", "content": f"Rewrite this city introduction to make it highly attractive for tourists:\n\n{wiki_text}"}
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

inputs = tokenizer([text], return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    max_new_tokens=380,
    temperature=0.7,
    top_p=0.9,
    do_sample=True
)

print(tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True).strip())