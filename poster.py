# -*- coding: utf-8 -*-
"""
Super Dumb Heroes Bot v2.1 
- Fixed: MoviePy PIL.Image.ANTIALIAS compatibility with Pillow 10+
- Host Upgrade: Replaced tempfile.org with free GitHub Releases media hosting
- AI Chain: OpenRouter -> Groq -> NVIDIA NIM
- Image Chain: Hugging Face (FLUX) <-> Pollinations AI
"""
BOT_VERSION = "v2.1"

# === CRITICAL PILLOW 10 PATCH ===
# MoviePy 1.0.3 calls Image.ANTIALIAS, which Pillow 10+ removed. 
# We patch it back in before importing MoviePy.
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
from datetime import datetime
from openai import OpenAI
from PIL import Image

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

IG_HANDLE = "@Super_dumb_heroes"

# GitHub Actions gives us these for free to host media temporarily
GITHUB_TOKEN           = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY      = os.environ.get("GITHUB_REPOSITORY", "")
MEDIA_RELEASE_TAG      = "media-cache"

REQUIRED_ENV_VARS = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "GITHUB_TOKEN"]

def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print(f"❌ FATAL: Missing required secret(s): {', '.join(missing)}")
        sys.exit(1)
    if not any([OPENROUTER_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY]):
        print("❌ FATAL: At least one Text AI API key (OpenRouter, Groq, or NVIDIA) must be provided!")
        sys.exit(1)
    if not any([HF_TOKEN, POLLINATIONS_API_KEY]):
        print("❌ FATAL: At least one Image API key (HF_TOKEN or POLLINATIONS_API_KEY) must be provided!")
        sys.exit(1)

