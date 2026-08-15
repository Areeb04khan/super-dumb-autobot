# -*- coding: utf-8 -*-
"""
Super Dumb Heroes Bot v6.1 (The Anti-Spam & Viral Comedy Update)
- Writing: High-IQ satirical comedy (OpenRouter/Groq)
- Voice: ElevenLabs / Sarcastic Edge-TTS (Split generation for timing)
- Visuals: Clean UI Card, EXIF metadata stripped to bypass IG filters
- Video: Custom Frame Generator with Animated Progress Bar (Bypasses static pixel filter)
- Audio: Randomized comedic gaps to prevent fingerprinting
- Hosting: GitHub Releases
"""
BOT_VERSION = "v6.1"

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
ELEVENLABS_API_KEY     = os.environ.get("ELEVENLABS_API_KEY", "")
OPENROUTER_API_KEY     = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
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
# TIER 1: HIGH-IQ COMEDY GENERATOR
# ============================================================
COMEDY_SYSTEM_PROMPT = """You write viral, deadpan, satirical comedy for internet culture. 
Tone: Hyper-specific, dry, cynical, unhinged, absurd realism.

RULES:
1. STRICTLY FORBIDDEN: Boomer tropes, puns, coffee jokes, Monday complaints, generic laundry jokes.
2. Structure: Setup (Hook) -> Sharp, unexpected, deadpan punchline (Script).
3. Focus on: Legal disputes, bureaucratic nightmares, hyper-specific biological curses of having powers, modern tech friction.

FEW-SHOT EXAMPLES OF THE HUMOR STYLE:
- Example 1:
  Hook: "Batman spends 40 million dollars on stealth technology every single year..."
  Script: "Yet he still gets hit with a 45 dollar service fee because the Batmobile took up two parking spots at CVS."
  Prompt: "Candid flash photography of Batman in full tactical armor standing awkwardly at a CVS pharmacy self-checkout counter, grainy 35mm documentary film still"

- Example 2:
  Hook: "Nobody talks about the real downside of Superman having microscopic telescopic vision..."
  Script: "He has to watch every single dust mite mate on his pillow before he can fall asleep."
  Prompt: "Cinematic portrait shot of Superman lying wide awake in bed staring at the ceiling in total psychological exhaustion, dark moody bedroom, 8k"

Return strictly valid JSON:
{
  "hero": "Character Name",
  "hook": "The provocative deadpan setup...",
  "script": "The absurd, hyper-specific punchline...",
  "image_prompt": "Specific candid photography prompt without generic text...",
  "caption": "The harsh reality. 💀\\n\\nWhat would you actually do in this situation?\\n\\nFollow @Super_dumb_heroes for daily breakdowns."
}"""

