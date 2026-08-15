# -*- coding: utf-8 -*-
"""
Trending Meme Bot v4.0 (The Viral Engagement Upgrade)
- Primary AI: justmeme.wtf targeting broad, relatable, trending memes.
- Audio Engine: Advanced compositing with Hook -> SFX -> Punchline -> SFX -> Invisible CTA.
- SFX Library: Dynamically fetches free Google Action sounds.
- Visuals: Ultra-crisp 1080p (high bitrate) smart-padded templates.
- Engagement: Built-in invisible TTS CTAs & caption comment-bait.
"""
BOT_VERSION = "v4.0"

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

IG_HANDLE = "@Super_dumb_heroes" # Feel free to change this to your new handle
MEDIA_RELEASE_TAG = "media-cache"

REQUIRED_ENV_VARS = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "GITHUB_TOKEN"]

# Reliable, free public domain SFX from Google's library
SFX_URLS = [
    "https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg",
    "https://actions.google.com/sounds/v1/cartoon/clown_horn.ogg",
    "https://actions.google.com/sounds/v1/cartoon/pop.ogg",
    "https://actions.google.com/sounds/v1/cartoon/slide_whistle.ogg",
    "https://actions.google.com/sounds/v1/cartoon/wood_plank_flicks.ogg",
    "https://actions.google.com/sounds/v1/foley/glass_break.ogg"
]

def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print(f"❌ FATAL: Missing required secret(s): {', '.join(missing)}")
        sys.exit(1)

# ============================================================
# TIER 1: CONTENT (Broad, Trending Memes + CTAs)
# ============================================================
def generate_content() -> dict:
    print("🧠 [1/2] Fetching Trending Meme via justmeme.wtf...")
    
    # Engaging questions to prompt algorithm-boosting comments
    caption_ctas = [
        "What would you do in this situation? Let me know below! 👇",
        "Tag that one friend who literally always does this. 😂",
        "Are you guilty of this? Be honest in the comments. 👀",
        "If this isn't the most relatable thing today... comment your thoughts! 🗣️"
    ]
    
    try:
        meme_res = requests.post(
            "https://justmeme.wtf/api/v1/ai-generate", 
            # Switched prompt from superheroes to general viral relatability
            json={"prompt": "A highly relatable, trending everyday struggle, embarrassing moment, or viral meme concept."},
            timeout=15
        ).json()
        
        if meme_res.get("success"):
            slug = meme_res.get("template")
            
            temp_res = requests.get(f"https://justmeme.wtf/api/v1/templates/{slug}", timeout=10).json()
            template_obj = temp_res.get("template", {})
            img_url = template_obj.get("blank_url") or template_obj.get("url")
            
            if img_url:
                img_path = f"output/template_{int(time.time())}.jpg"
                with open(img_path, "wb") as f:
                    f.write(requests.get(img_url, timeout=15).content)
                
                print("✅ Authentic meme template secured!")
                return {
                    "source": "justmeme",
                    "hook": meme_res.get("top_text", ""),
                    "script": meme_res.get("bottom_text", ""),
                    "image_path": img_path,
                    "caption": f"Literally me. 💀\n\n{random.choice(caption_ctas)}\n\nFollow {IG_HANDLE} for daily memes."
                }
    except Exception as e:
        print(f"⚠️ justmeme.wtf failed ({e}). Falling back to Text AI...")

    # --- FALLBACK: Standard AI Generation ---
    prompt = """Write a highly relatable, viral 2-part meme joke about an everyday struggle.
Return JSON: {"hook": "Top text setup...", "script": "Bottom text punchline...", "image_prompt": "Cinematic vertical 9:16 portrait of a person looking exhausted, 8k"}"""

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
            
            img_path = f"output/base_img_{int(time.time())}.png"
            if HF_TOKEN:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=HF_TOKEN)
                image = client.text_to_image(data["image_prompt"], model="black-forest-labs/FLUX.1-schnell")
                image.resize((1080, 1920), Image.Resampling.LANCZOS).convert("RGB").save(img_path)
            
            data["source"] = "fallback"
            data["image_path"] = img_path
            data["caption"] = f"Make it make sense. 🤦‍♂️\n\n{random.choice(caption_ctas)}\n\nFollow {IG_HANDLE}."
            return data
        except Exception as err:
            pass
    sys.exit(1)

# ============================================================
# TIER 2: VOICE & SFX ENGINE (Invisible CTA + Sound Effects)
# ============================================================
def fetch_random_sfx() -> str:
    """Downloads a random comedic sound effect from the Google library."""
    url = random.choice(SFX_URLS)
    path = f"output/sfx_{int(time.time())}_{random.randint(1,1000)}.ogg"
    with open(path, "wb") as f:
        f.write(requests.get(url, timeout=10).content)
    return path

