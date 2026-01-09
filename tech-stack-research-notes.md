# Tech Stack Video Series: Research Notes & Key Facts

## Quick Reference for Text Overlays & Scripts

---

## MAC STUDIO M3 ULTRA

### Verified Specifications
- **Chip:** Apple M3 Ultra (two M3 Max fused via UltraFusion)
- **CPU:** 32-core (24 performance + 8 efficiency)
- **GPU:** Up to 80-core
- **Neural Engine:** 32-core
- **Memory:** Up to 512GB unified LPDDR5x
- **Memory Bandwidth:** 819 GB/s
- **Storage:** Up to 16TB SSD
- **Connectivity:** Thunderbolt 5 (5 ports, 120 Gb/s each)
- **OS:** macOS Tahoe 26.2

### Key Capabilities (Research-Backed)
- Runs DeepSeek R1 671B parameters locally (4-bit quantized)
- 17-18 tokens/second on massive models
- Consumes ~404GB for 671B model, requires ~448GB VRAM allocation
- 16.9x faster token generation vs M1 Ultra (per Apple)
- Power consumption: Under 200W at full LLM load
- RDMA over Thunderbolt 5 enables clustering (latency < 50μs)
- Can cluster 4+ Mac Studios for distributed inference

### Value Propositions
- "First desktop to run 600B+ parameter models in memory"
- "Complete data privacy - models never leave your hardware"
- "4x efficiency advantage vs comparable GPU clusters"
- "Silent operation - whisper-quiet under load"

### Cost Context
- 512GB configuration: ~$9,499-$10,000
- Comparable NVIDIA setup would cost significantly more + higher power

---

## NVIDIA DGX SPARK

### Verified Specifications
- **Chip:** NVIDIA GB10 Grace Blackwell Superchip
- **CPU:** 20-core ARM (10× Cortex-X925 + 10× Cortex-A725)
- **GPU:** Blackwell architecture, 6,144 CUDA cores
- **AI Performance:** Up to 1 PFLOP (FP4 with sparsity)
- **Memory:** 128GB unified LPDDR5x
- **Memory Bandwidth:** 273 GB/s
- **Networking:** Dual QSFP 200 Gb/s (ConnectX-7)
- **OS:** DGX OS (Ubuntu-based)
- **Form Factor:** Desktop (similar to Mac Mini size)
- **Power:** USB-C power delivery (up to 240W)

### Key Capabilities (Research-Backed)
- Run inference on models up to 200B parameters
- Fine-tune models up to 70B parameters
- Two units can cluster for 405B parameter models (FP4)
- Preloaded NVIDIA AI software stack
- NIM microservices ready out of box
- Works with FLUX.1, Cosmos, Qwen3 optimized

### Value Propositions
- "1 petaflop in a desktop form factor"
- "The democratization of AI supercomputing"
- "Full NVIDIA ecosystem - CUDA, NIM, libraries"
- "From prototype to production on your desk"

### Cost Context
- Retail price: $3,999
- Named TIME Best Inventions of 2025
- Partners: Acer, ASUS, Dell, GIGABYTE, HP, Lenovo, MSI

---

## CLAUDE CODE

### Latest Capabilities (Dec 2025)
- **Market Position:** 54% of AI coding market share
- **Revenue:** $1 billion run-rate (achieved in 6 months)
- **Enterprise:** 30,000 Accenture professionals being trained
- **Acquisition:** Anthropic acquired Bun (JavaScript runtime)

### Key Features
- **Checkpoints:** Save progress, roll back instantly
- **LSP Integration:** Real-time diagnostics, go-to definition, references
- **Async Sub-Agents:** Parallel task execution, multitasking
- **Ultrathink Mode:** Advanced reasoning for complex problems
- **Context Window Tracking:** Real-time progress bar, /stats command
- **VS Code Extension:** Native integration
- **Slack Integration:** Handover capability
- **Chrome Integration:** /chrome command for testing
- **AutoCloud GUI:** Task management interface
- **Mobile Support:** Android app for task management

### Enterprise Features
- Works in terminal (not another IDE)
- GitHub integration
- MCP (Model Context Protocol) support
- Can use web search, Google Drive, Figma, Slack
- Enterprise-grade security built-in

### Model Options
- Claude Opus 4.5 (flagship)
- Claude Sonnet 4.5 (77.2% SWE-bench, best coding model)
- Claude Haiku 4.5 (fastest, most efficient)

### Value Propositions
- "Build features from descriptions"
- "Debug and fix issues from error messages"
- "Navigate any codebase with full context"
- "Automate tedious tasks in single commands"

---

## GEMINI ULTRA SUBSCRIPTION

### Subscription Details
- **Price:** $249.99/month (US)
- **Storage:** 30TB Google Photos/Drive/Gmail
- **Includes:** YouTube Premium individual plan

### Gemini 3 Pro
- LMArena Leaderboard score: 1501 Elo (breakthrough)
- Humanity's Last Exam: 37.5% (no tools)
- GPQA Diamond: 91.9% (PhD-level reasoning)
- MathArena Apex: 23.4% (state-of-the-art math)
- MMMU-Pro: 81% (multimodal reasoning)
- Video-MMMU: 87.6%
- SimpleQA Verified: 72.1% (factual accuracy)
- 200K token context window
- 64K output tokens

### Gemini 3 Deep Think
- Humanity's Last Exam: 41.0% (enhanced reasoning)
- GPQA Diamond: 93.8%
- Currently in safety testing for Ultra subscribers

### Google Antigravity
- Agentic development platform
- Highest rate limits with Ultra
- Access to Gemini 3 Pro + Claude Sonnet 4.5 + GPT-OSS
- Quotas refresh every 5 hours
- Desktop app for Windows, macOS, Linux
- "Reimagines developer experience at task-oriented level"

