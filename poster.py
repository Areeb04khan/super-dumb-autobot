# -*- coding: utf-8 -*-
"""
Trending Meme Bot v5.0 (The Round-Robin Engine)
- API Cycle: JustMeme -> Hugging Face -> Magic Hour (Video) -> Pollinations
- Audio: Edge-TTS with Google SFX and timed comedic pauses.
- Visuals: Unified transparent text overlays for both static images and AI video.
- Resilience: Auto-advances to the next API in the cycle if one fails.
"""
BOT_VERSION = "v5.0"

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
# CONFIGURATION & SECRETS
# ============================================================
OPENROUTER_API_KEY     = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
HF_TOKEN               = os.environ.get("HF_TOKEN", "")
POLLINATIONS_API_KEY   = os.environ.get("POLLINATIONS_API_KEY", "")
MAGIC_HOUR_API_KEY     = os.environ.get("MAGIC_HOUR_API_KEY", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID      = os.environ.get("INSTAGRAM_USER_ID", "")
GITHUB_TOKEN           = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY      = os.environ.get("GITHUB_REPOSITORY", "")

IG_HANDLE = "@Super_dumb_heroes"
MEDIA_RELEASE_TAG = "media-cache"
REQUIRED_ENV_VARS = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "GITHUB_TOKEN"]

SFX_URLS = [
    "https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg",
    "https://actions.google.com/sounds/v1/cartoon/clown_horn.ogg",
    "https://actions.google.com/sounds/v1/cartoon/pop.ogg",
    "https://actions.google.com/sounds/v1/cartoon/slide_whistle.ogg"
]

def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print(f"❌ FATAL: Missing required secret(s): {', '.join(missing)}")
        sys.exit(1)

