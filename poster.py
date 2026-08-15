# -*- coding: utf-8 -*-
"""
Super Dumb Heroes Bot v3.0 (The justmeme.wtf Upgrade)
- Primary AI: justmeme.wtf (/ai-generate) for authentic meme templates & text
- Fallback AI: OpenRouter (Text) + Hugging Face FLUX (Image)
- Visuals: Smart blurred-background padding for horizontal templates to fit 9:16 Reels
- Audio: Hardcoded comedic pauses between meme top_text and bottom_text
"""
BOT_VERSION = "v3.0"

import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'Resampling', PIL.Image).LANCZOS

import os
import sys
import time
import json
import random
import requests
import asyncio
import textwrap
from datetime import datetime
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(line_buffering=True)

# ============================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================
OPENROUTER_API_KEY     = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
HF_TOKEN               = os.environ.get("HF_TOKEN", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID      = os.environ.get("INSTAGRAM_USER_ID", "")
GITHUB_TOKEN           = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY      = os.environ.get("GITHUB_REPOSITORY", "")

IG_HANDLE = "@Super_dumb_heroes"
MEDIA_RELEASE_TAG = "media-cache"

REQUIRED_ENV_VARS = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "GITHUB_TOKEN"]

def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print(f"❌ FATAL: Missing required secret(s): {', '.join(missing)}")
        sys.exit(1)

# ============================================================
# TIER 1: CONTENT & IMAGE SELECTION (justmeme.wtf -> Fallback)
# ============================================================
def generate_content() -> dict:
    characters = ["Spider-Man", "Batman", "Thanos", "Superman", "The Flash", "Iron Man", "Deadpool"]
    chosen_hero = random.choice(characters)
    
    print("🧠 [1/2] Trying justmeme.wtf API for Authentic Meme Generation...")
    try:
        # Step 1: Let justmeme.wtf pick the template and write the joke
        meme_res = requests.post(
            "https://justmeme.wtf/api/v1/ai-generate", 
            json={"prompt": f"A meme about {chosen_hero} complaining about a mundane everyday problem"},
            timeout=15
        ).json()
        
        if meme_res.get("success"):
            slug = meme_res.get("template")
            top_text = meme_res.get("top_text", "")
            bottom_text = meme_res.get("bottom_text", "")
            
            # Step 2: Fetch the blank template image URL
            temp_res = requests.get(f"https://justmeme.wtf/api/v1/templates/{slug}", timeout=10).json()
            template_obj = temp_res.get("template", {})
            img_url = template_obj.get("blank_url") or template_obj.get("url") or template_obj.get("image_url")
            
            if img_url:
                img_path = f"output/template_{int(time.time())}.jpg"
                with open(img_path, "wb") as f:
                    f.write(requests.get(img_url, timeout=15).content)
                
                print("✅ Successfully generated meme via justmeme.wtf!")
                return {
                    "source": "justmeme",
                    "hero": chosen_hero,
                    "hook": top_text,
                    "script": bottom_text,
                    "image_path": img_path,
                    "caption": f"Even heroes hate Mondays. 🦸‍♂️🤦‍♂️\n\nFollow @Super_dumb_heroes for daily struggles."
                }
    except Exception as e:
        print(f"⚠️ justmeme.wtf failed ({e}). Falling back to Text AI + HuggingFace...")

    # --- FALLBACK: If justmeme.wtf is down, we use the original LLM + FLUX method ---
    prompt = f"""Write a short joke where {chosen_hero} is complaining about a mundane problem.
Return JSON: {{"hero": "{chosen_hero}", "hook": "Setup...", "script": "Punchline...", "image_prompt": "Cinematic vertical 9:16 portrait of {chosen_hero} looking exhausted, 8k"}}"""

    fallbacks = [
        {"name": "OpenRouter", "api_key": OPENROUTER_API_KEY, "url": "https://openrouter.ai/api/v1", "model": "openrouter/free"},
        {"name": "Groq", "api_key": GROQ_API_KEY, "url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    ]

    for provider in fallbacks:
        if not provider["api_key"]: continue
        try:
            print(f"🔄 Trying {provider['name']}...")
            client = OpenAI(base_url=provider["url"], api_key=provider["api_key"])
            response = client.chat.completions.create(model=provider["model"], messages=[{"role": "user", "content": prompt}], temperature=0.8)
            data = json.loads(response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip())
            
            # Generate FLUX Image
            img_path = f"output/base_img_{int(time.time())}.png"
            if HF_TOKEN:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=HF_TOKEN)
                image = client.text_to_image(data["image_prompt"], model="black-forest-labs/FLUX.1-schnell")
                image.resize((1080, 1920), Image.Resampling.LANCZOS).convert("RGB").save(img_path)
            
            data["source"] = "fallback"
            data["image_path"] = img_path
            data["caption"] = "Make it make sense. 🦸‍♂️🤦‍♂️\n\nFollow @Super_dumb_heroes for daily superhero struggles."
            return data
        except Exception as err:
            print(f"⚠️ {provider['name']} failed: {err}")

    sys.exit(1)

# ============================================================
# TIER 2: VOICE GENERATION (Comedic Timing)
# ============================================================
def generate_tts(data: dict) -> list:
    print("🎙️ Generating audio (Setup and Punchline separately)...")
    import edge_tts
    lines = [data['hook'], data['script']]
    output_paths = []

    async def _speak():
        for i, text in enumerate(lines):
            out_path = f"output/tts_part_{i}_{int(time.time())}.mp3"
            # Using Guy for deadpan, sarcastic delivery
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="-15%", pitch="-5Hz")
            await communicate.save(out_path)
            output_paths.append(out_path)

    try:
        asyncio.run(_speak())
        return output_paths
    except Exception as e:
        print(f"❌ FATAL: Edge-TTS failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: VIDEO COMPOSITOR (Smart Padding & Meme Fonts)
# ============================================================
def draw_meme_text(draw, text, y_pos, font):
    if not text: return
    wrapped = "\n".join(textwrap.wrap(text.upper(), width=25))
    x, outline = 540, 3
    
    # Classic Meme Black Outline
    for dx in range(-outline, outline+1):
        for dy in range(-outline, outline+1):
            if dx != 0 or dy != 0:
                draw.text((x+dx, y_pos+dy), wrapped, font=font, fill="black", anchor="mm", align="center")
    # White inner text
    draw.text((x, y_pos), wrapped, font=font, fill="white", anchor="mm", align="center")

def create_reel_video(data: dict, tts_paths: list) -> str:
    print("🎬 Compositing Video with Meme Overlays...")
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_audioclips
        
        # 1. AUDIO PACING (The 1.2 second comedic silence)
        hook_audio = AudioFileClip(tts_paths[0])
        script_audio = AudioFileClip(tts_paths[1])
        silence = hook_audio.subclip(0, min(1.2, hook_audio.duration)).volumex(0)
        final_audio = concatenate_audioclips([hook_audio, silence, script_audio])
        duration = min(final_audio.duration + 1.0, 30.0)

        # 2. VISUALS
        base_img = Image.open(data["image_path"]).convert("RGBA")
        
        if data.get("source") == "justmeme":
            # Smart padding: Blurs the background to make horizontal templates fit a vertical Reel
            bg_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(40)).convert("RGB")
            ratio = 1080 / float(base_img.size[0])
            new_h = int(float(base_img.size[1]) * ratio)
            fg_img = base_img.resize((1080, new_h), Image.Resampling.LANCZOS)
            bg_img.paste(fg_img, (0, (1920 - new_h) // 2), fg_img)
        else:
            # Fallback handling: Adds dark overlay for readability
            dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 140))
            bg_img = Image.alpha_composite(base_img.resize((1080, 1920)), dark_overlay).convert("RGB")
            
        draw = ImageDraw.Draw(bg_img)
        try:
            # Attempt to use a bold font for the meme aesthetic
            font_meme = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font_meme = ImageFont.load_default()

        # Place text at top and bottom of the vertical canvas
        draw_meme_text(draw, data["hook"], 300, font_meme)
        draw_meme_text(draw, data["script"], 1600, font_meme)
        
        captioned_img_path = f"output/captioned_{int(time.time())}.jpg"
        bg_img.save(captioned_img_path, "JPEG", quality=95)

        # 3. MOVIEPY RENDER
        final_video = ImageClip(captioned_img_path).set_duration(duration).set_audio(final_audio)
        reel_path = f"output/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        final_video.write_videofile(reel_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        
        return reel_path
    except Exception as e:
        print(f"❌ Video render failure: {e}")
        return None

