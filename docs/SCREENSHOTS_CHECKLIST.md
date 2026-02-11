# Screenshots Checklist for User Guide

This file lists all screenshots needed for `docs/USER_GUIDE.md`. Each item includes:
- Location in the guide
- Description of what to capture
- Suggested window size: 1440x900 or 1920x1080

---

## Getting Started Section

### 1. Project Folder Structure
- **Location**: After "Terminal showing successful pip install"
- **Capture**: 
  - Terminal showing completed `pip install`
  - Finder/Explorer showing The-Loom directory with: .venv, ui/, core/, agents/, etc.

### 2. First Launch
- **Location**: "First launch showing the main interface"
- **Capture**:
  - Browser at http://localhost:5173
  - Fresh empty canvas
  - Onboarding modal visible (if first run, or manually trigger)

---

## The Interface Section

### 3. Annotated Interface Overview
- **Location**: "Annotated interface overview"
- **Capture**:
  - Main app window with some example nodes loaded
  - Add annotation arrows/labels in image editor pointing to:
    - Header toolbar
    - Left sidebar tabs (Branches/Metadata/Import)
    - Graph canvas with nodes
    - Right panel area
    - Status bar

### 4. Graph Canvas Example
- **Location**: "Graph canvas with example nodes"
- **Capture**:
  - Canvas with 4-5 nodes of different types
  - Chapter (📚), Scene (🎬), Beat (🎵), Dialogue (💬)
  - One node selected (highlighted border)
  - Minimap visible in corner
  - Edges connecting nodes

### 5. Branches Tab Expanded
- **Location**: "Branches tab expanded"
- **Capture**:
  - Left sidebar showing Branches tab active
  - Tree view with nested structure:
    ```
    Chapter 1
    └── Scene 1
        └── Beat 1
    Chapter 2 [CURRENT]
    └── Scene 2
    ```
  - Recent nodes section below

### 6. Metadata Tab
- **Location**: "Metadata tab with fields filled"
- **Capture**:
  - Metadata tab active
  - A scene node selected
  - Form showing: Title, Description, Characters, Location, Tags
  - Character dropdown open showing options

### 7. Import Panel
- **Location**: "Import panel showing options"
- **Capture**:
  - Import tab active
  - Drag-and-drop zone visible
  - File type buttons (Text, Manga, Template)
  - Or show file browser dialog with files selected

---

## Core Workflows Section

### 8. Creating First Node
- **Location**: "Creating first node"
- **Capture**:
  - Node creation dialog/modal
  - Text input field with "Chapter 1: The Beginning"
  - Type dropdown showing "chapter" selected

### 9. Connected Story Nodes
- **Location**: "Connected story nodes"
- **Capture**:
  - 3-4 nodes in a sequence
  - Edge lines connecting parent to children
  - Second node selected
  - Clean layout

### 10. Writer Panel Generation
- **Location**: "Writer panel with generation in progress"
- **Capture**:
  - Right panel open showing Writer
  - Prompt text visible
  - Generate button
  - Progress indicator/spinner
  - Context chunks visible

### 11. Branching from Decision
- **Location**: "Branching nodes from a decision"
- **Capture**:
  - One parent node at top
  - Two child nodes branching below
  - Labels: "Accept" and "Refuse"
  - Different colors or connection styles

### 12. CLI Import Running
- **Location**: "CLI import running"
- **Capture**:
  - Terminal window
  - Command: `python scripts/import_manga_folder.py ...`
  - Progress output showing:
    ```
    Found 200 image files
    Processing page 001.webp...
    OCR: Extracted text...
    ```

### 13. UI Folder Import
- **Location**: "UI folder import"
- **Capture**:
  - Import tab active
  - Drag-and-drop zone highlighted (dragging state)
  - Or file picker dialog showing image files
  - Progress bar for upload

### 14. Artist Panel Blueprint
- **Location**: "Artist panel blueprint tab"
- **Capture**:
  - Art panel open
  - Blueprint tab active
  - Fields filled:
    - Setting: "Medieval castle courtyard"
    - Time of Day: "Sunset"
    - Weather: "Clear"
  - Preview placeholder or thumbnail

### 15. Atmosphere Settings
- **Location**: "Atmosphere settings"
- **Capture**:
  - Atmosphere tab in Art panel
  - Preset buttons: Light, Neutral, Dark, Horror
  - Lighting sliders visible
  - Preview showing lighting effect