# ============================================================
# TIER 1: TEXT SCRIPT GENERATOR
# ============================================================
def generate_text_script() -> dict:
    prompt = """Write a highly relatable, viral 2-part meme joke about an everyday struggle.
Return strictly valid JSON: {"hook": "Top text setup...", "script": "Bottom text punchline...", "image_prompt": "Cinematic vertical 9:16 portrait of a person looking exhausted, 8k"}"""

    fallbacks = [
        {"name": "OpenRouter", "api_key": OPENROUTER_API_KEY, "url": "https://openrouter.ai/api/v1", "model": "openrouter/free"},
        {"name": "Groq", "api_key": GROQ_API_KEY, "url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    ]

    for provider in fallbacks:
        if not provider["api_key"]: continue
        try:
            client = OpenAI(base_url=provider["url"], api_key=provider["api_key"])
            response = client.chat.completions.create(model=provider["model"], messages=[{"role": "user", "content": prompt}], temperature=0.8)
            data = json.loads(response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip())
            return data
        except Exception:
            pass
    raise RuntimeError("All Text AI providers failed.")

# ============================================================
# TIER 2: CYCLICAL VISUAL ENGINES
# ============================================================
def fetch_justmeme():
    print("🎨 Engine: JustMeme (Authentic Template)")
    meme_res = requests.post("https://justmeme.wtf/api/v1/ai-generate", json={"prompt": "A highly relatable everyday struggle"}, timeout=15).json()
    if not meme_res.get("success"): raise Exception("JustMeme generation failed")
    
    slug = meme_res.get("template")
    temp_res = requests.get(f"https://justmeme.wtf/api/v1/templates/{slug}", timeout=10).json()
    img_url = temp_res.get("template", {}).get("blank_url") or temp_res.get("template", {}).get("url")
    
    img_path = f"output/visual_{int(time.time())}.jpg"
    with open(img_path, "wb") as f: f.write(requests.get(img_url, timeout=15).content)
    
    # Smart blur-padding for horizontal memes to fit 9:16
    base_img = Image.open(img_path).convert("RGBA")
    bg_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(50)).convert("RGB")
    ratio = 1080 / float(base_img.size[0])
    new_h = int(float(base_img.size[1]) * ratio)
    fg_img = base_img.resize((1080, new_h), Image.Resampling.LANCZOS)
    bg_img.paste(fg_img, (0, (1920 - new_h) // 2), fg_img)
    bg_img.save(img_path, "JPEG", quality=95)
    
    return {"hook": meme_res["top_text"], "script": meme_res["bottom_text"], "media_path": img_path, "is_video": False}

def fetch_huggingface(prompt):
    print("🎨 Engine: Hugging Face (FLUX Image)")
    if not HF_TOKEN: raise Exception("Missing HF_TOKEN")
    from huggingface_hub import InferenceClient
    
    client = InferenceClient(token=HF_TOKEN)
    image = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")
    
    img_path = f"output/visual_{int(time.time())}.png"
    dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 120))
    bg_img = Image.alpha_composite(image.resize((1080, 1920), Image.Resampling.LANCZOS).convert("RGBA"), dark_overlay).convert("RGB")
    bg_img.save(img_path)
    return img_path

def fetch_magichour(prompt):
    print("🎨 Engine: Magic Hour (AI Video Animation)")
    if not MAGIC_HOUR_API_KEY: raise Exception("Missing MAGIC_HOUR_API_KEY")
    
    # Step 1: Get a base image from HF first
    img_path = fetch_huggingface(prompt)
    
    # Step 2: Upload to free temp host so Magic Hour can read it
    with open(img_path, "rb") as f:
        upload_res = requests.post("https://tempfile.org/api/upload/local", files={"files": (os.path.basename(img_path), f)}).json()
        public_url = f"{upload_res['files'][0]['url'].rstrip('/')}/download"
    
    # Step 3: Trigger Video Generation
    headers = {"Authorization": f"Bearer {MAGIC_HOUR_API_KEY}", "Content-Type": "application/json"}
    payload = {"end_seconds": 4, "resolution": "720p", "assets": {"image_file_path": public_url}}
    
    init_res = requests.post("https://api.magichour.ai/v1/image-to-video", headers=headers, json=payload).json()
    if "id" not in init_res: raise Exception(f"Magic Hour init failed: {init_res}")
    
    task_id = init_res["id"]
    print(f"   ↳ Task started ({task_id}). Polling for completion...")
    
    # Step 4: Poll for completion
    for _ in range(30): # 5 minutes max wait
        time.sleep(10)
        status_res = requests.get(f"https://api.magichour.ai/v1/image-to-video/{task_id}", headers=headers).json()
        if status_res.get("status") == "success":
            video_url = status_res["downloads"][0]["url"]
            vid_path = f"output/visual_{int(time.time())}.mp4"
            with open(vid_path, "wb") as f: f.write(requests.get(video_url).content)
            print("✅ Magic Hour video rendered!")
            return vid_path
        elif status_res.get("status") in ["failed", "canceled"]:
            raise Exception("Magic Hour generation failed on server.")
    raise Exception("Magic Hour polling timed out.")

def fetch_pollinations(prompt):
    print("🎨 Engine: Pollinations (Flux Image)")
    img_path = f"output/visual_{int(time.time())}.png"
    url = f"https://gen.pollinations.ai/image/{requests.utils.quote(prompt)}?model=flux&width=1080&height=1920&nologo=true"
    headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"} if POLLINATIONS_API_KEY else {}
    
    res = requests.get(url, headers=headers, timeout=45)
    if res.status_code == 200 and len(res.content) > 5000:
        base_img = Image.open(requests.compat.BytesIO(res.content)).convert("RGBA")
        dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 120))
        bg_img = Image.alpha_composite(base_img, dark_overlay).convert("RGB")
        bg_img.save(img_path)
        return img_path
    raise Exception("Pollinations API failed or returned invalid data.")

# ============================================================
# TIER 3: AUDIO & SFX ENGINE
# ============================================================
def generate_audio(data: dict) -> dict:
    print("🎙️ Generating Voiceover & SFX...")
    import edge_tts
    
    lines = [data['hook'], data['script'], "Send this to that one friend who needs to hear it."]
    paths = []

    async def _speak():
        for i, text in enumerate(lines):
            p = f"output/tts_{i}_{int(time.time())}.mp3"
            pitch = "-5Hz" if i < 2 else "+2Hz"
            await edge_tts.Communicate(text, "en-US-GuyNeural", rate="-10%", pitch=pitch).save(p)
            paths.append(p)

    asyncio.run(_speak())
    
    def get_sfx():
        p = f"output/sfx_{random.randint(1000,9999)}.ogg"
        with open(p, "wb") as f: f.write(requests.get(random.choice(SFX_URLS)).content)
        return p

    return {"hook": paths[0], "script": paths[1], "cta": paths[2], "sfx1": get_sfx(), "sfx2": get_sfx()}

