# 📖 Manga Workflow Guide - Complete End-to-End

> **For Non-Technical Users**: This guide explains how to import, manage, and read manga in The Loom without requiring programming knowledge.

---

## 🎯 What You Can Do

| Feature | Status | How to Access |
|---------|--------|---------------|
| Import manga from folders | ✅ Working | Command line (one simple command) |
| View imported manga list | ✅ Working | Import tab in the app |
| Read manga with viewer | ✅ Working | Click "View" button on any manga |
| Navigate between pages | ✅ Working | Arrow keys, on-screen buttons, or thumbnails |
| Zoom and fullscreen | ✅ Working | +/- keys, F key, or on-screen controls |
| Link to graph nodes | ✅ Working | Automatic on import |
| Delete manga | ✅ Working | Click trash icon in manga list |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Open Your Terminal

**Windows:**
1. Press `Win + R`
2. Type `cmd` and press Enter

**Mac:**
1. Press `Cmd + Space`
2. Type `terminal` and press Enter

**Linux:**
1. Press `Ctrl + Alt + T`

### Step 2: Run the Import Command

```bash
# Navigate to The Loom folder
cd /path/to/The-Loom

# Activate the environment (Windows)
.venv\Scripts\activate

# Activate the environment (Mac/Linux)
source .venv/bin/activate

# Import your manga
python scripts/import_manga_folder.py "/path/to/your/manga" "My Manga Title"
```

**Example:**
```bash
python scripts/import_manga_folder.py "/Users/me/Downloads/MyMangaVol1" "Dragon Quest Volume 1"
```

### Step 3: View in the App

