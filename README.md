🦸‍♂️ Super Dumb Heroes Bot
An automated, serverless Python bot powered by GitHub Actions that generates sarcastic, parody Instagram Reels about superheroes (Marvel & DC) dealing with mundane, everyday struggles.
📌 Features
 * Script Generation: Generates short, punchy, sarcastic monologue scripts using free LLM endpoints via OpenRouter.
 * Realistic Voiceover: Generates natural narration using edge-tts (Microsoft Edge Neural Voices) with zero API costs.
 * AI Image Generation: Generates vertical (9:16) situational artwork via Pollinations.ai (Flux model).
 * Video Compositing: Automatically stitches audio and dynamic zoom/motion effects using moviepy and ffmpeg.
 * Zero-Cost Infrastructure: Runs completely on GitHub Actions on a daily cron schedule.
 * Direct Instagram Publishing: Uploads and publishes directly to Instagram Reels using the Meta Graph API.
🏗️ Architecture Pipeline
OpenRouter (Free LLM) ──► Generates Hook, Script & Visual Prompt
        │
        ├──► edge-tts (Voice) ──────► output/tts.mp3
        │
        └──► Pollinations.ai (Flux) ─► output/base_img.png
                     │
                     ▼
             MoviePy Compositor ─────► output/reel.mp4
                     │
                     ▼
          Instagram Graph API ───────► Published to @Super_dumb_heroes

📁 Repository Structure
super-dumb-heroes-bot/
├── .github/
│   └── workflows/
│       └── super_dumb_heroes.yml   # GitHub Actions automation workflow
├── output/                         # Temporary storage for media artifacts
├── poster.py                       # Main execution script
├── requirements.txt                # Python package dependencies
└── README.md                       # Documentation

⚙️ Prerequisites & API Keys
Before deploying, make sure to collect the following API keys and tokens:
| Secret Name | Description | Source / Free Tier |
|---|---|---|
| OPENROUTER_API_KEY | Powers LLM text generation (openrouter/free models) | OpenRouter |
| POLLINATIONS_API_KEY | Generates 1080x1920 base artwork via Flux | Pollinations AI |
| MAGIC_HOUR_API_KEY | Video generation & animation fallback | Magic Hour Developer Hub |
| INSTAGRAM_ACCESS_TOKEN | Long-lived user access token for Instagram Graph API | Meta for Developers |
| INSTAGRAM_USER_ID | Your Instagram Business/Creator account ID | Graph API Explorer / Meta Business Suite |
🚀 Setup & Installation
1. Create Repository
Create a new GitHub repository named super-dumb-heroes-bot and clone it locally:
git clone https://github.com/<your-username>/super-dumb-heroes-bot.git
cd super-dumb-heroes-bot

2. Configure GitHub Secrets
Navigate to your repository on GitHub:
 * Go to Settings > Secrets and variables > Actions.
 * Click New repository secret.
 * Add each of the 5 required secrets:
   * OPENROUTER_API_KEY
   * POLLINATIONS_API_KEY
   * MAGIC_HOUR_API_KEY
   * INSTAGRAM_ACCESS_TOKEN
   * INSTAGRAM_USER_ID
📄 Configuration Files
requirements.txt
openai>=1.0.0
requests>=2.31.0
moviepy==1.0.3
numpy
edge-tts
asyncio

.github/workflows/super_dumb_heroes.yml
name: Super Dumb Heroes Automation

on:
  schedule:
    - cron: '0 12 * * *'  # Runs once every day at 12:00 PM UTC
  workflow_dispatch:      # Allows manual trigger via GitHub Actions tab

jobs:
  post-reel:
    runs-on: ubuntu-latest
    timeout-minutes: 25

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Setup FFmpeg
        uses: FedericoCarboni/setup-ffmpeg@v3
        with:
          ffmpeg-version: release

      - name: Install System Dependencies
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y fonts-dejavu-core fonts-dejavu-extra imagemagick
          fc-cache -f -v

      - name: Install Python Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Super Dumb Heroes Bot
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          POLLINATIONS_API_KEY: ${{ secrets.POLLINATIONS_API_KEY }}
          MAGIC_HOUR_API_KEY: ${{ secrets.MAGIC_HOUR_API_KEY }}
          INSTAGRAM_ACCESS_TOKEN: ${{ secrets.INSTAGRAM_ACCESS_TOKEN }}
          INSTAGRAM_USER_ID: ${{ secrets.INSTAGRAM_USER_ID }}
        run: python -u poster.py

🧪 Local Testing
You can run the script locally to test generation and Instagram publishing:
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Export environment variables (Linux/macOS)
export OPENROUTER_API_KEY="your_openrouter_key"
export POLLINATIONS_API_KEY="your_pollinations_key"
export MAGIC_HOUR_API_KEY="your_magic_hour_key"
export INSTAGRAM_ACCESS_TOKEN="your_instagram_token"
export INSTAGRAM_USER_ID="your_instagram_user_id"

# 4. Run the script
python -u poster.py

🛠️ Maintenance & Troubleshooting
 * Instagram Media Upload Timeouts: Instagram video containers must finish processing before publishing. The script polls the container status for up to 200 seconds before timing out.
 * Token Expiration: Meta Long-Lived Access Tokens generally expire every 60 days. Ensure you refresh your token periodically using the Meta Graph API token exchange endpoint.
 * Temporary File Hosting: The bot temporarily uploads the generated MP4 to a public temporary host to allow Meta's servers to fetch the video file. If the hosting endpoint is unreachable, check network accessibility.
 * 
