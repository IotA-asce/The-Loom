# The Loom - Complete User Guide

> *Weaving infinite timelines from existing stories.*

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [The Interface](#the-interface)
4. [Core Workflows](#core-workflows)
5. [Advanced Features](#advanced-features)
6. [Keyboard Shortcuts](#keyboard-shortcuts)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

**The Loom** is a full-stack storytelling framework for branching narratives with AI-generated prose and manga. Whether you're creating visual novels, interactive fiction, or manga stories, The Loom provides the tools to:

- **Visualize** your story as a branching graph
- **Generate** AI prose that matches your style
- **Create** manga panels with consistent characters
- **Collaborate** in real-time with other writers
- **Analyze** tone, continuity, and narrative structure

### What You Can Build

| Project Type | Description |
|--------------|-------------|
| Visual Novels | Branching storylines with character art |
| Interactive Fiction | Text-based adventures with multiple endings |
| Manga/Comics | Panel sequences with AI-generated artwork |
| Story Bibles | Character databases with visual references |
| Fan Fiction | Alternate timelines from existing stories |

---

## Getting Started

### System Requirements

- **OS**: macOS, Linux, or Windows (with WSL)
- **Python**: 3.12 or higher
- **Node.js**: 18 or higher
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for installation, plus space for generated images

### Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/IotA-asce/The-Loom.git
cd The-Loom
```

#### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Set Up Frontend

```bash
cd ui
npm install
cd ..
```

#### Step 4: Configure API Keys

Create a `.env` file in the project root:

```bash
# Required: At least one LLM provider
export GEMINI_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional: For image generation
export STABILITY_API_KEY="your-stability-api-key"

# Optional: For production deployments
export JWT_SECRET="your-secret-key-for-jwt"
```

> 📸 **[Screenshot: Project folder structure after installation]**
> ```
> Place screenshot here showing:
> - The-Loom directory with .venv, ui/, core/, etc.
> - Terminal showing successful pip install
> ```

#### Step 5: Start the Application

Terminal 1 - Backend:
```bash
source .venv/bin/activate
python -m ui.api
```

Terminal 2 - Frontend:
```bash
cd ui
npm run dev
```

Open your browser to **http://localhost:5173**

> 📸 **[Screenshot: First launch showing the main interface]**
> ```
> Place screenshot here showing:
> - The Loom main window with empty graph canvas
> - Welcome modal/onboarding visible
> ```

---

## The Interface

### Main Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🧵 The Loom    [Toolbar: Read Write Art Search ...]            │  ← Header
├──────────┬──────────────────────────────────────┬───────────────┤
│          │                                      │               │
│  Sidebar │         Graph Canvas                 │   Panel       │
│  (Tabs)  │         (Visual Story Editor)        │   (Tools)     │
│          │                                      │               │
│ • Branches                                      │               │
│ • Metadata                                      │               │
│ • Import                                        │               │
│          │                                      │               │
├──────────┴──────────────────────────────────────┴───────────────┤
│  Status: Connected | Nodes: 0 | Edges: 0 | Last saved: Never   │  ← Status Bar
└─────────────────────────────────────────────────────────────────┘
```

> 📸 **[Screenshot: Annotated interface overview]**
> ```
> Place screenshot here with labels pointing to:
> - Header with toolbar buttons
> - Left sidebar with tab buttons
> - Center canvas area
> - Right panel (collapsed or showing a tool)
> - Status bar at bottom
> ```

### Header Toolbar

| Button | Function | Shortcut |
|--------|----------|----------|
| 📖 Read | Toggle reading mode | `Ctrl+R` |
| ✍️ Write | Open AI writer panel | - |
| 🎨 Art | Open AI artist panel | - |
| 🔎 Search | Semantic search | - |
| 🧠 Memory | Browse story memory | - |
| 🔮 What-If | Consequence simulator | - |
| 🎭 Tones | Tone analysis heatmap | - |
| ⚙️ Tuner | Adjust AI parameters | `Ctrl+T` |
| 🖼️ Dual View | Split text/graph view | `Ctrl+D` |
| 💾 Save | Create checkpoint | `Ctrl+S` |
| 🔍 Find | Search nodes by name | `Ctrl+F` |
| 🎓 Help | Start tutorial | - |

### The Graph Canvas

The canvas is where you build your story structure visually.

#### Node Types

| Type | Icon | Color | Purpose |
|------|------|-------|---------|
| Chapter | 📚 | Blue | Major story divisions |
| Scene | 🎬 | Green | Individual scenes |
| Beat | 🎵 | Orange | Story beats/moments |
| Dialogue | 💬 | Purple | Conversation nodes |

> 📸 **[Screenshot: Graph canvas with example nodes]**
> ```
> Place screenshot here showing:
> - 4-5 nodes of different types connected by edges
> - One node selected (highlighted)
> - Minimap in corner
> ```

#### Navigating the Canvas

- **Pan**: Click and drag on empty space
- **Zoom**: Hold `Ctrl` + scroll wheel, or use pinch gesture
- **Select Node**: Click on it
- **Edit Node**: Double-click or press `Enter`
- **Delete Node**: Select and press `Delete`
- **Move Node**: Drag the node

### Sidebar Tabs

#### Branches Tab
Shows your story's branching structure:

```
🌿 Branches
├── 📚 Chapter 1: The Beginning
│   ├── 🎬 Scene 1: Arrival
│   │   └── 🎵 Beat: First Contact
│   └── 🎬 Scene 2: The Warning
├── 📚 Chapter 2: The Choice ⭐ [CURRENT]
│   ├── 🎬 Scene 3: Left Path
│   └── 🎬 Scene 4: Right Path
└── 🔀 Alternate Timeline
    └── 🎬 What if they stayed?
```

> 📸 **[Screenshot: Branches tab expanded]**
> ```
> Place screenshot here showing:
> - Tree view of story branches
> - Current node highlighted
> - Recent nodes section below
> ```

#### Metadata Tab
Edit details for the selected node:

- **Title**: Node name
- **Description**: Summary of what happens
- **Characters**: Who appears in this scene
- **Location**: Where it takes place
- **Time**: When it happens
- **Tags**: Custom labels for organization

> 📸 **[Screenshot: Metadata tab with fields filled]**
> ```
> Place screenshot here showing:
> - Form fields for a selected node
> - Character selector dropdown
> - Tag input field
> ```

#### Import Tab
Import existing content:

- **Text Files**: .txt, .pdf, .epub
- **Manga/Comics**: .cbz, image folders (.webp, .png, .jpg)
- **Templates**: Pre-made story structures

> 📸 **[Screenshot: Import panel showing options]**
> ```
> Place screenshot here showing:
> - File upload area
> - Format selection buttons
> - Import progress indicator
> ```

---

## Core Workflows

### Workflow 1: Creating Your First Story

#### Step 1: Create a Root Node

1. Click anywhere on the canvas
2. Press `Ctrl+N` (or right-click → "Add Node")
3. Type: "Chapter 1: The Beginning"
4. Press Enter

> 📸 **[Screenshot: Creating first node]**
> ```
> Place screenshot here showing:
> - Node creation dialog
> - Text input with "Chapter 1: The Beginning"
> ```

#### Step 2: Add Story Beats

1. Select your chapter node
2. Press `Ctrl+N` to create a child node
3. Name it "Scene 1: Introduction"
4. Repeat to add more scenes
5. Connect them with edges (drag from node edge to another node)

> 📸 **[Screenshot: Connected story nodes]**
> ```
> Place screenshot here showing:
> - 3-4 connected nodes in sequence
> - Edge lines connecting them
> - One node currently selected
> ```

#### Step 3: Write Content

1. Select a scene node
2. Click the **✍️ Write** button
3. In the Writer Panel, enter your prompt:
   ```
   Write an introduction scene where the protagonist 
   discovers a mysterious letter on their doorstep.
   ```
4. Click **Generate**

> 📸 **[Screenshot: Writer panel with generation in progress]**
> ```
> Place screenshot here showing:
> - Writer panel open on right side
> - Prompt text entered
> - Generate button visible
> - Progress indicator spinning
> ```

#### Step 4: Review and Accept

The AI will generate text based on your context. Review it and:
- Click **✓ Accept** to save to the node
- Click **✗ Reject** to discard
- Click **🔄 Regenerate** to try again

### Workflow 2: Creating a Branching Narrative

#### Step 1: Identify Decision Point

Find or create a scene where the protagonist makes a choice.

#### Step 2: Create Branch Nodes

1. Select the decision scene
2. Create two child nodes:
   - "Choice A: Accept the Quest"
   - "Choice B: Refuse the Quest"

> 📸 **[Screenshot: Branching nodes from a decision]**
> ```
> Place screenshot here showing:
> - One parent node splitting into two branches
> - Different colors or labels showing the choice paths
> ```

#### Step 3: Develop Each Branch

For each branch:
1. Add child scenes showing the consequences
2. Use **🔮 What-If Simulator** to explore outcomes
3. Mark canonical vs. alternate timelines

#### Step 4: Merge Branches (Optional)

If branches should reconverge:
1. Create a "Convergence" node
2. Add edges from both branches to it
3. Write content that works regardless of path taken

### Workflow 3: Importing Manga/Comics

The Loom can import manga and comics from image folders, making them available to read in the built-in viewer and link to your story graph.

#### Method A: CLI Import (Recommended)

**Step 1: Prepare Your Files**

Organize your manga images in a folder with zero-padded numbers:
```
My_Manga_Vol1/
├── 001.webp
├── 002.webp
├── 003.webp
└── ...
```

**Why zero-padding?** Files sort alphabetically, so `10.webp` would come before `2.webp`. Using `001.webp`, `002.webp` ensures correct page order.

**Step 2: Run the Import Script**

Open your terminal and run:
```bash
# Navigate to The Loom folder
cd /path/to/The-Loom

# Activate the virtual environment
source .venv/bin/activate  # Mac/Linux
# or: .venv\Scripts\activate  # Windows

# Import the manga
python scripts/import_manga_folder.py \
  "/path/to/My_Manga_Vol1" \
  "My Manga Volume 1"
```

**Step 3: Wait for Processing**

The script will:
- Scan and sort all image files
- Analyze each page (dimensions, format)
- Extract text via OCR (for searchability)
- Create a manga volume record
- Create a graph node (so it appears in your story graph)

For large volumes (500+ pages), this may take 2-5 minutes.

**Step 4: View in the App**

1. Open http://localhost:5173
2. Click the **📥 Import** tab
3. Scroll to **📚 Imported Manga**
4. Click **👁️ View** to start reading!

> 📸 **[Screenshot: CLI import running]**
> ```
> Place screenshot here showing:
> - Terminal with import command
> - Progress output showing pages being processed
> ```

#### Method B: Web UI Import (CBZ Files)

For CBZ (Comic Book ZIP) archives:

1. Open The Loom in your browser
2. Click **Import** tab in sidebar
3. Drag and drop your `.cbz` file onto the drop zone
4. Wait for import to complete

#### Method C: API Upload (Advanced)

For programmatic access or scripts:

```bash
curl -X POST "http://localhost:8000/api/ingest/manga/pages?title=My%20Manga" \
  -F "files=@page_001.webp" \
  -F "files=@page_002.webp"
```

#### Reading Imported Manga

Once imported, manga appears in two places:

**In the Import Tab:**
- Shows all imported volumes
- Click **👁️ View** to open the reader
- Click **📝 Go to Node** to find it in the graph

**In the Story Graph:**
- Manga nodes have a 📖 book icon
- Pink color distinguishes them from other nodes
- Click the node, then **📖 View Manga** in the right panel

> 📸 **[Screenshot: Manga viewer]**
> ```
> Place screenshot here showing:
> - Manga viewer with page displayed
> - Thumbnail sidebar visible
> - Navigation controls at bottom
> ```

#### Manga Viewer Features

| Feature | How to Use |
|---------|------------|
| Navigate pages | `←` / `→` arrow keys, or on-screen buttons |
| Jump to page | Type page number in the footer input |
| Zoom | `+` / `-` keys, or double-click image |
| Fullscreen | `F` key, or fullscreen button |
| Thumbnails | `T` key to toggle thumbnail sidebar |
| Close | `Escape` key, or ✕ button |

See [MANGA_WORKFLOW_COMPLETE.md](MANGA_WORKFLOW_COMPLETE.md) for detailed troubleshooting and advanced options.

### Workflow 4: Generating Manga Panels

#### Step 1: Create Scene Blueprint

1. Open the **🎨 Art** panel
2. Click **Blueprint** tab
3. Fill in the scene details:
   ```
   Setting: Medieval castle courtyard
   Time of Day: Sunset
   Weather: Clear, golden hour
   Key Elements: Fountain, rose bushes, stone archway
   ```

> 📸 **[Screenshot: Artist panel blueprint tab]**
> ```
> Place screenshot here showing:
> - Blueprint form with fields filled
> - Preview/thumbnail area
> ```

#### Step 2: Configure Atmosphere

Choose an atmosphere preset:
- **Light/Wholesome**: Bright, optimistic
- **Neutral/Dramatic**: Cinematic balance
- **Dark/Moody**: Mysterious, low-key
- **Horror**: Harsh, unsettling

Adjust lighting direction, intensity, and contrast.

> 📸 **[Screenshot: Atmosphere settings]**
> ```
> Place screenshot here showing:
> - Atmosphere preset buttons
> - Lighting controls (sliders)
> - Preview of lighting effect
> ```

#### Step 3: Generate Panels

1. Set number of panels (1-8)
2. Choose aspect ratio (9:16 for phone, 4:3 for print)
3. Click **Generate Panels**
4. Wait for generation (30-120 seconds)

> 📸 **[Screenshot: Generated panels grid]**
> ```
> Place screenshot here showing:
> - Grid of 4 generated manga panels
> - Each panel with number overlay
> - Accept/Reject buttons below each
> ```

#### Step 4: Review and Refine

For each panel:
- **Accept**: Keep and attach to scene
- **Reject**: Discard
- **Regenerate**: Try again with same prompt
- **Edit**: Adjust prompt for that specific panel

### Workflow 5: Character Consistency with LoRA

#### Step 1: Collect Reference Images

Gather 10-20 images of your character:
- Different angles
- Various expressions
- Consistent outfit/design

#### Step 2: Train LoRA

```python
from core.lora_training import CharacterLoRATrainer

trainer = CharacterLoRATrainer()
job = await trainer.start_training(
    character_name="Aria",
    reference_images=["aria_01.png", "aria_02.png", ...],
    style_preset="anime",
    training_steps=1000
)
```

Or use the UI:
1. Open **🎭 Characters** gallery
2. Click **+ New Character**
3. Upload reference images
4. Click **Train LoRA**

> 📸 **[Screenshot: Character training interface]**
> ```
> Place screenshot here showing:
> - Character gallery with uploaded references
> - Training progress bar
> - Preview of training samples
> ```

#### Step 3: Use in Generation

When generating panels:
1. Select your character from dropdown
2. The LoRA will be automatically applied
3. Generated images will maintain character consistency

### Workflow 6: Collaborative Writing

#### Step 1: Start Collaboration Session

1. Click your profile icon
2. Select **Start Collaboration Session**
3. Share the room ID with collaborators

#### Step 2: Invite Team Members

```python
from core.collaboration import get_collaboration_engine

engine = get_collaboration_engine()
await engine.invite_user(
    room_id="story-room-123",
    email="collaborator@example.com",
    role="editor"
)
```

Or share the room link:
```
http://localhost:5173/collaborate/story-room-123
```

> 📸 **[Screenshot: Collaboration session active]**
> ```
> Place screenshot here showing:
> - Multiple cursors visible (different colors)
> - User avatars in corner
> - Presence indicators on nodes
> ```

#### Step 3: Real-Time Editing

- See other users' cursors in real-time
- Nodes show who's currently editing them
- Lock nodes to prevent conflicts
- See change history in the timeline

#### Step 4: Resolve Conflicts

If two users edit simultaneously:
1. The system highlights conflicting changes
2. Review both versions side-by-side
3. Choose which to keep or merge manually

### Workflow 7: Semantic Search

#### Step 1: Index Your Story

The story is automatically indexed as you work. For imported content:
1. Go to **🔎 Search** panel
2. Click **Re-index Story**
3. Wait for processing

#### Step 2: Natural Language Search

Search using natural language:
```
"scenes where the protagonist feels betrayed"
"moments with romantic tension"
"descriptions of the castle interior"
```

> 📸 **[Screenshot: Search results]**
> ```
> Place screenshot here showing:
> - Search query entered
> - Results list with relevance scores
> - Preview snippets from matching nodes
> ```

#### Step 3: Navigate Results

Click any result to:
- Jump to that node in the graph
- See surrounding context
- Add to current working context

---

## Advanced Features

### Tone Analysis Heatmap

Visualize emotional tone across your story:

1. Click **🎭 Tones** in toolbar
2. See color-coded nodes by emotional valence:
   - 🔴 Red: Negative/Conflict
   - 🟡 Yellow: Neutral/Tension
   - 🟢 Green: Positive/Resolution
   - 🔵 Blue: Melancholic/Reflective

3. Identify tone inconsistencies
4. Balance your narrative arc

> 📸 **[Screenshot: Tone heatmap view]**
> ```
> Place screenshot here showing:
> - Graph with nodes colored by tone
> - Legend explaining colors
> - Tone curve graph on side
> ```

### Consequence Simulator

Test "what if" scenarios:

1. Click **🔮 What-If** in toolbar
2. Select a decision node
3. Choose alternative outcome
4. See projected consequences:
   - Affected downstream nodes
   - Character relationship changes
   - Plot consistency warnings

> 📸 **[Screenshot: Consequence simulator]**
> ```
> Place screenshot here showing:
> - Decision node selected
> - Alternative branches shown
> - Impact analysis panel
> ```

### Memory Browser

Navigate your story's memory hierarchy:

```
🧠 Memory Browser
├── Characters
│   ├── Protagonist
│   │   ├── Physical Description
│   │   ├── Personality Traits
│   │   └── Relationship Web
│   └── Supporting Cast
├── Locations
│   ├── Primary Settings
│   └── Secondary Locations
├── Events
│   ├── Major Plot Points
│   └── Recurring Motifs
└── Items
    ├── McGuffins
    └── Significant Objects
```

> 📸 **[Screenshot: Memory browser panel]**
> ```
> Place screenshot here showing:
> - Tree structure of story memory
> - Character profile expanded
> - Relationship web visualization
> ```

### Quality Control Dashboard

Review AI-generated content:

1. Click **🔍 QC** in toolbar
2. Review pending items:
   - Generated text awaiting approval
   - Images with quality warnings
   - Continuity issues detected
   - Style consistency scores

3. Batch accept/reject or review individually

> 📸 **[Screenshot: QC Dashboard]**
> ```
> Place screenshot here showing:
> - List of items needing review
> - Quality scores for generated content
> - Accept/Reject/Edit buttons
> ```

### Operations Dashboard

Monitor system health:

1. Click **🔧 Ops** in toolbar
2. View metrics:
   - Generation queue status
   - API rate limits
   - Storage usage
   - Error rates
   - SLO compliance

> 📸 **[Screenshot: Operations dashboard]**
> ```
> Place screenshot here showing:
> - Charts of generation activity
> - Queue depth over time
> - API usage gauges
> ```

---

## Keyboard Shortcuts

### Navigation

| Shortcut | Action |
|----------|--------|
| `↑` `↓` `←` `→` | Navigate between nodes |
| `Enter` | Edit selected node |
| `Delete` | Delete selected node |
| `Escape` | Cancel / Close panel |
| `Ctrl+F` | Find node |
| `Alt+←` | Navigate back in history |
| `Alt+→` | Navigate forward |

### Creation & Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | Create new node |
| `Ctrl+S` | Save checkpoint |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+T` | Toggle tuner panel |
| `Ctrl+D` | Toggle dual view |
| `Ctrl+R` | Toggle reading mode |
| `Ctrl+H` | Restart tutorial |
| `Ctrl+?` | Show shortcuts help |

### View Controls

| Shortcut | Action |
|----------|--------|
| `Ctrl+Scroll` | Zoom in/out |
| `Ctrl+0` | Reset zoom |
| `Space+Drag` | Pan canvas |
| `Tab` | Cycle through nodes |

> 📸 **[Screenshot: Keyboard shortcuts modal]**
> ```
> Place screenshot here showing:
> - Shortcuts help modal open
> - Categorized list of shortcuts
> - Search/filter functionality
> ```

---

## Troubleshooting

### Common Issues

#### "No supported image files found" (Import)

**Problem**: Importing folder shows no files found.

**Solutions**:
1. Check file extensions are lowercase (`.webp` not `.WEBP`)
2. Verify supported formats: `.webp`, `.png`, `.jpg`, `.jpeg`
3. Ensure files are directly in folder, not nested subfolders

#### Pages Import in Wrong Order

**Problem**: Manga pages appear out of sequence.

**Solution**: Use zero-padded numbers:
```
✅ Good: 001.webp, 002.webp, ..., 010.webp
❌ Bad:  1.webp, 2.webp, ..., 10.webp
```

#### Generation Times Out

**Problem**: AI generation stops with timeout error.

**Solutions**:
1. Reduce context window size
2. Lower max token count
3. Check API provider status
4. For local models, verify GPU is being used

#### "Cannot connect to backend"

**Problem**: UI shows connection errors.

**Solutions**:
1. Verify backend is running: `python -m ui.api`
2. Check port 8000 is available
3. Look for firewall blocking connections
4. Check logs for startup errors

#### Character Inconsistency in Images

**Problem**: Generated character looks different between panels.

**Solutions**:
1. Train a LoRA for the character
2. Use consistent descriptive prompts
3. Enable continuity checking
4. Increase reference image count

#### Collaboration Sync Issues

**Problem**: Changes not appearing for other users.

**Solutions**:
1. Check WebSocket connection (look for indicator in status bar)
2. Refresh the page to reconnect
3. Verify all users are in same room
4. Check for conflicting edit locks

### Performance Tips

#### For Large Stories (1000+ nodes)

1. **Enable lazy loading**: Settings → Performance → Lazy Load Nodes
2. **Use minimap**: Navigate via minimap instead of panning
3. **Collapse branches**: Hide completed storylines
4. **Regular checkpoints**: Save every 30 minutes

#### For Faster Generation

1. **Use "Fast" model preset** for drafts
2. **Reduce context window** to essential only
3. **Batch generate**: Queue multiple generations
4. **Local GPU**: Use local SD instead of API for images

#### For Better Image Quality

1. **Use Quality preset** for final images
2. **Train LoRAs** for main characters
3. **Increase sampling steps** (25-50)
4. **Use higher resolution** (1024x1024 or larger)

### Getting Help

- **GitHub Issues**: [github.com/IotA-asce/The-Loom/issues](https://github.com/IotA-asce/The-Loom/issues)
- **API Documentation**: http://localhost:8000/docs (when running)
- **Logs**: Check `logs/` directory for detailed error logs
- **Community**: GitHub Discussions for questions

---

## Quick Reference Card

### Starting Up
```bash
# Terminal 1
source .venv/bin/activate
python -m ui.api

# Terminal 2
cd ui && npm run dev

# Open http://localhost:5173
```

### Daily Workflow
1. **Start** the application
2. **Load** your story or create new
3. **Navigate** graph with arrow keys
4. **Edit** nodes (Enter) or create new (Ctrl+N)
5. **Generate** content with Write/Art panels
6. **Save** regularly (Ctrl+S)

### Emergency Shortcuts
- `Ctrl+S` - Save immediately
- `Escape` - Close any panel/modal
- `Ctrl+Z` - Undo mistake
- `Ctrl+?` - Get help

---

## Appendix A: File Formats

### Supported Import Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Plain Text | .txt | UTF-8 encoding |
| Markdown | .md | Preserves formatting |
| EPUB | .epub | Extracts chapters |
| PDF | .pdf | Text extraction |
| CBZ | .cbz | Comic book archive |
| WebP | .webp | Preferred image format |
| PNG | .png | Lossless images |
| JPEG | .jpg/.jpeg | Compressed images |

### Export Formats

| Format | Use Case |
|--------|----------|
| JSON | Full graph backup |
| Markdown | Readable story export |
| EPUB | E-book creation |
| CBZ | Manga/comic export |
| PDF | Print-ready output |

---

## Appendix B: API Quick Reference

### Key Endpoints

```bash
# Ingest text
curl -X POST http://localhost:8000/api/ingest/text \
  -F "file=@story.txt"

# Generate text
curl -X POST http://localhost:8000/api/writer/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a scene...", "context": [...]}'

# Generate image
curl -X POST http://localhost:8000/api/artist/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A castle at sunset...", "width": 1024, "height": 1024}'

# Search
curl "http://localhost:8000/api/search?q=romantic+scenes"

# Graph operations
curl http://localhost:8000/api/graph/nodes
curl -X POST http://localhost:8000/api/graph/nodes \
  -d '{"label": "New Scene", "type": "scene"}'
```

---

*Happy weaving! 🧵*

For updates and community, visit: [github.com/IotA-asce/The-Loom](https://github.com/IotA-asce/The-Loom)