1. Open The Loom in your browser (http://localhost:5173)
2. Click the **📥 Import** tab on the left
3. Scroll down to see **📚 Imported Manga**
4. Click the **👁️ View** button to start reading!

---

## 📁 Preparing Your Manga Files

### Folder Structure

Your manga folder should contain image files:

```
My_Manga_Volume_1/
├── 001.webp
├── 002.webp
├── 003.webp
├── ...
└── 200.webp
```

### Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| WebP | `.webp` | ✅ Best choice - small files, good quality |
| PNG | `.png` | ✅ Good quality, larger files |
| JPEG | `.jpg`, `.jpeg` | ✅ Smallest files, some quality loss |

### File Naming Tips

**✅ Good naming (pages will be in correct order):**
```
001.webp, 002.webp, 003.webp ... 010.webp, 011.webp
page_001.webp, page_002.webp ...
ch01_001.webp, ch01_002.webp ...
```

**❌ Avoid (pages may be out of order):**
```
1.webp, 2.webp, ... 10.webp, 11.webp  (10 will come before 2!)
page1.webp, page2.webp ...
```

> 💡 **Tip**: Use leading zeros! `001` instead of `1`

---

## 📚 Using the Manga Library

### Where to Find It

1. Click the **📥 Import** tab in the left sidebar
2. Scroll down past the file upload area
3. You'll see **📚 Imported Manga** with all your imported volumes

### What You See

```
┌─────────────────────────────────┐
│ 📚 Imported Manga          🔄   │
├─────────────────────────────────┤
│ 📖 Dragon Quest Volume 1        │
│    529 pages • Imported 2/10/25 │
│    📝 In graph                  │
│    [👁️] [📝] [🗑️]              │
├─────────────────────────────────┤
│ 📖 My Other Manga               │
│    45 pages • Imported 2/9/25   │
│    [👁️] [🗑️]                   │
└─────────────────────────────────┘
```

### Button Guide

| Button | What It Does |
|--------|--------------|
| 👁️ **View** | Opens the manga reader |
| 📝 **Go to Node** | Finds the manga in your story graph |
| 🗑️ **Delete** | Removes the manga (cannot be undone) |
| 🔄 **Refresh** | Updates the list if you just imported |

---

## 📖 Reading Manga

### Opening the Viewer

Click the **👁️ View** button on any manga in the library.

### Viewer Controls

```
┌─────────────────────────────────────────────────────┐
│ 📖 Title                    Page 5 of 200    ✕      │  ← Header
├─────────────────────────────────────────────────────┤
│ 📑 │                                                │
│    │         [Manga Page Image]                     │
│    │                                                │
│    │         ‹                          ›          │  ← Navigation
│    │                                                │
├─────────────────────────────────────────────────────┤
│ [−] 100% [+] [⟲]          [← Prev] [5/200] [Next →] │  ← Footer
└─────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `←` or `Page Up` | Previous page |
| `→` or `Page Down` or `Space` | Next page |
| `+` or `=` | Zoom in |
| `-` or `_` | Zoom out |
| `0` | Reset zoom to 100% |
| `F` | Fullscreen mode |
| `T` | Show/hide thumbnail sidebar |
| `Escape` | Close viewer |

### Using Thumbnails

- Click the **📑** button (or press `T`) to show thumbnails
- Click any thumbnail to jump to that page
- Useful for quickly finding a specific page

### Zoom Options

Click the fit mode button in the footer:
- **Fit Height**: Full page visible vertically (default)
- **Fit Width**: Full page width visible
- **Original**: 1:1 pixel size

---

## 🔗 Manga and Your Story Graph

### What Is a Graph Node?

When you import manga, it automatically creates a **node** in your story graph. This lets you:
- See manga as part of your story structure
- Connect manga to related story elements
- Click from the graph to view the manga

### Finding Manga in the Graph

**From the Library:**
1. Find your manga in the Imported Manga list
2. Click the **📝 Go to Node** button
3. The graph will center on your manga node

**From a Manga Node:**
1. Find the manga node in your graph (it has a 📖 book icon)
2. Click on it to select it
3. In the right panel, click **📖 View Manga** button

### Manga Node Appearance

```
┌─────────────┐
│     📖      │  ← Book icon
│ Manga Title │  ← Your title
│             │
│   (pink)    │  ← Manga nodes are pink
└─────────────┘
```

---

## 🛠️ Troubleshooting

### "No supported image files found"

**Problem:** The import script can't find your images.

**Solutions:**
1. Check file extensions are lowercase (`.webp` not `.WEBP`)
2. Make sure images are directly in the folder, not in subfolders
3. Verify the path you typed is correct

### Pages are in wrong order

**Problem:** Page 10 comes before page 2.

**Solution:** Rename files with leading zeros:
```bash
# Before (wrong):
1.webp, 2.webp, ..., 10.webp

# After (correct):
001.webp, 002.webp, ..., 010.webp
```

### Import is very slow

**Problem:** Large volumes (500+ pages) take a long time.

**What's happening:** The app is analyzing each page (OCR text extraction).

**Solutions:**
1. Wait patiently - it's working!
2. For 500+ pages, expect 2-5 minutes
3. The viewer will work immediately after import

### "Command not found: python"

**Problem:** Python isn't recognized.

**Solutions:**
- **Windows:** Use `py` instead of `python`
- **Mac/Linux:** Use `python3` instead of `python`

### Manga doesn't appear in the app

**Checklist:**
1. ✅ Is the backend running? (Terminal should show "Uvicorn running")
2. ✅ Did the import say "✅ Saved manga volume"?
3. ✅ Click the 🔄 refresh button in the Import tab
4. ✅ Check the database exists: look for `.loom/manga.db` file

### Viewer shows "Failed to load manga"

**Solutions:**
1. Check the backend is running
2. Try refreshing the manga list
3. The image files must still exist at their original location
4. Check browser console for error details (F12 → Console)

---

## 📊 Understanding the Import Report

After running the import command, you'll see:

```
==================================================
✅ Import successful!
==================================================
Pages imported: 529
Spreads detected: 3
Source hash: a3f7b2c8...

Page details:
  Page 1: webp, 1200x1800
  Page 2: webp, 1200x1800
  ...

💾 Saving to manga storage...
📝 Creating graph node...
✅ Created graph node: node_a1b2c3d4e5f6
✅ Saved manga volume: manga_x7y8z9w0a1b2
   Title: Dragon Quest Volume 1
   Pages: 529
   Graph Node: node_a1b2c3d4e5f6
   The manga is now available in the UI!
```

**What each line means:**

| Line | Meaning |
|------|---------|
| `Pages imported` | Total number of image files found |
| `Spreads detected` | Pages wider than tall (two-page spreads) |
| `Source hash` | Unique identifier for this manga |
| `Graph Node` | ID of the node created in your story graph |

---

## 🎓 Advanced: Command Options

### Dry Run (Preview Without Importing)

See what would be imported without actually doing it:

```bash
python scripts/import_manga_folder.py "/path/to/manga" "Title" --dry-run
```

### Don't Create Graph Node

Import manga without adding it to your story graph:

```bash
python scripts/import_manga_folder.py "/path/to/manga" "Title" --no-graph-node
```

### Custom Database Location

Store manga in a different location:

```bash
python scripts/import_manga_folder.py "/path/to/manga" "Title" --db-path "/custom/path/manga.db"
```

---

## 🔄 Workflow Summary

```
┌─────────────────┐
│ 1. PREPARE      │  Rename images with leading zeros
│    FILES        │  (001.webp, 002.webp, etc.)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. RUN IMPORT   │  python scripts/import_manga_folder.py
│    COMMAND      │     "/path" "Title"
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. OPEN APP     │  Go to http://localhost:5173
│                 │  Click Import tab
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. VIEW MANGA   │  Click 👁️ View button
│                 │  Read with keyboard shortcuts
└─────────────────┘
```

---

## ❓ Frequently Asked Questions

**Q: Do I need to keep the original image files?**
A: Yes! The Loom references the original files. Don't move or delete them after importing.

**Q: Can I import the same manga twice?**
A: The app will detect duplicates and skip them. You'll see "A manga with this content already exists."

**Q: What happens if I delete a manga from the library?**
A: It removes the entry from The Loom's database but doesn't delete your original image files.

**Q: Can I read manga on mobile?**
A: Yes! The viewer works on mobile browsers. Use touch gestures to navigate.

**Q: How do I update a manga after importing?**
A: Currently, re-importing will create a new entry. Delete the old one first if needed.

**Q: What's the maximum file size?**
A: Individual images can be up to 100MB. Volumes can have up to 10,000 pages.

**Q: Can I import CBZ files?**
A: Yes! Drag and drop CBZ files in the Import tab, or use the API directly.

---

## 📞 Getting Help

If something isn't working:

1. **Check this guide's Troubleshooting section** above
2. **Verify your setup:**
   - Backend running? (Terminal shows "Uvicorn")
   - Frontend running? (Terminal shows "Vite")
3. **Check the logs:** Look for error messages in the terminal
4. **File an issue:** github.com/IotA-asce/The-Loom/issues

---

*Happy reading! 📖✨*