# ============================================================
# TIER 1: TEXT GENERATION (Multi-Provider Chain)
# ============================================================
def generate_content(used_heroes: list = None) -> dict:
    used_heroes = used_heroes or []
    print(f"🧠 Querying Text AI Chain for {IG_HANDLE}...")

    characters = ["Spider-Man", "Batman", "Thanos", "Superman", "The Flash", "Iron Man", "Deadpool", "Thor", "Wolverine", "Aquaman"]
    # Pick a hero we haven't posted recently
    available_heroes = [h for h in characters if h not in used_heroes[-4:]]
    chosen_hero = random.choice(available_heroes if available_heroes else characters)

    prompt = f"""Act as a sarcastic pop-culture comedy writer.
Write a short, punchy, 3-sentence script where {chosen_hero} is complaining about a mundane, relatable, everyday problem made absurd by their superhero status or lifestyle.

Return strictly valid JSON:
{{
  "hero": "{chosen_hero}",
  "hook": "The punchy opening hook...",
  "script": "The rest of the comedic complaint...",
  "image_prompt": "Cinematic vertical 9:16 portrait photo of {chosen_hero} looking annoyed in a mundane everyday situation, highly detailed, dramatic lighting, photorealistic, 8k",
  "caption": "Even saving the multiverse doesn't exempt you from daily nonsense. 🦸‍♂️☕\\n\\nFollow @Super_dumb_heroes for daily superhero struggles."
}}"""

    fallbacks = [
        {"name": "OpenRouter", "api_key": OPENROUTER_API_KEY, "base_url": "https://openrouter.ai/api/v1", "model": "openrouter/free"},
        {"name": "Groq", "api_key": GROQ_API_KEY, "base_url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
        {"name": "NVIDIA NIM", "api_key": NVIDIA_API_KEY, "base_url": "https://integrate.api.nvidia.com/v1", "model": "meta/llama-3.1-70b-instruct"}
    ]

    for index, provider in enumerate(fallbacks, start=1):
        if not provider["api_key"]: continue
        try:
            print(f"🔄 [{index}/3] Trying {provider['name']} for script generation...")
            client = OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])
            response = client.chat.completions.create(
                model=provider["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            print(f"✅ Generated script for {data.get('hero', chosen_hero)} via {provider['name']}!")
            return data
        except Exception as err:
            print(f"⚠️ {provider['name']} failed: {err}")

    print("❌ FATAL: All Text AI providers failed.")
    sys.exit(1)

# ============================================================
# TIER 2: VOICE GENERATION (Edge TTS)
# ============================================================
def generate_tts(data: dict) -> str:
    print("🎙️ Generating narration via Edge-TTS...")
    # Added natural pacing pause between hook and script
    full_text = f"{data['hook']} ... {data['script']}"
    out_path = f"output/tts_{int(time.time())}.mp3"

    import edge_tts
    async def _speak():
        communicate = edge_tts.Communicate(full_text, "en-US-ChristopherNeural", rate="+3%", pitch="-2Hz")
        await communicate.save(out_path)

    try:
        asyncio.run(_speak())
        print("✅ Edge-TTS Audio generated successfully!")
        return out_path
    except Exception as e:
        print(f"❌ FATAL: Edge-TTS failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: MULTI-TIER IMAGE GENERATION 
# ============================================================
def generate_base_image(prompt: str) -> str:
    out_path = f"output/base_img_{int(time.time())}.png"

    # Try Hugging Face first
    if HF_TOKEN:
        try:
            print("🎨 [1/2] Attempting Image Generation via Hugging Face (FLUX.1-schnell)...")
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=HF_TOKEN)
            image = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")
            image = image.resize((1080, 1920), Image.Resampling.LANCZOS)
            image.save(out_path)
            print("✅ Base image successfully generated via Hugging Face!")
            return out_path
        except Exception as e:
            print(f"⚠️ Hugging Face image generation failed: {e}")
            
    # Fallback to Pollinations AI
    try:
        print("🎨 [2/2] Attempting Image Generation via Pollinations AI...")
        url = f"https://gen.pollinations.ai/image/{requests.utils.quote(prompt)}?model=flux&width=1080&height=1920&nologo=true"
        headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"} if POLLINATIONS_API_KEY else {}
        res = requests.get(url, headers=headers, timeout=45)
        if res.status_code == 200 and len(res.content) > 5000:
            with open(out_path, "wb") as f:
                f.write(res.content)
            print("✅ Base image successfully generated via Pollinations AI!")
            return out_path
        else:
            print(f"⚠️ Pollinations returned status code {res.status_code}")
    except Exception as e:
        print(f"⚠️ Pollinations AI failed: {e}")

    print("❌ FATAL: All Image Generation providers failed.")
    sys.exit(1)

# ============================================================
# TIER 4: VIDEO COMPOSITOR
# ============================================================
def create_reel_video(image_path: str, audio_path: str, data: dict) -> str:
    print("🎬 Compositing 1080x1920 Reel Video with MoviePy...")
    try:
        from moviepy.editor import ImageClip, AudioFileClip
        import numpy as np

        audio_clip = AudioFileClip(audio_path)
        duration = min(audio_clip.duration + 1.2, 30.0)

        def zoom_transform(t):
            return 1.0 + 0.035 * t

        bg_clip = ImageClip(image_path).resize((1080, 1920))
        bg_clip = bg_clip.resize(zoom_transform).set_position('center').set_duration(duration)
        bg_clip = bg_clip.fl_image(lambda frame: (frame * 0.95).astype(np.uint8))

        final_video = bg_clip.set_audio(audio_clip)
        reel_path = f"output/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        final_video.write_videofile(reel_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        print("✅ Reel composited successfully!")
        return reel_path
    except Exception as e:
        print(f"❌ Video render failure: {e}")
        return None

# ============================================================
# GITHUB RELEASES MEDIA HOSTING
# ============================================================
def _gh_headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def get_or_create_media_release() -> dict:
    api_base = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
    res = requests.get(f"{api_base}/releases/tags/{MEDIA_RELEASE_TAG}", headers=_gh_headers(), timeout=15)
    if res.status_code == 200:
        return res.json()

    print("ℹ️ First run: creating one-time 'media-cache' Release for hosting...")
    res = requests.post(
        f"{api_base}/releases",
        headers=_gh_headers(),
        timeout=15,
        json={"tag_name": MEDIA_RELEASE_TAG, "name": "Media Cache", "body": "Temporary IG file hosting.", "prerelease": True, "make_latest": "false"}
    )
    res.raise_for_status()
    return res.json()

def upload_public_media(path: str) -> tuple:
    release = get_or_create_media_release()
    filename = os.path.basename(path)
    
    print(f"☁️ Uploading {filename} to GitHub Release (free host)...")
    upload_url = f"https://uploads.github.com/repos/{GITHUB_REPOSITORY}/releases/{release['id']}/assets"
    
    with open(path, "rb") as f:
        res = requests.post(
            upload_url,
            headers={**_gh_headers(), "Content-Type": "video/mp4"},
            params={"name": filename},
            data=f,
            timeout=120,
        )
    res.raise_for_status()
    asset = res.json()
    url = asset["browser_download_url"]
    print(f"✅ Hosted at: {url}")
    return url, asset["id"]

def delete_public_media(asset_id: int) -> None:
    try:
        requests.delete(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/assets/{asset_id}", headers=_gh_headers(), timeout=15)
    except:
        pass

# ============================================================
# INSTAGRAM PUBLISHER
# ============================================================
def post_to_instagram(media_path: str, caption: str) -> bool:
    print(f"📱 Publishing Reel to {IG_HANDLE}...")
    asset_id = None
    try:
        media_url, asset_id = upload_public_media(media_path)
        payload = {"access_token": INSTAGRAM_ACCESS_TOKEN, "caption": caption, "media_type": "REELS", "video_url": media_url}

        c_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media", data=payload).json()
        container_id = c_res.get("id")
        if not container_id:
            print(f"❌ Container creation failed: {c_res}")
            return False

        print("⏳ Waiting for Instagram video processing...")
        for attempt in range(1, 21):
            time.sleep(10)
            status = requests.get(f"https://graph.instagram.com/v21.0/{container_id}?fields=status_code&access_token={INSTAGRAM_ACCESS_TOKEN}").json()
            code = status.get("status_code")
            if code == "FINISHED": break
            elif code == "ERROR": return False

        p_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish", data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN}).json()
        return "id" in p_res
    except Exception as e:
        print(f"❌ Instagram API Failure: {e}")
        return False
    finally:
        if asset_id:
            delete_public_media(asset_id)

# ============================================================
# STATE MANAGEMENT
# ============================================================
def load_progress():
    if os.path.exists("progress.json"):
        with open("progress.json") as f:
            return json.load(f)
    return {"used_heroes": []}

def save_progress(p):
    with open("progress.json", "w") as f:
        json.dump(p, f, indent=2)

# ============================================================
# MAIN WORKFLOW
# ============================================================
def run():
    print(f"📦 Bot version: {BOT_VERSION}")
    validate_environment()
    os.makedirs("output", exist_ok=True)
    p = load_progress()
    
    print(f"\n🚀 STARTING WORKFLOW: [PARODY REEL] for {IG_HANDLE}\n")
    data = generate_content(p.get("used_heroes", []))
    caption = f"{data.get('caption', '')}\n\n#superheroes #marvel #dc #marvelmemes #dcmemes #superhero #relatable #humor #parody"

    audio_path = generate_tts(data)
    base_image_path = generate_base_image(data["image_prompt"])
    reel_path = create_reel_video(base_image_path, audio_path, data)

    if reel_path and post_to_instagram(reel_path, caption):
        # Prevent picking the same hero back-to-back
        p.setdefault("used_heroes", []).append(data["hero"])
        save_progress(p)
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
    