### Flow (AI Filmmaking)
- Text to video
- Ingredients to video
- Frames to video
- 1080p generation
- Advanced camera controls
- Veo 3.1 access

### Whisk
- Image-to-video creation
- Veo 3 powered
- 8-second video generation

### Jules (AI Coding Agent)
- 20x higher limits vs Pro
- Highest concurrency limits
- Priority model access
- GitHub integration
- "For intensive, multi-agent workflows at scale"

### Project Mariner
- Agentic browser research prototype
- 10 simultaneous tasks
- Research, shopping, booking

### Value Propositions
- "VIP pass to Google AI"
- "Highest access to most capable models"
- "Professional-grade AI filmmaking"
- "Agentic development at scale"

---

## NOTEBOOKLM

### Core Capabilities
- Upload up to 50 sources (free) / 300 sources (Plus)
- 500,000 words per source
- Supports: PDFs, Google Docs, Word, Sheets, URLs, YouTube, images
- Built on Gemini 3 (as of Dec 2025)

### Output Types
- **Audio Overviews:** Podcast-style summaries, 50+ languages
- **Video Overviews:** Visual explanations, 6 Nano Banana styles
- **Mind Maps:** Interactive topic navigation
- **Data Tables:** Structured information, export to Sheets
- **Flashcards:** Study aids from documents
- **Quizzes:** Auto-generated assessments
- **Reports:** Customized document generation (blog posts, etc.)
- **Infographics**
- **Slide Decks**
- **Learning Guides**

### Recent Features (Dec 2025)
- Deep Research integration
- Data Tables (export to Google Sheets)
- Upload to Gemini app capability
- Improved reasoning with Gemini 3

### Value Propositions
- "Your personal AI research partner"
- "Source-grounded - never hallucinates"
- "Citations link directly to source passages"
- "Turn information into knowledge"

---

## LM STUDIO

### Core Features
- Free desktop application (Windows, macOS, Linux)
- Polished GUI - no command line required
- Model browser with 1000+ preconfigured models
- Automatic hardware detection/optimization
- OpenAI-compatible API endpoints
- MCP Host support (as of 0.3.17)

### Technical Capabilities
- Multi-GPU controls (enable/disable, allocation strategies)
- Flash Attention support (CUDA, Vulkan, Metal)
- Vulkan offloading for Intel/AMD integrated GPUs
- Apple Silicon optimization (MLX)
- Model splitting (GPU + RAM)
- CUDA 12.8 acceleration
- DGX Spark native support (Linux ARM)

### Latest Updates (Dec 2025)
- 0.3.36: Google FunctionGemma support
- 0.3.35: Devstral-2, GLM-4.6V
- 0.3.34: EssentialAI rnj-1
- 0.3.33: Ministral 3, Olmo-3 tool calling
- 0.3.32: GLM 4.5 tool calling, olmOCR-2
- OpenAI gpt-oss-safeguard support (launch day)

### Supported Models
- GPT-OSS (20B, 120B)
- Qwen3 (4B, 30B, 235B)
- DeepSeek
- Llama 3
- Mistral/Ministral
- Gemma 3
- Devstral-2
- And 1000+ more from Hugging Face

### Value Propositions
- "Local AI on your computer"
- "Complete privacy - no data leaves your machine"
- "Free forever for personal and commercial use"
- "The most accessible local LLM tool"

---

## DAVINCI RESOLVE STUDIO 2.0

### AI Features
- Neural Engine for processing
- AI-powered color grading
- Face detection and tracking
- Object removal
- Speed warp (AI frame interpolation)
- Voice isolation
- Dialogue leveler
- AI-based stabilization
- Super scale (AI upscaling)

### Production Capabilities
- Full color grading suite
- Fusion visual effects
- Fairlight audio post
- Multi-cam editing
- ProRes/DNxHR support
- 8K timeline support
- HDR grading

### Integration Points
- Export presets for social media
- Scripting API (Lua, Python)
- Workflow integration possibilities

---

## HUGGING FACE

### Platform Capabilities
- Model Hub: 500,000+ models
- Datasets: 100,000+ datasets
- Spaces: Demo/app hosting
- Transformers library
- Inference API
- AutoTrain

### Integration Value
- Source for LM Studio models
- Fine-tuning workflows
- Community model discovery
- Version control for models

---

## HUBSPOT CRM

### AI-Enhanced Features
- Contact insights
- Predictive lead scoring
- Content assistant
- Email suggestions
- Conversation intelligence

### Integration Points
- API access for custom AI workflows
- Automation possibilities
- Data source for personalization

---

## QUICK STATS FOR OVERLAYS

### Hardware
- "1TB UNIFIED MEMORY (2× Mac Studio)"
- "160 GPU CORES COMBINED"
- "1 PETAFLOP AI COMPUTE"
- "200B PARAMETER MODELS LOCALLY"

### Claude Code
- "54% CODING MARKET SHARE"
- "$1B RUN-RATE IN 6 MONTHS"
- "30,000 ACCENTURE DEVS TRAINING"

### Gemini Ultra
- "1501 ELO - BREAKTHROUGH SCORE"
- "37.5% HUMANITY'S LAST EXAM"
- "91.9% GPQA DIAMOND"
- "30TB STORAGE INCLUDED"

### NotebookLM
- "300 SOURCES PER NOTEBOOK"
- "50+ LANGUAGES"
- "ZERO HALLUCINATION - SOURCE-GROUNDED"

### LM Studio
- "1000+ MODELS"
- "FREE FOREVER"
- "OPENAI-COMPATIBLE API"

---

*Research compiled January 2026*
*Sources: Official documentation, press releases, verified reviews*