def generate_tts(data: dict) -> dict:
    print("🎙️ Generating Voiceover, CTAs, and SFX...")
    import edge_tts
    
    # The 3rd line is the "Invisible" CTA. It will be heard, but not written on the screen.
    invisible_ctas = [
        "Send this to that one friend who needs to hear it.",
        "If you didn't laugh, tag a friend to waste their time too.",
        "Share this to your story if you agree."
    ]
    
    lines = [data['hook'], data['script'], random.choice(invisible_ctas)]
    output_paths = []

    async def _speak():
        for i, text in enumerate(lines):
            out_path = f"output/tts_part_{i}_{int(time.time())}.mp3"
            # Part 3 (CTA) gets a slightly different pitch so it sounds like an "announcer" step-in
            pitch = "-5Hz" if i < 2 else "+2Hz"
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="-10%", pitch=pitch)
            await communicate.save(out_path)
            output_paths.append(out_path)

    try:
        asyncio.run(_speak())
        
        # Download two random SFX for the compositing phase
        sfx1 = fetch_random_sfx()
        sfx2 = fetch_random_sfx()
        
        return {
            "hook": output_paths[0],
            "script": output_paths[1],
            "cta": output_paths[2],
            "sfx1": sfx1,
            "sfx2": sfx2
        }
    except Exception as e:
        print(f"❌ FATAL: Audio engine failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: ADVANCED VIDEO COMPOSITOR
# ============================================================
def draw_meme_text(draw, text, y_pos, font):
    if not text: return
    wrapped = "\n".join(textwrap.wrap(text.upper(), width=22))
    x, outline = 540, 4
    
    for dx in range(-outline, outline+1):
        for dy in range(-outline, outline+1):
            if dx != 0 or dy != 0:
                draw.text((x+dx, y_pos+dy), wrapped, font=font, fill="black", anchor="mm", align="center")
    draw.text((x, y_pos), wrapped, font=font, fill="white", anchor="mm", align="center")

def create_reel_video(data: dict, audio_assets: dict) -> str:
    print("🎬 Compositing Video (Syncing SFX and CTAs)...")
    try:
        from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip
        
        # 1. AUDIO TIMELINE COMPOSITING
        hook_audio = AudioFileClip(audio_assets["hook"]).set_start(0)
        
        # Play first SFX right after the hook
        t_sfx1 = hook_audio.duration + 0.2
        sfx1_audio = AudioFileClip(audio_assets["sfx1"]).volumex(0.6).set_start(t_sfx1)
        
        # Wait for comedic effect, then drop punchline
        t_script = t_sfx1 + 1.2
        script_audio = AudioFileClip(audio_assets["script"]).set_start(t_script)
        
        # Play second SFX right after punchline
        t_sfx2 = t_script + script_audio.duration + 0.1
        sfx2_audio = AudioFileClip(audio_assets["sfx2"]).volumex(0.8).set_start(t_sfx2)
        
        # Drop the invisible CTA voiceover
        t_cta = t_sfx2 + 1.0
        cta_audio = AudioFileClip(audio_assets["cta"]).set_start(t_cta)
        
        final_audio = CompositeAudioClip([hook_audio, sfx1_audio, script_audio, sfx2_audio, cta_audio])
        duration = min(final_audio.duration + 0.5, 30.0)

        # 2. VISUALS (Smart Padding)
        base_img = Image.open(data["image_path"]).convert("RGBA")
        
        if data.get("source") == "justmeme":
            bg_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(50)).convert("RGB")
            ratio = 1080 / float(base_img.size[0])
            new_h = int(float(base_img.size[1]) * ratio)
            fg_img = base_img.resize((1080, new_h), Image.Resampling.LANCZOS)
            bg_img.paste(fg_img, (0, (1920 - new_h) // 2), fg_img)
        else:
            dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 140))
            bg_img = Image.alpha_composite(base_img.resize((1080, 1920)), dark_overlay).convert("RGB")
            
        draw = ImageDraw.Draw(bg_img)
        try:
            # Huge, bold font for meme readability
            font_meme = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        except:
            font_meme = ImageFont.load_default()

        draw_meme_text(draw, data["hook"], 300, font_meme)
        draw_meme_text(draw, data["script"], 1600, font_meme)
        
        captioned_img_path = f"output/captioned_{int(time.time())}.jpg"
        bg_img.save(captioned_img_path, "JPEG", quality=100) # Max JPEG quality

        # 3. HIGH BITRATE MOVIEPY RENDER
        final_video = ImageClip(captioned_img_path).set_duration(duration).set_audio(final_audio)
        reel_path = f"output/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # Pushing a heavy 8000k bitrate to trick Instagram into retaining ultimate crispness
        final_video.write_videofile(
            reel_path, fps=30, codec="libx264", audio_codec="aac", 
            bitrate="8000k", verbose=False, logger=None
        )
        
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
    audio_assets = generate_tts(data)
    reel_path = create_reel_video(data, audio_assets)

    if reel_path and post_to_instagram(reel_path, data["caption"]):
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
        
