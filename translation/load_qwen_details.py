import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ── CONFIGURATION ─────────────────────────────────────────────────────
SOURCE_FOLDER = "en"  # Root folder to start searching from

TARGET_FOLDER = "th"  # Where translated files will go

TRANSLATABLE_META_KEYS = {
    "description", "keywords", "og:title", "og:description",
    "twitter:title", "twitter:description"
}

TARGET_LANG = "Thai"  # For translation instructions
TARGET_LANG_CODE = "th"  # For HTML lang attribute
BATCH_SIZE = 8

# ── LOAD TRANSLATION MODEL ────────────────────────────────────────────
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

print("🔄 Loading translation model...")
print(f"   Model: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    low_cpu_mem_usage=True
)
print("✅ Model loaded successfully!\n")

# ── SYSTEM PROMPT FOR TRANSLATION ─────────────────────────────────────
SYSTEM_PROMPT = f"""You are a professional web content translator.
Translate the provided list into {TARGET_LANG}.
- Maintain the exact numbering format [number].
- Keep proper names (brands, city names) as is.
- Translate Meta descriptions to be natural and SEO-friendly.
- Return ONLY the translated list. No intro text or explanations."""

# ── TRANSLATION FUNCTION ───────────────────────────────────────────────
def translate_texts(texts: list[str]) -> list[str]:
    """Translate a list of text fragments."""
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
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": numbered_content}
            ]
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.1,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )

            generated_text = tokenizer.decode(
                outputs[0][len(inputs["input_ids"][0]):],
                skip_special_tokens=True
            ).strip()

            # Parse translations using regex
            pattern = re.compile(r"^\[?(\d+)\]?[\s.:]*(.*)", re.MULTILINE)
            for match in pattern.finditer(generated_text):
                try:
                    num = int(match.group(1)) - 1
                    trans = match.group(2).strip()
                    if 0 <= num < len(batch):
                        global_idx = start + num
                        if global_idx < len(non_empty_texts):
                            results[non_empty_idx + global_idx] = trans
                except (ValueError, IndexError):
                    continue

        except Exception as e:
            print(f"   ⚠️ Translation error: {e}")

        non_empty_idx += len(batch)

    return results

# ── RECURSIVE FUNCTION TO TRAVERSE FOLDERS AND TRANSLATE ───────────────
def traverse_and_translate(current_path: Path, target_base: Path, source_base: Path, 
                          counters: list, indent: str = ""):
    """
    Recursively traverse folders and translate HTML files.
    
    Args:
        current_path: Current directory being traversed
        target_base: Base directory for translated files
        source_base: Base source directory
        counters: List to track [total, success, failed]
        indent: Indentation for pretty printing
    """
    try:
        # Get all items in the current folder
        items = sorted(current_path.iterdir())
        
        # Separate folders and files
        folders = []
        html_files = []
        
        for item in items:
            if item.is_dir():
                folders.append(item)
            elif item.is_file() and item.suffix.lower() in ['.html', '.htm']:
                html_files.append(item)
        
        # Print current folder
        rel_path = current_path.relative_to(source_base) if current_path != source_base else Path("")
        if rel_path == Path(""):
            print(f"\n{indent}📁 Root folder: {current_path.name}")
        else:
            print(f"\n{indent}📁 Entering folder: {rel_path}")
        
        # Translate HTML files in current folder
        if html_files:
            print(f"{indent}   Found {len(html_files)} HTML file(s) in this folder:")
            for html_file in html_files:
                counters[0] += 1  # total++
                success = translate_html_file(html_file, target_base, source_base, indent + "      ")
                if success:
                    counters[1] += 1  # success++
                    print(f"{indent}      ✅ Translated")
                else:
                    counters[2] += 1  # failed++
                    print(f"{indent}      ❌ Failed")
        else:
            print(f"{indent}   No HTML files in this folder")
        
        # Recursively traverse subfolders
        for folder in folders:
            traverse_and_translate(folder, target_base, source_base, counters, indent + "   ")
            
    except PermissionError:
        print(f"{indent}❌ Permission denied: {current_path}")
    except Exception as e:
        print(f"{indent}❌ Error accessing {current_path}: {e}")

