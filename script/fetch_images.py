"""
StatFacts image generator (Google Imagen).
- Reads `image_prompt` from insight markdown (`*_en.md`).
- Saves to `app/static/images/{id}.jpg` (uses frontmatter `id`).
- Run: python script/fetch_images.py  (requires GEMINI_API_KEY)
"""
import os
import sys
import frontmatter
from dotenv import load_dotenv

load_dotenv()

from md_clean import clean_md, load_post
from resolve_secrets import ensure_gemini_api_key

ensure_gemini_api_key()
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
IMAGES_DIR  = os.path.join(BASE_DIR, 'app', 'static', 'images')


def generate_image(safe_name: str, prompt: str, *, force: bool = False) -> bool:
    out_path = os.path.join(IMAGES_DIR, f"{safe_name}.jpg")
    if os.path.exists(out_path) and not force:
        print(f"⏭️  Skip (already exists): {safe_name}.jpg")
        return True

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
        enhanced = (
            f"{prompt} Editorial infographic illustration, clean modern style, "
            "high quality, no text, no watermark, no logos."
        )
        response = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=enhanced,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='16:9',
                output_mime_type='image/jpeg',
                person_generation='allow_adult',
            )
        )
        if not response.generated_images:
            print(f"⚠️  No image returned: {safe_name}")
            return False
        img_bytes = response.generated_images[0].image.image_bytes
        os.makedirs(IMAGES_DIR, exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(img_bytes)
        print(f"✅ Image generated: {safe_name}.jpg ({len(img_bytes) // 1024}KB)")
        return True
    except Exception as e:
        print(f"❌ Image generation failed ({safe_name}): {e}")
        return False


def generate_image_for_markdown(fpath: str, *, force: bool = False) -> bool:
    """Generate thumbnail from a single insight markdown file."""
    post = load_post(open(fpath, encoding='utf-8').read())
    safe_name = str(post.get('id', os.path.basename(fpath).replace('_en.md', '')))
    prompt = str(post.get('image_prompt', ''))
    if not prompt or len(prompt) < 10:
        print(f"⚠️  image_prompt is missing: {fpath}")
        return False
    return generate_image(safe_name, prompt, force=force)


def run(*, only_missing: bool = True, force: bool = False) -> int:
    if not ensure_gemini_api_key():
        print("❌ GEMINI_API_KEY is missing — set env, .env, or GCP Secret Manager (GEMINI_API_KEY)")
        return 1
    global API_KEY
    API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

    processed = set()
    failures: list[str] = []
    for filename in sorted(os.listdir(CONTENT_DIR)):
        if not filename.endswith('_en.md'):
            continue
        fpath = os.path.join(CONTENT_DIR, filename)
        try:
            post = load_post(open(fpath, encoding='utf-8').read())
            safe_name = str(post.get('id', filename.replace('_en.md', '')))
            if safe_name in processed:
                continue
            prompt = str(post.get('image_prompt', ''))
            img_path = os.path.join(IMAGES_DIR, f"{safe_name}.jpg")
            if not prompt or len(prompt) < 10:
                if only_missing and os.path.exists(img_path):
                    print(f"⏭️  Skip (image exists, no prompt): {filename}")
                    processed.add(safe_name)
                    continue
                print(f"❌ image_prompt is missing: {filename}")
                failures.append(filename)
                continue
            if only_missing and os.path.exists(img_path):
                print(f"⏭️  Skip (already exists): {safe_name}.jpg")
                processed.add(safe_name)
                continue
            if not generate_image(safe_name, prompt, force=force):
                failures.append(filename)
            processed.add(safe_name)
        except Exception as e:
            print(f"❌ Failed to read file ({filename}): {e}")
            failures.append(filename)

    if failures:
        print(f"❌ Image step failed for {len(failures)} file(s)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