# ============================================================
# GITHUB RELEASES & INSTAGRAM PUBLISHER
# ============================================================
def _gh_headers(): return {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

def upload_public_media(path: str) -> tuple:
    api_base = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
    res = requests.get(f"{api_base}/releases/tags/{MEDIA_RELEASE_TAG}", headers=_gh_headers())
    if res.status_code != 200:
        res = requests.post(f"{api_base}/releases", headers=_gh_headers(), json={"tag_name": MEDIA_RELEASE_TAG, "name": "Media Cache", "prerelease": True})
    
    release_id = res.json()["id"]
    filename = os.path.basename(path)
    url = f"https://uploads.github.com/repos/{GITHUB_REPOSITORY}/releases/{release_id}/assets"
    
    with open(path, "rb") as f:
        up_res = requests.post(url, headers={**_gh_headers(), "Content-Type": "video/mp4"}, params={"name": filename}, data=f)
    asset = up_res.json()
    return asset["browser_download_url"], asset["id"]

def delete_public_media(asset_id: int):
    try: requests.delete(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/assets/{asset_id}", headers=_gh_headers())
    except: pass

def post_to_instagram(media_path: str, caption: str) -> bool:
    print(f"📱 Publishing to Instagram...")
    asset_id = None
    try:
        media_url, asset_id = upload_public_media(media_path)
        payload = {"access_token": INSTAGRAM_ACCESS_TOKEN, "caption": caption, "media_type": "REELS", "video_url": media_url}
        c_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media", data=payload).json()
        container_id = c_res.get("id")
        if not container_id: return False

        for _ in range(25):
            time.sleep(10)
            status = requests.get(f"https://graph.instagram.com/v21.0/{container_id}?fields=status_code&access_token={INSTAGRAM_ACCESS_TOKEN}").json()
            if status.get("status_code") == "FINISHED": break
            if status.get("status_code") == "ERROR": return False

        p_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish", data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN}).json()
        return "id" in p_res
    finally:
        if asset_id: delete_public_media(asset_id)

def run():
    print(f"📦 Bot version: {BOT_VERSION}")
    validate_environment()
    os.makedirs("output", exist_ok=True)
    
    data = generate_content()
    tts_paths = generate_tts(data)
    reel_path = create_reel_video(data, tts_paths)

    if reel_path and post_to_instagram(reel_path, data["caption"]):
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
    