### 16. Generated Panels Grid
- **Location**: "Generated panels grid"
- **Capture**:
  - Grid of 4 generated manga panels
  - Each with subtle number overlay (1, 2, 3, 4)
  - Accept/Reject buttons below each
  - Style: Anime/manga aesthetic

### 17. Character Training Interface
- **Location**: "Character training interface"
- **Capture**:
  - Character gallery open
  - Character profile "Aria" selected
  - Grid of reference images (10-12 thumbnails)
  - "Train LoRA" button
  - Progress bar at 45%

### 18. Collaboration Session
- **Location**: "Collaboration session active"
- **Capture**:
  - Main canvas with 2-3 cursor indicators (different colors)
  - User avatars in top-right corner
  - One node showing "Alice is editing..." indicator
  - Presence dots on nodes

### 19. Search Results
- **Location**: "Search results"
- **Capture**:
  - Search panel open
  - Query: "scenes where protagonist feels betrayed"
  - Results list with:
    - Node titles
    - Relevance scores (0.95, 0.87, etc.)
    - Text snippets
  - 5-6 results visible

---

## Advanced Features Section

### 20. Tone Heatmap
- **Location**: "Tone heatmap view"
- **Capture**:
  - Graph view with nodes colored:
    - Red nodes (conflict)
    - Green nodes (resolution)
    - Yellow nodes (tension)
  - Legend visible
  - Tone curve chart on side panel

### 21. Consequence Simulator
- **Location**: "Consequence simulator"
- **Capture**:
  - What-If panel open
  - Decision node "The Choice" selected
  - Alternative branches displayed
  - Impact analysis showing:
    - "3 downstream nodes affected"
    - "Character relationship: -10"

### 22. Memory Browser
- **Location**: "Memory browser panel"
- **Capture**:
  - Memory panel open
  - Tree structure expanded:
    - Characters
      - Protagonist (expanded)
        - Description
        - Relationships
  - Relationship web mini-visualization

### 23. QC Dashboard
- **Location**: "QC Dashboard"
- **Capture**:
  - QC panel open
  - List of items:
    - Generated text with quality score (85%)
    - Image with warning icon
    - Continuity issue flagged
  - Batch action buttons at top

### 24. Operations Dashboard
- **Location**: "Operations dashboard"
- **Capture**:
  - Ops panel open
  - Charts showing:
    - Generation activity (line chart)
    - Queue depth (bar chart)
    - API usage gauge (circular)
  - All green status indicators

### 25. Keyboard Shortcuts Modal
- **Location**: "Keyboard shortcuts modal"
- **Capture**:
  - Shortcuts help modal open
  - Grid of shortcuts organized by category:
    - Navigation
    - Editing
    - View Controls
  - Search box at top

---

## Tips for Good Screenshots

### Technical Settings
- **Browser**: Use Chrome or Firefox
- **Window Size**: 1440x900 minimum, 1920x1080 preferred
- **Zoom**: 100% (don't zoom in/out)
- **Theme**: Use light theme for better visibility in docs

### Content Guidelines
- **Use sample data**: Create a realistic example story
- **Consistent naming**: Use "The Artifact" or similar theme throughout
- **Fill fields**: Don't leave forms empty
- **Show results**: Capture after actions complete (generated content, search results)

### Visual Polish
- **Hide personal info**: No real API keys in screenshots
- **Clean desktop**: Close unrelated windows
- **Consistent padding**: Leave small margin around window edges

### Annotation (Post-Capture)
Use an image editor to add:
- Red arrows pointing to key elements
- Numbered callouts for step sequences
- Highlight boxes around important buttons

---

## Screenshot Naming Convention

Save files as:
```
screenshot_[section]_[number]_[brief-description].png

Examples:
- screenshot_interface_01_main-layout.png
- screenshot_workflow_05_writer-panel.png
- screenshot_advanced_03_qc-dashboard.png
```

Store all screenshots in:
```
docs/images/
```

---

## After Capturing

1. Move screenshots to `docs/images/`
2. Update `docs/USER_GUIDE.md` to reference actual images:
   ```markdown
   ![Main Interface](images/screenshot_interface_01_main-layout.png)
   ```
3. Remove the placeholder code blocks
4. Verify all images display correctly in markdown preview