# ============================================================
# TIER 4: UNIVERSAL COMPOSITOR (Handles Images & Video)
# ============================================================
def create_text_overlay(hook, script):
    """Creates a transparent PNG with the meme text that can overlay ANY media."""
    overlay = Image.new("RGBA", (1080, 1920), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    try: font_meme = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
    except: font_meme = ImageFont.load_default()

    def draw_outline(y_pos, text):
        wrapped = "\n".join(textwrap.wrap(text.upper(), width=22))
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                draw.text((540+dx, y_pos+dy), wrapped, font=font_meme, fill="black", anchor="mm", align="center")
        draw.text((540, y_pos), wrapped, font=font_meme, fill="white", anchor="mm", align="center")

    draw_outline(300, hook)
    draw_outline(1600, script)
    path = f"output/overlay_{int(time.time())}.png"
    overlay.save(path)
    return path

def composite_final_reel(visual_data, audio_assets):
    print("🎬 Compositing Final Reel...")
    from moviepy.editor import ImageClip, VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
    
    # 1. Audio Timeline
    h_clip = AudioFileClip(audio_assets["hook"]).set_start(0)
    s1_clip = AudioFileClip(audio_assets["sfx1"]).volumex(0.6).set_start(h_clip.duration + 0.2)
    s_clip = AudioFileClip(audio_assets["script"]).set_start(s1_clip.start + 1.2)
    s2_clip = AudioFileClip(audio_assets["sfx2"]).volumex(0.8).set_start(s_clip.start + s_clip.duration + 0.1)
    cta_clip = AudioFileClip(audio_assets["cta"]).set_start(s2_clip.start + 1.0)
    
    final_audio = CompositeAudioClip([h_clip, s1_clip, s_clip, s2_clip, cta_clip])
    duration = min(final_audio.duration + 0.5, 30.0)

    # 2. Visual Timeline (Handling both Images and Video)
    if visual_data["is_video"]:
        # Loop the short video to fit the audio duration
        base_clip = VideoFileClip(visual_data["media_path"]).loop(duration=duration)
    else:
        base_clip = ImageClip(visual_data["media_path"]).set_duration(duration)

    overlay_path = create_text_overlay(visual_data["hook"], visual_data["script"])
    text_clip = ImageClip(overlay_path).set_duration(duration)
    
    final_video = CompositeVideoClip([base_clip, text_clip]).set_audio(final_audio)
    reel_path = f"output/final_reel_{int(time.time())}.mp4"
    
    final_video.write_videofile(reel_path, fps=30, codec="libx264", audio_codec="aac", bitrate="8000k", verbose=False, logger=None)
    return reel_path

# ============================================================
# INSTAGRAM & GITHUB HOSTING (UNCHANGED)
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
    print("📱 Publishing to Instagram...")
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

# ============================================================
# MAIN ROUND-ROBIN LOOP
# ============================================================
def load_progress():
    if os.path.exists("progress.json"):
        with open("progress.json") as f: return json.load(f)
    return {"engine_index": 0}

def save_progress(p):
    with open("progress.json", "w") as f: json.dump(p, f)

def run():
    print(f"📦 Bot version: {BOT_VERSION}")
    validate_environment()
    os.makedirs("output", exist_ok=True)
    
    p = load_progress()
    target_engine = p["engine_index"] % 4
    
    visual_data = None
    
    # Cycle through the engines until one succeeds
    for attempt_offset in range(4):
        current_engine = (target_engine + attempt_offset) % 4
        try:
            if current_engine == 0:
                visual_data = fetch_justmeme()
            else:
                # Engines 1-3 require text AI first
                text_data = generate_text_script()
                prompt = text_data["image_prompt"]
                visual_data = {"hook": text_data["hook"], "script": text_data["script"]}
                
                if current_engine == 1:
                    visual_data["media_path"] = fetch_huggingface(prompt)
                    visual_data["is_video"] = False
                elif current_engine == 2:
                    visual_data["media_path"] = fetch_magichour(prompt)
                    visual_data["is_video"] = True
                elif current_engine == 3:
                    visual_data["media_path"] = fetch_pollinations(prompt)
                    visual_data["is_video"] = False
            
            # If we reached here, the engine succeeded!
            print(f"✅ Selected Engine {current_engine} succeeded.")
            # Move the pointer forward for the NEXT cron run
            p["engine_index"] = (current_engine + 1) % 4
            save_progress(p)
            break
        except Exception as e:
            print(f"⚠️ Engine {current_engine} failed: {e}. Cycling to next...")
            
    if not visual_data:
        print("❌ FATAL: All visual engines failed in this cycle.")
        sys.exit(1)

    audio_assets = generate_audio(visual_data)
    reel_path = composite_final_reel(visual_data, audio_assets)
    
    caption = f"Literally me. 💀\n\nTag that one friend who always does this. 👇\n\nFollow {IG_HANDLE} for daily struggles."
    if reel_path and post_to_instagram(reel_path, caption):
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
    