def generate_satirical_script() -> dict:
    print("🧠 Crafting comedy script via LLM Chain...")
    
    characters = [
        "Batman", "Spider-Man", "Superman", "The Flash", "Thanos", 
        "Professor X", "Wolverine", "Iron Man", "Doctor Strange", "Magneto"
    ]
    hero = random.choice(characters)
    user_prompt = f"Write a new, original, sharp satirical bit about {hero}."

    fallbacks = [
        {"name": "OpenRouter", "api_key": OPENROUTER_API_KEY, "url": "https://openrouter.ai/api/v1", "model": "openrouter/free"},
        {"name": "Groq", "api_key": GROQ_API_KEY, "url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    ]

    for provider in fallbacks:
        if not provider["api_key"]: continue
        try:
            print(f"🔄 Querying {provider['name']}...")
            client = OpenAI(base_url=provider["url"], api_key=provider["api_key"])
            response = client.chat.completions.create(
                model=provider["model"],
                messages=[
                    {"role": "system", "content": COMEDY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.85
            )
            raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            print(f"✅ Generated script for {data.get('hero', hero)}!")
            return data
        except Exception as e:
            print(f"⚠️ {provider['name']} failed: {e}")

    raise RuntimeError("All LLM providers failed.")

# ============================================================
# TIER 2: HIGH-END SPLIT VOICE ENGINE (For Randomized Gaps)
# ============================================================
def generate_audio(data: dict) -> dict:
    print("🎙️ Generating split audio files for dynamic timing...")
    texts = {"hook": data["hook"], "script": data["script"]}
    paths = {}

    # Tier 1: ElevenLabs (Deep, Realistic Deadpan)
    if ELEVENLABS_API_KEY:
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            
            for key, text in texts.items():
                out_path = f"output/voice_{key}_{int(time.time())}.mp3"
                audio_stream = client.text_to_speech.convert(
                    text=text,
                    voice_id="pNInz6obpgDQGcFmaJgB", # Adam
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128",
                    voice_settings=VoiceSettings(stability=0.68, similarity_boost=0.80)
                )
                with open(out_path, "wb") as f:
                    for chunk in audio_stream:
                        if chunk: f.write(chunk)
                paths[key] = out_path
            print("✅ ElevenLabs Voice generated successfully!")
            return paths
        except Exception as e:
            print(f"⚠️ ElevenLabs failed ({e}). Falling back to Edge-TTS...")

    # Tier 2: Edge-TTS (Dry British Narrative Tone)
    try:
        import edge_tts
        async def _speak():
            for key, text in texts.items():
                out_path = f"output/voice_{key}_{int(time.time())}.mp3"
                communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-8%", pitch="-4Hz")
                await communicate.save(out_path)
                paths[key] = out_path
        asyncio.run(_speak())
        print("✅ Edge-TTS Voice generated successfully!")
        return paths
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: IMAGE GENERATION (Photorealistic FLUX Engine)
# ============================================================
def generate_image(prompt: str) -> str:
    print(f"🎨 Generating raw visual prompt: {prompt}...")
    out_path = f"output/raw_img_{int(time.time())}.png"

    if HF_TOKEN:
        try:
            print("🎨 [1/2] Rendering via Hugging Face (FLUX.1-schnell)...")
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=HF_TOKEN)
            img = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS).convert("RGB")
            img.save(out_path)
            print("✅ Visual generated via Hugging Face!")
            return out_path
        except Exception as e:
            print(f"⚠️ Hugging Face image failed: {e}")

    try:
        print("🎨 [2/2] Rendering via Pollinations AI...")
        url = f"https://gen.pollinations.ai/image/{requests.utils.quote(prompt)}?model=flux&width=1080&height=1920&nologo=true"
        headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"} if POLLINATIONS_API_KEY else {}
        res = requests.get(url, headers=headers, timeout=45)
        if res.status_code == 200 and len(res.content) > 5000:
            with open(out_path, "wb") as f:
                f.write(res.content)
            print("✅ Visual generated via Pollinations AI!")
            return out_path
    except Exception as e:
        print(f"⚠️ Pollinations failed: {e}")

    raise RuntimeError("All Image engines failed.")

# ============================================================
# TIER 4: MODERN CARD COMPOSITOR (Metadata Scrubbed)
# ============================================================
def build_modern_meme_canvas(bg_image_path: str, data: dict) -> str:
    print("🖌️ Compositing modern high-contrast social card...")
    base_img = Image.open(bg_image_path).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    
    vignette = Image.new("RGBA", (1080, 1920), (5, 5, 10, 90))
    canvas = Image.alpha_composite(base_img, vignette)

    card_w, card_h = 960, 580
    card_x = (1080 - card_w) // 2
    card_y = 220

    card_layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=32, fill=(15, 15, 22, 225), outline=(255, 255, 255, 35), width=2
    )
    canvas = Image.alpha_composite(canvas, card_layer).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    try:
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_hook = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_script = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_watermark = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font_tag = font_hook = font_script = font_watermark = ImageFont.load_default()

    draw.text((card_x + 40, card_y + 40), f"⚡ UNFILTERED HERO LOGS • {data.get('hero', 'HERO').upper()}", font=font_tag, fill="#FACC15")

    hook_lines = textwrap.wrap(data["hook"], width=38)
    cur_y = card_y + 100
    for line in hook_lines:
        draw.text((card_x + 40, cur_y), line, font=font_hook, fill="#FFFFFF")
        cur_y += 48

    cur_y += 15
    draw.line([(card_x + 40, cur_y), (card_x + card_w - 40, cur_y)], fill=(255, 255, 255, 40), width=1)
    cur_y += 25

    script_lines = textwrap.wrap(data["script"], width=42)
    for line in script_lines:
        draw.text((card_x + 40, cur_y), line, font=font_script, fill="#E2E8F0")
        cur_y += 42

    draw.text((540, 1820), IG_HANDLE, font=font_watermark, fill=(255, 255, 255, 180), anchor="mm")

    # ANTI-SPAM FIX: Extract raw image data to completely strip EXIF metadata
    out_card_path = f"output/card_{int(time.time())}.jpg"
    clean_canvas = Image.new(canvas.mode, canvas.size)
    clean_canvas.paste(canvas)
    clean_canvas.save(out_card_path, "JPEG", quality=98, exif=b"")
    return out_card_path

# ============================================================
# TIER 5: VIDEO ENGINE (Anti-Spam Motion & Audio Sync)
# ============================================================
def create_final_reel(canvas_path: str, audio_assets: dict) -> str:
    print("🎬 Rendering Master Reel (With Anti-Spam Motion & Randomized Pauses)...")
    from moviepy.editor import VideoClip, AudioFileClip, CompositeAudioClip
    import numpy as np
    from PIL import Image

    # 1. Randomized Audio Fingerprint Prevention
    hook_clip = AudioFileClip(audio_assets["hook"]).set_start(0)
    pause_length = random.uniform(0.8, 1.8) # Random gap prevents identical audio fingerprints
    script_clip = AudioFileClip(audio_assets["script"]).set_start(hook_clip.duration + pause_length)
    
    final_audio = CompositeAudioClip([hook_clip, script_clip])
    duration = min(final_audio.duration + 1.2, 30.0)

    # 2. Dynamic Pixel Injector (Defeats the "Static Image" IG Filter)
    base_img_array = np.array(Image.open(canvas_path).convert("RGB"))

    def make_frame(t):
        frame = np.copy(base_img_array)
        progress_width = int(1080 * (t / duration))
        
        if progress_width > 0:
            # Adds a vibrant yellow tracking bar to the absolute bottom of the screen
            frame[-12:, :progress_width] = [250, 204, 21] 
            
        return frame

    clip = VideoClip(make_frame, duration=duration).set_audio(final_audio)
    reel_path = f"output/final_reel_{int(time.time())}.mp4"

    clip.write_videofile(
        reel_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="9000k",
        verbose=False,
        logger=None
    )
    print("✅ Anti-Spam Reel rendered successfully!")
    return reel_path

# ============================================================
# GITHUB RELEASES STORAGE & INSTAGRAM PUBLISHER
# ============================================================
def _gh_headers(): 
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}", 
        "Accept": "application/vnd.github+json", 
        "X-GitHub-Api-Version": "2022-11-28"
    }

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
    print("📱 Publishing Master Reel to Instagram...")
    asset_id = None
    try:
        media_url, asset_id = upload_public_media(media_path)
        payload = {
            "access_token": INSTAGRAM_ACCESS_TOKEN, 
            "caption": caption, 
            "media_type": "REELS", 
            "video_url": media_url
        }
        c_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media", data=payload).json()
        container_id = c_res.get("id")
        if not container_id: 
            print(f"❌ Container failed: {c_res}")
            return False

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
# MAIN WORKFLOW
# ============================================================
def run():
    print(f"📦 Bot version: {BOT_VERSION}")
    validate_environment()
    os.makedirs("output", exist_ok=True)
    
    # 1. Sharp Satirical Script
    data = generate_satirical_script()
    
    # 2. Voice (Split generation for timing)
    audio_assets = generate_audio(data)
    
    # 3. Cinematic Photography Image
    raw_img = generate_image(data["image_prompt"])
    
    # 4. Modern Dark-Mode Card UI (Metadata stripped)
    canvas_path = build_modern_meme_canvas(raw_img, data)
    
    # 5. Composite Anti-Spam High-Bitrate Reel
    reel_path = create_final_reel(canvas_path, audio_assets)

    if reel_path and post_to_instagram(reel_path, data["caption"]):
        print("\n🎉 MASTER COMEDY REEL PUBLISHED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
        
