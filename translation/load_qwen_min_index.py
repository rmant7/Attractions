import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ── CONFIG ─────────────────────────────────────────────────────────────
SOURCE_DIR = "all_cities_data"
TARGET_DIR = "it/all_cities_data"

TRANSLATABLE_META_KEYS = {
    "description", "keywords", "og:title", "og:description",
    "twitter:title", "twitter:description"
}

TARGET_LANG = "Italian"
BATCH_SIZE = 8  # Keep small for speed; can increase to 16+ on GPU

# ── LOCAL MODEL SETUP (loaded once) ────────────────────────────────────
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

print(f"Loading model: {MODEL_ID} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",          # auto = GPU if available, else CPU
    low_cpu_mem_usage=True
)
print("Model loaded successfully!")

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are a professional web content translator.
Translate the provided list into {TARGET_LANG}.
- Maintain the exact numbering format [number].
- Keep proper names (brands, city names like 'Paris', 'London') as is.
- Translate Meta descriptions to be natural and SEO-friendly.
- Return ONLY the translated list. No intro text.
- match the html lang to the {TARGET_LANG}"""

# ── TRANSLATION ENGINE (local inference) ───────────────────────────────
def translate_texts(texts: list[str]) -> list[str]:
    """
    Translate a list of text fragments using local Qwen2.5-1.5B-Instruct.
    Returns translated texts in the same order, falling back to originals on failure.
    """
    if not texts:
        return []

    non_empty_texts = [t.strip() for t in texts if t and t.strip()]
    if not non_empty_texts:
        return texts[:]

    results = texts[:]
    non_empty_idx = 0

    for start in range(0, len(non_empty_texts), BATCH_SIZE):
        batch = non_empty_texts[start : start + BATCH_SIZE]
        numbered_content = "\n".join(f"[{i+1}] {t}" for i, t in enumerate(batch))

        try:
            # Build chat prompt
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": numbered_content}
            ]
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize and generate
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=512,     # enough for batch of 8
                    temperature=0.1,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )

            generated_text = tokenizer.decode(
                outputs[0][len(inputs["input_ids"][0]):],
                skip_special_tokens=True
            ).strip()

            # Parse the generated text (same regex logic)
            translated_map = _parse_generated_text(generated_text, len(batch))

            # Map back to results
            for local_idx, translated in translated_map.items():
                global_idx = start + local_idx
                if global_idx < len(non_empty_texts):
                    results[non_empty_idx + global_idx] = translated

        except Exception as e:
            print(f"   ⚠️ Generation error: {e} → falling back to originals for this batch")
            # Keep originals for this batch

        non_empty_idx += len(batch)

    return results


def _parse_generated_text(text: str, expected_count: int) -> dict[int, str]:
    """Parse numbered translations from raw model output (same regex as before)."""
    translated_map = {}
    pattern = re.compile(r"^\[?(\d+)\]?[\s.:]*(.*)", re.MULTILINE)

    for match in pattern.finditer(text):
        try:
            num = int(match.group(1)) - 1
            trans = match.group(2).strip()
            if 0 <= num < expected_count:
                translated_map[num] = trans
        except (ValueError, IndexError):
            continue

    if len(translated_map) < expected_count * 0.7:
        print(f"   ⚠️ Incomplete parse: got {len(translated_map)} / {expected_count}")

    return translated_map


# ── HELPERS (unchanged) ────────────────────────────────────────────────
def update_document_language(soup):
    if soup.html:
        soup.html["lang"] = "fr"


def update_og_locale(soup):
    for meta in soup.find_all("meta", attrs={"property": "og:locale"}):
        meta["content"] = "fr_FR"


def translate_title(soup):
    if soup.title and soup.title.string:
        original = soup.title.string.strip()
        if original:
            soup.title.string = translate_texts([original])[0]


def collect_and_translate_meta(soup):
    meta_items = []
    for meta in soup.find_all("meta"):
        key = (meta.get("name") or meta.get("property") or "").lower()
        if key in TRANSLATABLE_META_KEYS:
            val = meta.get("content", "").strip()
            if val:
                meta_items.append((meta, val))

    if not meta_items:
        return

    originals = [item[1] for item in meta_items]
    translated = translate_texts(originals)

    for (meta_tag, _), new_val in zip(meta_items, translated):
        meta_tag["content"] = new_val


def collect_translatable_text_nodes(soup) -> list[NavigableString]:
    nodes = []
    skip_tags = {"script", "style", "title", "noscript"}

    for node in soup.find_all(string=True):
        if isinstance(node, NavigableString) and node.parent.name not in skip_tags:
            cleaned = node.strip()
            if cleaned and re.search(r'[a-zA-Z]', cleaned):
                nodes.append(node)

    return nodes


def translate_text_nodes_in_batches(nodes: list[NavigableString]):
    for start in range(0, len(nodes), BATCH_SIZE):
        batch_nodes = nodes[start : start + BATCH_SIZE]
        originals = [n.strip() for n in batch_nodes]
        translations = translate_texts(originals)

        for node, translated in zip(batch_nodes, translations):
            node.replace_with(translated)


# ── MAIN PROCESSING FUNCTION (unchanged) ──────────────────────────────
def process_html_file(filepath: Path):
    rel_path = filepath.relative_to(SOURCE_DIR)
    target_path = Path(TARGET_DIR) / rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        soup = BeautifulSoup(f, "html.parser")

    print(f"Processing {rel_path}")

    # Step 1 – Document & fixed attributes
    update_document_language(soup)
    update_og_locale(soup)

    # Step 2 – Head content
    translate_title(soup)
    collect_and_translate_meta(soup)

    # Step 3 – Body text
    text_nodes = collect_translatable_text_nodes(soup)
    print(f"  → Found {len(text_nodes)} translatable text nodes")

    if text_nodes:
        translate_text_nodes_in_batches(text_nodes)

    # Save result
    target_path.write_text(str(soup), encoding="utf-8")
    print(f"  → Saved to {target_path}")


# ── EXECUTION ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    html_files = list(Path(SOURCE_DIR).rglob("*.html"))
    print(f"Found {len(html_files)} HTML files\n")

    for html_file in html_files:
        process_html_file(html_file)

    print("\n✅ All files processed.")