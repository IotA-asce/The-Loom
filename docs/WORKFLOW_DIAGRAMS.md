# 🗺️ The Loom - Complete Workflow Diagrams

> Visual reference for all workflows in The Loom storytelling framework.

---

## 📑 Table of Contents

1. [Manga Workflows](#manga-workflows)
   - [Manga Import (Folder)](#manga-import-folder)
   - [Manga Import (CBZ)](#manga-import-cbz)
   - [Story Extraction from Manga](#story-extraction-from-manga)
   - [Manga Reading](#manga-reading)
2. [Story Graph Workflows](#story-graph-workflows)
   - [Graph Node Management](#graph-node-management)
   - [Branch Lifecycle](#branch-lifecycle)
   - [Story Extraction & Scene Creation](#story-extraction--scene-creation)
3. [AI Generation Workflows](#ai-generation-workflows)
   - [Text Generation (Writer Agent)](#text-generation-writer-agent)
   - [Image Generation (Artist Agent)](#image-generation-artist-agent)
4. [Ingestion Workflows](#ingestion-workflows)
   - [Text Document Ingestion](#text-document-ingestion)
   - [Manga Page Ingestion](#manga-page-ingestion)
5. [Dual-View Workflows](#dual-view-workflows)
   - [Text-Image Sync](#text-image-sync)
   - [Director Mode Editing](#director-mode-editing)
6. [System Workflows](#system-workflows)
   - [LLM Configuration](#llm-configuration)
   - [Accessibility & Mobile](#accessibility--mobile)

---

## Manga Workflows

### Manga Import (Folder)

```mermaid
flowchart TD
    Start([User Initiates Import]) --> Select[Select Manga Folder]
    Select --> Validate{Valid Images?}
    Validate -->|No| Error[Show Error Message]
    Error --> Start
    Validate -->|Yes| Upload[Upload Files to Backend]
    Upload --> Ingest[Ingest via archivist.py]
    
    subgraph Processing [Processing Pipeline]
        Ingest --> Sort[Sort by Filename]
        Sort --> Analyze[Analyze Each Page]
        Analyze --> OCR[Optional: OCR Text]
        OCR --> Hash[Compute Content Hash]
        Hash --> Metadata[Extract Metadata]
    end
    
    Metadata --> Copy[Copy to Permanent Storage<br/>.loom/manga_images/]
    Copy --> SaveVolume[Save to manga.db]
    SaveVolume --> CreateNode{Create Graph Node?}
    CreateNode -->|Yes| GraphNode[Create Graph Node<br/>node_type: manga]
    CreateNode -->|No| Success
    GraphNode --> Link[Link Volume to Node]
    Link --> Success([Import Success])
    
    style Processing fill:#e1f5e1,stroke:#2e7d32
    style Success fill:#c8e6c9,stroke:#2e7d32
    style Error fill:#ffcdd2,stroke:#c62828
```

**Key Files:**
- `ui/src/components/MangaFolderImport.tsx` - UI component
- `agents/archivist.py` - Ingestion logic
- `core/manga_storage.py` - Storage layer
- `ui/api.py` - API endpoints

---

### Manga Import (CBZ)

```mermaid
flowchart TD
    Start([User Drops CBZ]) --> Validate{Valid CBZ?}
    Validate -->|No| Error[Show Error]
    Error --> Start
    Validate -->|Yes| Extract[Extract Archive]
    
    subgraph SecurityChecks [Security Validation]
        Extract --> SizeCheck{File Size OK?}
        SizeCheck -->|No| Error
        SizeCheck -->|Yes| SigCheck{Signature Valid?}
        SigCheck -->|No| Error
        SigCheck -->|Yes| ZipCheck{Valid ZIP?}
        ZipCheck -->|No| Error
    end
    
    ZipCheck -->|Yes| ProcessPages[Process Image Pages]
    ProcessPages --> Security[Path Traversal Check]
    Security --> DeDuplicate[Deduplication Check]
    DeDuplicate --> Save[Save to Storage]
    Save --> CreateNode[Create Graph Node]
    CreateNode --> Success([Success])
    
    style SecurityChecks fill:#fff3e0,stroke:#e65100
    style Success fill:#c8e6c9,stroke:#2e7d32
```

---

### Story Extraction from Manga

```mermaid
flowchart TD
    Start([Click Extract Story]) --> Fetch[Fetch Volume with OCR]
    Fetch --> CheckOCR{Has OCR Text?}
    CheckOCR -->|No| Error[Error: No OCR Data]
    CheckOCR -->|Yes| Combine[Combine Page Text]
    
    subgraph AIProcessing [AI Processing]
        Combine --> SendLLM[Send to LLM Backend]
        SendLLM --> Prompt[Build Extraction Prompt]
        Prompt --> Generate[Generate Scene Analysis]
        Generate --> Parse[Parse JSON Response]
        Parse --> Validate{Valid Scenes?}
        Validate -->|No| Fallback[Create Fallback Scene]
    end
    
    Validate -->|Yes| CreateScenes[Create Scene Nodes]
    Fallback --> CreateScenes
    
    subgraph GraphCreation [Graph Creation]
        CreateScenes --> ForEach[For Each Scene]
        ForEach --> SceneNode[Create Scene Node]
        SceneNode --> Position[Set Position<br/>x: 150 + i*50]
        Position --> Metadata[Add Metadata<br/>pages, mood, characters]
        Metadata --> SaveNode[Save to graph.db]
        SaveNode --> LinkEdge[Link to Manga Node]
    end
    
    LinkEdge --> Notify[Notify User]
    Notify --> Refresh[Refresh Graph View]
    Refresh --> Success([Extraction Complete])
    
    style AIProcessing fill:#e3f2fd,stroke:#1565c0
    style GraphCreation fill:#f3e5f5,stroke:#6a1b9a
```

**API Endpoint:** `POST /api/manga/{volume_id}/extract-story`

---

### Manga Reading

```mermaid
flowchart TD
    Start([Open Manga]) --> LoadVolume[Load Volume Data]
    LoadVolume --> LoadProgress[Load Reading Progress]
    LoadProgress --> Resume{Resume Position?}
    
    Resume -->|Yes| GotoPage[Go to Last Page]
    Resume -->|No| Page1[Start at Page 1]
    
    GotoPage --> Display[Display Page Image]
    Page1 --> Display
    
    subgraph Navigation [Navigation Loop]
        Display --> Input{User Input}
        
        Input -->|Arrow Keys| Navigate[Change Page]
        Input -->|Swipe| Navigate
        Input -->|Thumbnail Click| Navigate
        
        Navigate --> SaveProgress[Save Progress<br/>localStorage]
        SaveProgress --> Preload[Preload Next Pages]
        Preload --> Display
        
        Input -->|Zoom In/Out| Zoom[Adjust Zoom Level]
        Zoom --> Display
        
        Input -->|Fullscreen| Fullscreen[Toggle Fullscreen]
        Fullscreen --> Display
        
        Input -->|Close| End
    end
    
    End([Close Reader])
    
    style Navigation fill:#e8f5e9,stroke:#2e7d32
```

---

## Story Graph Workflows

### Graph Node Management

```mermaid
flowchart TD
    Start([User Action]) --> Action{Action Type}
    
    Action -->|Create Node| Create[Create GraphNodeView]
    Create --> SetPosition[Set Position & Metadata]
    SetPosition --> PushUndo[Push to Undo Stack]
    PushUndo --> Save[Save to graph.db]
    
    Action -->|Move Node| Move[Update Position]
    Move --> PushUndo
    
    Action -->|Delete Node| Delete[Remove Node]
    Delete --> PushUndo
    
    Action -->|Undo| Undo[Pop from Undo Stack]
    Undo --> Restore[Restore Snapshot]
    PushRedo[Push to Redo Stack]
    Restore --> PushRedo
    
    Action -->|Redo| Redo[Pop from Redo Stack]
    Redo --> Restore2[Restore Snapshot]
    PushUndo2[Push to Undo Stack]
    Restore2 --> PushUndo2
    
    Action -->|Autosave| Snapshot[Create Snapshot]
    Snapshot --> Hash[Compute Hash]
    Hash --> Checkpoint[Create Checkpoint]
    Checkpoint --> Store[Store Autosave]
    
    Save --> Update[Update UI]
    PushUndo --> Update
    PushRedo --> Update
    PushUndo2 --> Update
    Store --> Update
    Update --> End([End])
    
    style Action fill:#e3f2fd,stroke:#1565c0
```

---

### Branch Lifecycle

```mermaid
flowchart TD
    Start([Branch Operation]) --> Operation{Operation}
    
    Operation -->|Create| Preview[Preview Impact]
    Preview --> ShowImpact[Show Descendant Count<br/>Divergence Score]
    ShowImpact --> Confirm{User Confirms?}
    Confirm -->|No| Cancel[Cancel]
    Confirm -->|Yes| CheckBudget{Budget OK?}
    CheckBudget -->|No| ShowArchive[Suggest Archive Candidates]
    CheckBudget -->|Yes| CreateBranch[Create BranchRecord]
    CreateBranch --> SetLineage[Set Lineage<br/>parent.child]
    SetLineage --> SetStatus[Status: ACTIVE]
    
    Operation -->|Archive| CheckActive{Branch Active?}
    CheckActive -->|No| Error1[Error: Not Active]
    CheckActive -->|Yes| CheckArchiveBudget{Archive Budget OK?}
    CheckArchiveBudget -->|No| Error2[Error: Archive Full]
    CheckArchiveBudget -->|Yes| Archive[Set Status: ARCHIVED]
    Archive --> SetReason[Set Archive Reason]
    
    Operation -->|Merge| CheckBoth{Both Exist?}
    CheckBoth -->|No| Error3[Error: Branch Missing]
    CheckBoth -->|Yes| CheckActive2{Source Active?}
    CheckActive2 -->|No| Error4[Error: Source Inactive]
    CheckActive2 -->|Yes| Merge[Set Status: MERGED]
    Merge --> SetTarget[Set merged_into]
    
    SetStatus --> Persist[Persist to Storage]
    SetReason --> Persist
    SetTarget --> Persist
    Persist --> Notify[Notify Listeners]
    Notify --> End([End])
    
    Cancel --> End
    Error1 --> End
    Error2 --> End
    Error3 --> End
    Error4 --> End
    
    style Operation fill:#fff3e0,stroke:#e65100
    style Persist fill:#c8e6c9,stroke:#2e7d32
```

---

### Story Extraction & Scene Creation

```mermaid
flowchart TD
    Start([Extract Story]) --> GetOCR[Get OCR Text by Page]
    GetOCR --> BuildContext[Build LLM Context]
    
    subgraph LLMExtraction [LLM Scene Extraction]
        BuildContext --> Prompt[Build Prompt:<br/>- Manga Title<br/>- Page Text<br/>- Extraction Rules]
        Prompt --> CallLLM[Call LLM Backend]
        CallLLM --> Response[Get JSON Response]
        Response --> Parse[Parse Scenes Array]
        Parse --> ForEach[For Each Scene]
    end
    
    subgraph SceneCreation [Scene Node Creation]
        ForEach --> GenID[Generate UUID]
        GenID --> CreateNode[Create GraphNode]
        CreateNode --> SetType[node_type: scene]
        SetType --> AddMeta[Add Metadata:<br/>- page_start/end<br/>- characters<br/>- mood<br/>- key_events<br/>- content]
        AddMeta --> Position[Position:<br/>x: 150 + i*50<br/>y: 150 + i*30]
        Position --> Save[Save to graph.db]
        Save --> CreateEdge[Create Edge to Manga Node]
        CreateEdge --> Link[Link Type: contains]
    end
    
    Link --> Collect[Collect Created Scenes]
    Collect --> Result[Return Result:<br/>- scenes_created<br/>- manga_node_id]
    Result --> Refresh[Refresh Graph Canvas]
    Refresh --> End([Show Success Toast])
    
    style LLMExtraction fill:#e3f2fd,stroke:#1565c0
    style SceneCreation fill:#f3e5f5,stroke:#6a1b9a
```

---

## AI Generation Workflows

### Text Generation (Writer Agent)

```mermaid
flowchart TD
    Start([Generate Text]) --> BuildRequest[Build WriterRequest]
    
    subgraph RequestSetup [Request Setup]
        BuildRequest --> Context[Assemble Context:<br/>- chapter_summary<br/>- arc_summary<br/>- context_text]
        Context --> Tuner[Apply TunerSettings:<br/>- violence<br/>- humor<br/>- romance]
        Tuner --> Exemplars[Retrieve Style Exemplars]
        Exemplars --> VoiceCards[Load Voice Cards]
    end
    
    subgraph PromptBuilding [Prompt Building]
        RequestSetup --> Registry[Load PromptRegistry]
        Registry --> Package[Build PromptPackage:<br/>- system_prompt<br/>- developer_prompt<br/>- user_prompt<br/>- grounded_prompt]
        Package --> Layer[Strict Layering:<br/>System → Developer → User]
    end
    
    subgraph Generation [Generation]
        Layer --> CheckInjection{Prompt Injection?}
        CheckInjection -->|Yes| Block[Block & Log]
        CheckInjection -->|No| SendLLM[Send to LLM Backend]
        SendLLM --> Stream{Stream?}
        Stream -->|Yes| StreamResponse[Stream Chunks]
        Stream -->|No| FullResponse[Get Full Response]
    end
    
    subgraph PostProcess [Post-Processing]
        StreamResponse --> QualityCheck[Quality Checks:<br/>- Style similarity<br/>- Contradiction detection]
        FullResponse --> QualityCheck
        QualityCheck --> CheckVoice{Voice OK?}
        CheckVoice -->|No| Adjust[Adjust Output]
        CheckVoice -->|Yes| Finalize[Finalize Result]
        Adjust --> Finalize
    end
    
    Finalize --> Store[Store Result]
    Block --> Error[Return Error]
    Store --> End([Return WriterResult])
    Error --> End
    
    style RequestSetup fill:#e3f2fd,stroke:#1565c0
    style PromptBuilding fill:#fff3e0,stroke:#e65100
    style Generation fill:#f3e5f5,stroke:#6a1b9a
    style PostProcess fill:#e8f5e9,stroke:#2e7d32
```

**API Endpoint:** `POST /api/writer/generate`

---

### Image Generation (Artist Agent)

```mermaid
flowchart TD
    Start([Generate Panels]) --> BuildRequest[Build ArtistRequest]
    
    subgraph BlueprintSetup [Scene Blueprint]
        BuildRequest --> Setting[Setting]<br/>TimeOfDay<br/>Weather
        Setting --> Lighting[Lighting:<br/>- direction<br/>- intensity]
        Lighting --> Camera[Camera:<br/>- shot_type<br/>- angle<br/>- focus]
        Camera --> Characters[Characters:<br/>- position<br/>- pose<br/>- expression]
        Characters --> Props[Props]
    end
    
    subgraph Atmosphere [Atmosphere Control]
        BlueprintSetup --> Preset[Select Preset:<br/>- neutral<br/>- tense<br/>- melancholy<br/>- action]
        Preset --> Adjust[Adjust Parameters:<br/>- temperature<br/>- CFG scale<br/>- Steps]
    end
    
    subgraph Generation [Panel Generation]
        Atmosphere --> ForEach[For Each Panel]
        ForEach --> LoadLoRA[Load Character LoRAs]
        LoadLoRA --> Identity[Apply Identity Packs]
        Identity --> Continuity[Apply Continuity:<br/>- Previous panel reference<br/>- Style consistency]
        Continuity --> Generate[Generate Image]
        Generate --> QC[Quality Control]
        QC --> Check{Pass?}
        Check -->|No| Retry[Retry/Adjust]
        Check -->|Yes| Store[Store Artifact]
    end
    
    subgraph Output [Output Assembly]
        Store --> Collect[Collect All Panels]
        Collect --> Scores[Compute Scores:<br/>- overall_quality<br/>- continuity_score]
        Scores --> Package[Package ArtistResult]
    end
    
    Package --> End([Return Result])
    Retry --> Generate
    
    style BlueprintSetup fill:#e3f2fd,stroke:#1565c0
    style Atmosphere fill:#fff3e0,stroke:#e65100
    style Generation fill:#f3e5f5,stroke:#6a1b9a
```

**API Endpoint:** `POST /api/artist/generate-panels`

---

## Ingestion Workflows

### Text Document Ingestion

```mermaid
flowchart TD
    Start([Upload Text]) --> DetectType{File Type}
    
    DetectType -->|.txt| ParseTXT[Parse TXT:<br/>- Decode bytes<br/>- Normalize whitespace]
    DetectType -->|.pdf| ParsePDF[Parse PDF:<br/>- Try pypdf<br/>- Fallback extraction]
    DetectType -->|.epub| ParseEPUB[Parse EPUB:<br/>- Read spine<br/>- Extract HTML<br/>- Parse chapters]
    
    subgraph Parsing [Parsing Pipeline]
        ParseTXT --> Normalize[Normalize Content]
        ParsePDF --> Normalize
        ParseEPUB --> Normalize
        Normalize --> Split[Split into Chapters]
        Split --> Hash[Compute Chunk Hashes]
    end
    
    subgraph Deduplication [Deduplication]
        Hash --> CheckCache{In Cache?}
        CheckCache -->|Yes| UseCached[Return Cached Report]
        CheckCache -->|No| Compare[Compare Signatures]
        Compare --> NearDup{Near Duplicate?}
        NearDup -->|Yes| Warn[Add Warning]
        NearDup -->|No| Continue
        Warn --> Continue
    end
    
    Continue --> BuildReport[Build TextIngestionReport:<br/>- parser_used<br/>- chapters<br/>- confidence<br/>- warnings]
    BuildReport --> CacheResult[Cache Result]
    UseCached --> End
    CacheResult --> End([Return Report])
    
    style Parsing fill:#e3f2fd,stroke:#1565c0
    style Deduplication fill:#fff3e0,stroke:#e65100
```

---

### Manga Page Ingestion

```mermaid
flowchart TD
    Start([Upload Images]) --> Validate{Valid Files?}
    Validate -->|No| Error[Error: Invalid]
    Validate -->|Yes| Sort[Sort by Filename]
    
    subgraph Processing [Per-Page Processing]
        Sort --> ForEach[For Each Image]
        ForEach --> Load[Load with PIL]
        Load --> Normalize[Normalize Mode:<br/>RGB conversion<br/>Alpha handling]
        Normalize --> Analyze[Visual Analysis:<br/>- Brightness<br/>- Contrast<br/>- Line density<br/>- Composition]
        Analyze --> Hash[Compute Hashes:<br/>- content_hash<br/>- perceptual_hash]
        Hash --> DetectSpread[Detect Spreads:<br/>aspect ratio check]
        DetectSpread --> Metadata[Build MangaPageMetadata]
    end
    
    subgraph Security [Security & Validation]
        Metadata --> CheckSize{Size OK?}
        CheckSize -->|No| Error
        CheckSize -->|Yes| CheckSig{Signature OK?}
        CheckSig -->|No| Error
        CheckSig -->|Yes| CheckPath{Path Safe?}
        CheckPath -->|No| Error
    end
    
    CheckPath -->|Yes| Deduplicate[Deduplication Check]
    Deduplicate --> BuildReport[Build IngestionReport]
    BuildReport --> Save[Save to manga.db]
    Save --> End([Success])
    Error --> End
    
    style Processing fill:#e3f2fd,stroke:#1565c0
    style Security fill:#ffcdd2,stroke:#c62828
```

---

## Dual-View Workflows

### Text-Image Sync

```mermaid
flowchart TD
    Start([Initialize Dual View]) --> CreateState[Create DualViewState]
    CreateState --> SetVersions[Set Versions:<br/>text_version<br/>image_version]
    SetVersions --> SetStatus[Status: SYNCED]
    SetVersions --> AddBadge[Add SyncBadge]
    
    subgraph EditLoop [Edit Loop]
        AddBadge --> Wait{Edit Type?}
        
        Wait -->|Text Edit| TextEdit[Record SentenceEditAction]
        TextEdit --> MarkTextStale[Mark TEXT_STALE]
        MarkTextStale --> UpdateBadges[Update Badges]
        UpdateBadges --> QueueImageSync[Queue Image Sync]
        
        Wait -->|Image Redraw| ImageEdit[Record PanelRedrawAction]
        ImageEdit --> MarkImageStale[Mark IMAGE_STALE]
        MarkImageStale --> UpdateBadges2[Update Badges]
        UpdateBadges2 --> QueueTextSync[Queue Text Sync]
    end
    
    subgraph Reconcile [Reconcile]
        QueueImageSync --> UserAction{User Action}
        QueueTextSync --> UserAction
        UserAction -->|Reconcile| StartReconcile[Status: RECONCILING]
        StartReconcile --> UpdateVersions[Update Versions]
        UpdateVersions --> MarkSynced[Status: SYNCED]
        MarkSynced --> ClearBadges[Clear Stale Badges]
    end
    
    ClearBadges --> End([Synced])
    
    style EditLoop fill:#fff3e0,stroke:#e65100
    style Reconcile fill:#e8f5e9,stroke:#2e7d32
```

---

### Director Mode Editing

```mermaid
flowchart TD
    Start([Director Mode]) --> ViewState[View Current State]
    ViewState --> ShowBadges[Show Sync Badges]
    
    subgraph Actions [Available Actions]
        ShowBadges --> Choice{User Choice}
        
        Choice -->|Edit Sentence| Edit[Edit Sentence]
        Edit --> RecordEdit[RecordEditAction:<br/>- sentence_index<br/>- before/after<br/>- actor]
        RecordEdit --> MarkStale[Mark Text Stale]
        
        Choice -->|Request Redraw| Redraw[Request Panel Redraw]
        Redraw --> RecordRedraw[RecordRedrawAction:<br/>- panel_index<br/>- reason<br/>- actor]
        RecordRedraw --> MarkImageStale[Mark Image Stale]
        
        Choice -->|Reconcile| Reconcile[Reconcile Versions]
        Reconcile --> Sync[Sync Text & Image]
    end
    
    subgraph StateManagement [State Management]
        MarkStale --> UpdateUI[Update UI Badges]
        MarkImageStale --> UpdateUI
        Sync --> ClearQueue[Clear Action Queue]
        ClearQueue --> ResetStatus[Reset to SYNCED]
    end
    
    ResetStatus --> Refresh[Refresh View]
    UpdateUI --> Continue{Continue?}
    Continue -->|Yes| ShowBadges
    Continue -->|No| End([Exit Director Mode])
    Refresh --> End
    
    style Actions fill:#e3f2fd,stroke:#1565c0
    style StateManagement fill:#f3e5f5,stroke:#6a1b9a
```

---

## System Workflows

### LLM Configuration

```mermaid
flowchart TD
    Start([Configure LLM]) --> ListProviders[GET /api/llm/providers]
    ListProviders --> Select[Select Provider]
    
    Select -->|OpenAI| ConfigOpenAI[Config: OPENAI_API_KEY]
    Select -->|Anthropic| ConfigAnthropic[Config: ANTHROPIC_API_KEY]
    Select -->|Gemini| ConfigGemini[Config: GEMINI_API_KEY]
    Select -->|Ollama| ConfigOllama[Config: Base URL]
    Select -->|Mock| UseMock[Use Mock Backend]
    
    subgraph Setup [Backend Setup]
        ConfigOpenAI --> CreateBackend[Create LLM Backend]
        ConfigAnthropic --> CreateBackend
        ConfigGemini --> CreateBackend
        ConfigOllama --> CreateBackend
        UseMock --> CreateBackend
        CreateBackend --> Test[Test Connection]
    end
    
    Test --> Success{Success?}
    Success -->|Yes| Store[Store as Global Backend]
    Success -->|No| ShowError[Show Error]
    ShowError --> Retry[Retry Configuration]
    Retry --> Select
    
    Store --> Ready[Backend Ready]
    Ready --> End([Configuration Complete])
    
    style Setup fill:#e3f2fd,stroke:#1565c0
```

**API Endpoints:**
- `GET /api/llm/providers`
- `POST /api/llm/config`
- `POST /api/llm/test`
- `WS /api/llm/stream/{client_id}`

---

### Accessibility & Mobile

```mermaid
flowchart TD
    Start([Page Load]) --> DetectViewport[Detect Viewport Size]
    DetectViewport --> Breakpoint{Breakpoint}
    
    Breakpoint -->|< 768px| Mobile[Mobile Layout:<br/>- Single column<br/>- Stacked controls<br/>- Touch gestures]
    Breakpoint -->|768-1100px| Tablet[Tablet Layout:<br/>- Two columns<br/>- Hybrid controls]
    Breakpoint -->|> 1100px| Desktop[Desktop Layout:<br/>- Three columns<br/>- Side-by-side dual view]
    
    subgraph Audit [Accessibility Audit]
        Mobile --> CheckShortcuts[Check Keyboard Shortcuts]
        Tablet --> CheckShortcuts
        Desktop --> CheckShortcuts
        CheckShortcuts --> CheckLabels[Check Semantic Labels]
        CheckLabels --> CheckIndicators[Check Non-Color Indicators]
    end
    
    subgraph Compliance [Compliance Check]
        CheckIndicators --> Coverage{Coverage >= 95%?}
        Coverage -->|Yes| Pass[Mark Accessible]
        Coverage -->|No| Issues[Generate Issue List]
        Issues --> Suggest[Suggest Fixes]
    end
    
    Pass --> ApplyLayout[Apply Responsive Layout]
    Suggest --> ApplyLayout
    ApplyLayout --> End([Render UI])
    
    style Audit fill:#e3f2fd,stroke:#1565c0
    style Compliance fill:#fff3e0,stroke:#e65100
```

---

## Data Flow Overview

```mermaid
flowchart LR
    subgraph Frontend [Frontend - React/TypeScript]
        UI[UI Components]
        State[Zustand Stores]
        Canvas[Graph Canvas]
    end
    
    subgraph API [API Layer - FastAPI]
        Endpoints[REST Endpoints]
        WS[WebSocket]
        Models[Pydantic Models]
    end
    
    subgraph Core [Core Engine - Python]
        Graph[Story Graph Engine]
        Writer[Text Generation]
        Artist[Image Generation]
        Ingest[Ingestion]
    end
    
    subgraph Storage [Storage]
        SQLite[(SQLite<br/>graph.db<br/>manga.db)]
        Vector[(ChromaDB<br/>Vector Store)]
        Files[File Storage<br/>manga_images/]
    end
    
    UI --> State
    State --> Canvas
    UI --> Endpoints
    Canvas --> Endpoints
    Endpoints --> Models
    Models --> Graph
    Models --> Writer
    Models --> Artist
    Models --> Ingest
    Graph --> SQLite
    Writer --> SQLite
    Writer --> Vector
    Artist --> Files
    Ingest --> SQLite
    Ingest --> Files
    
    style Frontend fill:#e3f2fd,stroke:#1565c0
    style API fill:#f3e5f5,stroke:#6a1b9a
    style Core fill:#fff3e0,stroke:#e65100
    style Storage fill:#e8f5e9,stroke:#2e7d32
```

---

## Event Sourcing Flow

```mermaid
flowchart TD
    Start([User Action]) --> CreateEvent[Create Event]
    CreateEvent --> Validate[Validate Event]
    Validate --> Append[Append to Event Store]
    
    subgraph EventStore [Event Store]
        Append --> Persist[Persist to SQLite]
        Persist --> Notify[Notify Subscribers]
    end
    
    subgraph Projection [Projection Handler]
        Notify --> UpdateReadModel[Update Read Model]
        UpdateReadModel --> UpdateCache[Update Cache]
    end
    
    subgraph WebSocket [Real-time Updates]
        UpdateCache --> Broadcast[Broadcast to Clients]
        Broadcast --> Push[Push to UI]
    end
    
    Push --> Render[Re-render Components]
    Render --> End([UI Updated])
    
    style EventStore fill:#e3f2fd,stroke:#1565c0
    style Projection fill:#f3e5f5,stroke:#6a1b9a
    style WebSocket fill:#e8f5e9,stroke:#2e7d32
```

---

## Key Files Reference

| Workflow | Primary Files |
|----------|---------------|
| **Manga Import** | `ui/src/components/MangaFolderImport.tsx`, `agents/archivist.py`, `core/manga_storage.py` |
| **Story Extraction** | `ui/api.py::extract_story_from_manga()`, `core/llm_backend.py` |
| **Manga Reading** | `ui/src/components/ReadingView.tsx`, `ui/src/components/MangaViewer.tsx` |
| **Graph Management** | `core/graph_persistence.py`, `core/story_graph_engine.py`, `ui/src/components/GraphCanvas.tsx` |
| **Text Generation** | `core/text_generation_engine.py`, `agents/writer.py` |
| **Image Generation** | `core/image_generation_engine.py`, `agents/artist.py` |
| **Dual View** | `core/frontend_workflow_engine.py::DualViewManager` |
| **Branching** | `core/story_graph_engine.py::BranchLifecycleManager` |

---

*Generated: 2026-02-10 | The Loom v1.0*
