# -*- coding: utf-8 -*-
"""
Super Dumb Heroes / Meme Bot v6.0 (Comedy & Aesthetic Overhaul)
- Writing Engine: Satirical, hyper-specific deadpan humor prompts with few-shot examples
- Voice Engine: ElevenLabs (Primary) -> Dry Sarcastic British Edge-TTS (Fallback)
- Visuals: Modern dark-mode translucent meme card with clean typography (No 2012 Impact font)
- Media Host: GitHub Releases Cache
"""
BOT_VERSION = "v6.0"

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

- Example 3:
  Hook: "Professor X claims he can read any mind on planet Earth..."
  Script: "Which means he spends 80 percent of his day involuntarily listening to random men debating if they could beat a chimpanzee in a fistfight."
  Prompt: "Raw photo of Professor X sitting in a wheelchair rubbing his temples in intense annoyance in a dimly lit office, hyper-realistic"

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
# TIER 2: HIGH-END VOICE ENGINE (ElevenLabs -> Sarcastic Edge-TTS)
# ============================================================
def generate_audio(data: dict) -> dict:
    print("🎙️ Generating high-fidelity voiceover...")
    full_text = f"{data['hook']} ... ... {data['script']}"
    out_path = f"output/voice_{int(time.time())}.mp3"

    # Tier 1: ElevenLabs (Deep, Realistic Deadpan)
    if ELEVENLABS_API_KEY:
        try:
            print("🎙️ [TTS 1/2] Generating via ElevenLabs (Adam/Deep Deadpan)...")
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings

            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio_stream = client.text_to_speech.convert(
                text=full_text,
                voice_id="pNInz6obpgDQGcFmaJgB", # Adam (clean, deadpan masculine voice)
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                voice_settings=VoiceSettings(stability=0.68, similarity_boost=0.80, style=0.0, speed=0.92)
            )
            with open(out_path, "wb") as f:
                for chunk in audio_stream:
                    if chunk: f.write(chunk)
            print("✅ ElevenLabs Voice generated successfully!")
            return {"voice_path": out_path}
        except Exception as e:
            print(f"⚠️ ElevenLabs failed ({e}). Falling back to Edge-TTS...")

    # Tier 2: Edge-TTS (Dry British Narrative Tone)
    try:
        print("🎙️ [TTS 2/2] Generating via Edge-TTS (Sarcastic British Delivery)...")
        import edge_tts
        async def _speak():
            # en-GB-RyanNeural provides a drier, documentary-style sarcastic delivery
            communicate = edge_tts.Communicate(full_text, "en-GB-RyanNeural", rate="-8%", pitch="-4Hz")
            await communicate.save(out_path)
        asyncio.run(_speak())
        print("✅ Edge-TTS Voice generated successfully!")
        return {"voice_path": out_path}
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: IMAGE GENERATION (Photorealistic FLUX Engine)
# ============================================================
def generate_image(prompt: str) -> str:
    print(f"🎨 Generating raw visual prompt: {prompt}...")
    out_path = f"output/raw_img_{int(time.time())}.png"

    # 1. Try Hugging Face FLUX
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

    # 2. Fallback to Pollinations AI
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
# TIER 4: MODERN CARD COMPOSITOR (Clean Dark-Mode UI)
# ============================================================
def build_modern_meme_canvas(bg_image_path: str, data: dict) -> str:
    """Composites a sleek, modern translucent card overlay instead of 2012 Impact font."""
    print("🖌️ Compositing modern high-contrast social card...")
    base_img = Image.open(bg_image_path).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    
    # Slight cinematic vignette/darkening on the background
    vignette = Image.new("RGBA", (1080, 1920), (5, 5, 10, 90))
    canvas = Image.alpha_composite(base_img, vignette)

    # Card dimensions
    card_w, card_h = 960, 580
    card_x = (1080 - card_w) // 2
    card_y = 220

    # Draw rounded translucent dark card
    card_layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=32,
        fill=(15, 15, 22, 225),
        outline=(255, 255, 255, 35),
        width=2
    )
    canvas = Image.alpha_composite(canvas, card_layer).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Load fonts
    try:
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_hook = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_script = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_watermark = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font_tag = font_hook = font_script = font_watermark = ImageFont.load_default()

    # Draw Meta header in card
    draw.text((card_x + 40, card_y + 40), f"⚡ UNFILTERED HERO LOGS • {data.get('hero', 'HERO').upper()}", font=font_tag, fill="#FACC15")

    # Draw Hook (Bold Setup)
    hook_lines = textwrap.wrap(data["hook"], width=38)
    cur_y = card_y + 100
    for line in hook_lines:
        draw.text((card_x + 40, cur_y), line, font=font_hook, fill="#FFFFFF")
        cur_y += 48

    # Divider line inside card
    cur_y += 15
    draw.line([(card_x + 40, cur_y), (card_x + card_w - 40, cur_y)], fill=(255, 255, 255, 40), width=1)
    cur_y += 25

    # Draw Script (Punchline)
    script_lines = textwrap.wrap(data["script"], width=42)
    for line in script_lines:
        draw.text((card_x + 40, cur_y), line, font=font_script, fill="#E2E8F0")
        cur_y += 42

    # Bottom Handle Watermark
    draw.text((540, 1820), IG_HANDLE, font=font_watermark, fill=(255, 255, 255, 180), anchor="mm")

    out_card_path = f"output/card_{int(time.time())}.jpg"
    canvas.save(out_card_path, "JPEG", quality=98)
    return out_card_path

def create_final_reel(canvas_path: str, audio_path: str) -> str:
    print("🎬 Rendering Master 1080x1920 Reel...")
    from moviepy.editor import ImageClip, AudioFileClip

    voice = AudioFileClip(audio_path)
    duration = min(voice.duration + 1.2, 30.0)

    clip = ImageClip(canvas_path).set_duration(duration).set_audio(voice)
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
    print("✅ High-bitrate Reel rendered successfully!")
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
    
    # 2. Voice (ElevenLabs / Sarcastic British Edge-TTS)
    audio_data = generate_audio(data)
    
    # 3. Cinematic Photography Image
    raw_img = generate_image(data["image_prompt"])
    
    # 4. Modern Dark-Mode Card UI
    canvas_path = build_modern_meme_canvas(raw_img, data)
    
    # 5. Composite High-Bitrate Reel
    reel_path = create_final_reel(canvas_path, audio_data["voice_path"])

    if reel_path and post_to_instagram(reel_path, data["caption"]):
        print("\n🎉 MASTER COMEDY REEL PUBLISHED SUCCESSFULLY!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
                  