# ── HTML TRANSLATION FUNCTION ─────────────────────────────────────────
def translate_html_file(html_file_path: Path, target_base: Path, source_base: Path, indent: str = "") -> bool:
    """
    Translate a single HTML file and save it to the target location.
    """
    try:
        # Calculate relative path to maintain folder structure
        relative_path = html_file_path.relative_to(source_base)
        target_path = target_base / relative_path
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"{indent}📄 Translating: {relative_path}")
        
        # Read HTML file
        with open(html_file_path, "r", encoding="utf-8-sig", errors="replace") as f:
            soup = BeautifulSoup(f, "html.parser")

        # 1. Update language attributes
        if soup.html:
            soup.html["lang"] = TARGET_LANG_CODE
        
        # 2. Update Open Graph locale
        for meta in soup.find_all("meta", attrs={"property": "og:locale"}):
            meta["content"] = "zh_CN"
        for meta in soup.find_all("meta", attrs={"name": "locale"}):
            meta["content"] = "zh_CN"

        # 3. Translate title
        if soup.title and soup.title.string:
            original = soup.title.string.strip()
            if original:
                translated = translate_texts([original])[0]
                soup.title.string = translated

        # 4. Translate meta tags
        meta_items = []
        for meta in soup.find_all("meta"):
            key = (meta.get("name") or meta.get("property") or "").lower()
            if key in TRANSLATABLE_META_KEYS:
                val = meta.get("content", "").strip()
                if val:
                    meta_items.append((meta, val))

        if meta_items:
            originals = [item[1] for item in meta_items]
            translated = translate_texts(originals)
            for (meta_tag, _), new_val in zip(meta_items, translated):
                meta_tag["content"] = new_val

        # 5. Translate body text
        text_nodes = []
        skip_tags = {"script", "style", "title", "noscript", "meta", "code", "pre"}
        
        for node in soup.find_all(string=True):
            if isinstance(node, NavigableString) and node.parent.name not in skip_tags:
                cleaned = node.strip()
                # Only translate text that contains letters and is meaningful
                if cleaned and len(cleaned) > 1 and re.search(r'[a-zA-Z]', cleaned):
                    text_nodes.append(node)

        if text_nodes:
            for start in range(0, len(text_nodes), BATCH_SIZE):
                batch_nodes = text_nodes[start : start + BATCH_SIZE]
                originals = [n.strip() for n in batch_nodes]
                translations = translate_texts(originals)
                
                for node, translated in zip(batch_nodes, translations):
                    if translated and translated != node.strip():
                        node.replace_with(translated)

        # Save translated file
        target_path.write_text(str(soup), encoding="utf-8")
        
        return True
        
    except Exception as e:
        print(f"{indent}❌ Error translating {html_file_path.name}: {e}")
        return False

# ── MAIN FUNCTION ─────────────────────────────────────────────────────
def main():
    """Main function to start recursive traversal and translation."""
    
    print("="*60)
    print("🌐 RECURSIVE HTML FILE TRANSLATOR")
    print("="*60)
    print("This script will:")
    print("  • Go through every folder recursively")
    print("  • If it finds an HTML file → translate it")
    print("  • If it finds a subfolder → go inside and look for more HTML files")
    print("="*60)
    
    # Set up paths
    source_dir = Path(SOURCE_FOLDER)
    target_dir = Path(TARGET_FOLDER)
    
    # Check if source directory exists
    if not source_dir.exists():
        print(f"\n❌ Source folder not found: {source_dir}")
        print(f"Current directory: {Path.cwd()}")
        
        # Try to find the folder
        print("\n🔍 Searching for 'all_cities_data' folder...")
        found = False
        for root, dirs, files in os.walk(Path.cwd()):
            if "all_cities_data" in dirs:
                found_path = Path(root) / "all_cities_data"
                print(f"✅ Found at: {found_path}")
                response = input("Use this path? (yes/no): ").strip().lower()
                if response in ['yes', 'y']:
                    source_dir = found_path
                    found = True
                    break
        
        if not found:
            print("❌ Could not find all_cities_data folder.")
            return
    
    print(f"\n📍 Source directory: {source_dir}")
    print(f"📍 Target directory: {target_dir}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will recursively traverse all folders and translate every HTML file found.")
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Translation cancelled.")
        return
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Start recursive traversal and translation
    print(f"\n🚀 Starting recursive folder traversal...")
    print("="*60)
    
    # Initialize counters [total, success, failed]
    counters = [0, 0, 0]
    
    # Start traversal
    traverse_and_translate(source_dir, target_dir, source_dir, counters)
    
    # Print summary
    print("\n" + "="*60)
    print("✅ TRANSLATION COMPLETE!")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   Total HTML files found: {counters[0]}")
    print(f"   Successfully translated: {counters[1]}")
    print(f"   Failed: {counters[2]}")
    print(f"\n📍 Source: {source_dir}")
    print(f"📍 Target: {target_dir.absolute()}")
    print("="*60)

if __name__ == "__main__":
    main()