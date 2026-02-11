# The Loom - Quick Start Guide

Get up and running with The Loom in 5 minutes.

---

## ⚡ 5-Minute Setup

### 1. Install (2 minutes)

```bash
# Clone repo
git clone https://github.com/IotA-asce/The-Loom.git
cd The-Loom

# Python setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ui && npm install && cd ..
```

### 2. Configure (1 minute)

```bash
# Set API key (choose one)
export GEMINI_API_KEY="your-key"      # Recommended
export OPENAI_API_KEY="your-key"      # Alternative
export ANTHROPIC_API_KEY="your-key"   # Alternative
```

### 3. Launch (2 minutes)

```bash
# Terminal 1: Backend
source .venv/bin/activate
python -m ui.api

# Terminal 2: Frontend
cd ui
npm run dev
```

Open **http://localhost:5173**

---

## 🎯 Your First Story (10 minutes)

### Step 1: Create Structure

1. **Press `Ctrl+N`** to create your first node
2. Type: `Chapter 1: The Beginning`
3. **Press `Ctrl+N`** again to add a scene
4. Type: `Scene 1: The Discovery`
5. **Drag** from Chapter node to Scene node to connect them

### Step 2: Add Content

1. **Double-click** the Scene node (or press `Enter`)
2. Type your scene description:
   ```
   The protagonist finds a mysterious artifact 
   in the attic of their ancestral home.
   ```
3. **Press Escape** to save

### Step 3: Generate AI Content

1. **Select** your scene node
2. Click **✍️ Write** in toolbar
3. Enter prompt:
   ```
   Write 3 paragraphs describing the artifact 
   and the protagonist's reaction.
   ```
4. Click **Generate**
5. Click **✓ Accept** when satisfied

### Step 4: Create a Branch

1. **Select** the scene node
2. **Press `Ctrl+N`** twice
3. Name them:
   - `Choice A: Take the artifact`
   - `Choice B: Leave it behind`
4. **Connect** both to the original scene

---

## 📸 Generate Manga Panels

### Step 1: Create Blueprint

1. Click **🎨 Art** in toolbar
2. Fill in:
   ```
   Setting: Attic with dusty boxes and sunbeams
   Time: Late afternoon
   Key Elements: Ancient box, glowing artifact
   ```

### Step 2: Generate

1. Set **Panels**: 4
2. Click **Generate Panels**
3. Wait 30-60 seconds
4. Review and click **✓ Accept**

---

## 🔍 Key Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+N` | New node |
| `Enter` | Edit node |
| `Delete` | Delete node |
| `Ctrl+S` | Save |
| `Ctrl+Z` | Undo |
| `↑↓←→` | Navigate |
| `Ctrl+F` | Find |
| `Ctrl+?` | Help |

---

## 📚 Next Steps

- **Import existing story**: Drag .txt, .pdf, or .epub to Import tab
- **Collaborate**: Share your room ID from Profile menu
- **Search**: Use **🔎 Search** for natural language queries
- **Analyze**: Click **🎭 Tones** for emotional heatmap

---

## 🆘 Need Help?

- Full guide: `docs/USER_GUIDE.md`
- Manga import: `docs/MANGA_IMPORT.md`
- API docs: http://localhost:8000/docs
- Issues: github.com/IotA-asce/The-Loom/issues

---

*Happy weaving! 🧵*
