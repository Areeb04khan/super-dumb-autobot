# -*- coding: utf-8 -*-
"""
Super Dumb Heroes Bot v2.2 (The "Actually Funny" Update)
- Fixed: MoviePy horizontal stripe codec glitch (removed buggy zoom, enforced RGB)
- Fixed: Robotic TTS (Forced line-by-line audio generation with physical silences)
- Added: Meme-style visual text overlays using PIL
"""
BOT_VERSION = "v2.2"

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
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(line_buffering=True)

# ============================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================
OPENROUTER_API_KEY     = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
NVIDIA_API_KEY         = os.environ.get("NVIDIA_API_KEY", "")
HF_TOKEN               = os.environ.get("HF_TOKEN", "")
POLLINATIONS_API_KEY   = os.environ.get("POLLINATIONS_API_KEY", "")
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
# TIER 1: TEXT GENERATION (With Forced Pauses)
# ============================================================
def generate_content(used_heroes: list = None) -> dict:
    used_heroes = used_heroes or []
    print(f"🧠 Querying Text AI Chain for {IG_HANDLE}...")

    characters = ["Spider-Man", "Batman", "Thanos", "Superman", "The Flash", "Iron Man", "Deadpool"]
    available_heroes = [h for h in characters if h not in used_heroes[-4:]]
    chosen_hero = random.choice(available_heroes if available_heroes else characters)

    # Prompt heavily modified to force short sentences and better comedic structure
    prompt = f"""Act as a sarcastic pop-culture comedy writer.
Write a short, punchy joke where {chosen_hero} is complaining about a mundane, relatable problem ruined by their superhero life.

Rules:
1. The hook is the setup. 
2. The script is the punchline. 
3. KEEP IT SHORT. Maximum 2 sentences for the script.

Return strictly valid JSON:
{{
  "hero": "{chosen_hero}",
  "hook": "Wait, let me get this straight...",
  "script": "I can lift a building, but I still have to wait 45 minutes for Comcast customer service.",
  "image_prompt": "Cinematic vertical 9:16 portrait photo of {chosen_hero} sitting on a couch looking deeply exhausted holding a cell phone, photorealistic, 8k",
  "caption": "Make it make sense. 🦸‍♂️🤦‍♂️\\n\\nFollow @Super_dumb_heroes for daily superhero struggles."
}}"""

    fallbacks = [
        {"name": "OpenRouter", "api_key": OPENROUTER_API_KEY, "base_url": "https://openrouter.ai/api/v1", "model": "openrouter/free"},
        {"name": "Groq", "api_key": GROQ_API_KEY, "base_url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    ]

    for provider in fallbacks:
        if not provider["api_key"]: continue
        try:
            print(f"🔄 Trying {provider['name']}...")
            client = OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])
            response = client.chat.completions.create(model=provider["model"], messages=[{"role": "user", "content": prompt}], temperature=0.8)
            raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            print(f"✅ Generated script via {provider['name']}!")
            return data
        except Exception as err:
            print(f"⚠️ {provider['name']} failed: {err}")

    sys.exit(1)

# ============================================================
# TIER 2: VOICE GENERATION (Line-by-Line for Comedic Timing)
# ============================================================
def generate_tts(data: dict) -> list:
    print("🎙️ Generating audio (Hook and Script separately)...")
    import edge_tts
    
    # We create separate files for the setup and punchline
    lines = [data['hook'], data['script']]
    output_paths = []

    async def _speak():
        for i, text in enumerate(lines):
            out_path = f"output/tts_part_{i}_{int(time.time())}.mp3"
            # Using Guy (more conversational) with heavily reduced speed for a deadpan delivery
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="-15%", pitch="-5Hz")
            await communicate.save(out_path)
            output_paths.append(out_path)

    try:
        asyncio.run(_speak())
        print("✅ Audio generated successfully!")
        return output_paths
    except Exception as e:
        print(f"❌ FATAL: Edge-TTS failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: IMAGE GENERATION
# ============================================================
def generate_base_image(prompt: str) -> str:
    out_path = f"output/base_img_{int(time.time())}.png"
    if HF_TOKEN:
        try:
            print("🎨 Generating via Hugging Face...")
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=HF_TOKEN)
            image = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")
            image = image.resize((1080, 1920), Image.Resampling.LANCZOS).convert("RGB")
            image.save(out_path)
            print("✅ Image generated!")
            return out_path
        except Exception as e:
            print(f"⚠️ HF failed: {e}")
            
    sys.exit(1)

# ============================================================
# TIER 4: VIDEO COMPOSITOR (Fixed Glitch & Added Text)
# ============================================================
def create_reel_video(image_path: str, tts_paths: list, data: dict) -> str:
    print("🎬 Compositing Video with Captions and Pauses...")
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_audioclips
        import numpy as np

        # 1. AUDIO PACING: Add a 1.2 second silence between the hook and the script
        hook_audio = AudioFileClip(tts_paths[0])
        script_audio = AudioFileClip(tts_paths[1])
        
        # Create a silent audio clip for the comedic pause
        silence = hook_audio.subclip(0, min(1.2, hook_audio.duration)).volumex(0)
        
        final_audio = concatenate_audioclips([hook_audio, silence, script_audio])
        duration = min(final_audio.duration + 1.0, 30.0)

        # 2. VISUALS: Draw the meme text directly onto the image using PIL
        base_img = Image.open(image_path).convert("RGBA")
        
        # Add a dark gradient overlay so white text is readable
        dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 140))
        img = Image.alpha_composite(base_img, dark_overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Load fonts (using defaults if system fonts fail)
        try:
            font_hook = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
            font_script = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
        except:
            font_hook = font_script = ImageFont.load_default()

        # Wrap text so it fits the screen
        hook_wrapped = "\n".join(textwrap.wrap(data["hook"], width=30))
        script_wrapped = "\n".join(textwrap.wrap(data["script"], width=35))

        # Draw the setup at the top, punchline in the middle
        draw.text((540, 400), hook_wrapped, font=font_hook, fill="#FFFFFF", anchor="mm", align="center", spacing=15)
        draw.text((540, 1000), script_wrapped, font=font_script, fill="#FACC15", anchor="mm", align="center", spacing=15)
        
        # Save the captioned image
        captioned_img_path = f"output/captioned_{int(time.time())}.jpg"
        img.save(captioned_img_path, "JPEG", quality=95)

        # 3. MOVIEPY: Clean static clip (No buggy zoom transforms!)
        final_video = ImageClip(captioned_img_path).set_duration(duration).set_audio(final_audio)
        reel_path = f"output/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        final_video.write_videofile(reel_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        print("✅ Reel composited cleanly!")
        return reel_path
    except Exception as e:
        print(f"❌ Video render failure: {e}")
        return None

# ============================================================
# GITHUB RELEASES & INSTAGRAM
# ============================================================
# (These remain exactly the same as they worked perfectly)
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
    base_image_path = generate_base_image(data["image_prompt"])
    
    reel_path = create_reel_video(base_image_path, tts_paths, data)

    if reel_path and post_to_instagram(reel_path, data["caption"]):
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
    
