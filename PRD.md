# Product Requirements Document (PRD): The Loom

| Field | Value |
| --- | --- |
| Project | The Loom |
| Version | 1.1 |
| Status | Draft |
| Date | 2026-02-08 |

## 1. Executive Summary

The Loom is a universal, Python-based AI storytelling engine designed to ingest, analyze, and expand narratives of any genre or maturity level. Whether the source material is a lighthearted children's fable or a visceral, complex adult horror manga, The Loom respects and replicates the source's tone without sanitization or bias.

It features a node-based interactive UI for visualizing narrative branches and orchestrates specialized LLM agents to generate text (novels) and images (manga panels) that are faithful to the original author's intent -- no matter how charming or how gory.

## 2. Problem Statement

Current AI storytelling tools suffer from "tonal regression": they often default to safe, neutral, or overly positive outputs, struggling to capture extreme stylistic nuances.

- Genre limitations: Existing models struggle to switch effectively between the innocence required for a fairy tale and the psychological depth or visceral description required for Seinen/adult fiction.
- Visual inconsistency: Generating consistent art for "gory" or "dark" scenes often triggers safety refusals in standard tools, or fails to capture the specific aesthetic of horror/action manga.
- Narrative amnesia: Long-form stories lose coherency over time.
- Rigid linear paths: Users cannot easily explore "What If" scenarios (e.g., "What if the villain won?") without manually rewriting previous context.

## 3. Goals & Objectives

- Total genre agnosticism: Build a system capable of handling the full spectrum of storytelling.
  - Tone: Wholesome/Charming <-> Dark/Nihilistic
  - Audience: Children (Kodomomuke) <-> Adult (Seinen/Josei/Mature)
  - Content: Fluff/Slice-of-Life <-> Gore/Horror/Violence
- Unfiltered stylistic fidelity: The AI must act as a neutral mirror, reflecting the exact writing style and visual intensity of the ingested content.
- Visual logic mapping: Create a navigable "Tree of Possibilities" for every story.
- Multi-modal output: Seamless generation of novel chapters and manga pages.

## 4. User Personas

- The Dark Fantasy Author: Needs a tool that won't tone down their battle scenes or soften the impact of a tragic plot twist.
- The Children's Illustrator: Needs consistent, soft, and non-threatening visual consistency for a picture book.
- The Legacy Fan: Wants to see an alternate ending to a favorite series that was cancelled or had a controversial ending, maintaining the original gritty or mature tone.

## 5. Functional Requirements

### 5.1 Core Architecture (The Backend)

- Tech stack: Python, LangChain (agent orchestration), vector database (Pinecone/Chroma), local LLM support (Llama 3 / Mistral for uncensored steerability).
- The "Spectrum Engine": A tuning module that analyzes the "Safety/Maturity Rating" of the input and adjusts the model's temperature and system prompts to match.

### 5.2 The Ingestion Phase (Input)

- Universal text ingestion: Parse `.txt`, `.pdf`, `.epub`.
- Sentiment & intensity analysis: Detects the baseline level of violence, romance, or comedy.
- Universal manga ingestion: Parse `.cbz` and image folders.
- Visual tonal analysis: Distinguishes between "chibi/gag" and "realistic/grotesque" art styles.
- OCR: Extracts dialogue to pair with visual context.

### 5.3 The "Tree of Possibilities" (Logic)

- Timeline mapping: Auto-generates a chronological event graph.
- Divergence nodes: Users can click any node (event) to create a branch.
  - Example: In a horror story, branching at "Character opens the door" vs. "Character runs away."
- Consequence simulation: The logic engine calculates how a change in tone (e.g., "Make this scene gorier") impacts future nodes.

### 5.4 The Generation Engine (Output)

- Novel mode (text)
  - Style mimicry: If the input is simple and repetitive (children's book), the output matches it. If the input is dense, archaic, or violent (Lovecraftian), the output matches it.
- Manga mode (visual)
  - Panel generation: Uses diffusion models with ControlNet to generate panels.
  - Aesthetic range:
    - Mode A (Light): Soft lines, bright colors, round shapes.
    - Mode B (Dark): Heavy shadows, high contrast, detailed cross-hatching, visceral textures (blood, grime, damage).
  - Character consistency: LoRA models trained on the specific character designs to ensure they look the same whether they are smiling or in battle.

### 5.5 User Interface (The Frontend)

- Interactive graph: A visual tree where nodes represent plot beats.
- The "Tuner" slider: A UI element allowing users to manually override the intensity of the generated branch (e.g., specific sliders for "Violence," "Humor," "Romance").
- Dual view: Split screen option to see the text generation and the corresponding manga panel generation simultaneously.

## 6. Development Stages (Milestones)

### Phase 1: The Foundation (Ingestion & Tonal Analysis)

- [ ] Build ingestion scripts for text and image data.
- [ ] Develop the "Rating Classifier" to tag ingested content (e.g., tags: "Gore", "Psychological", "Wholesome").
- Deliverable: A system that reads a story and outputs a JSON profile of its characters and its "Maturity Rating".

### Phase 2: The Weaver (Text Generation & Branching)

- [ ] Implement the node graph data structure.
- [ ] Build the "Writer Agent" with dynamic system prompting (e.g., "You are a horror writer, do not hold back on description").
- Deliverable: A UI where I can load a text file, pick a scene, and generate a darker or lighter version of the next chapter.

### Phase 3: The Illustrator (Manga Pipeline)

- [ ] Integrate Stable Diffusion / Flux with LoRA training on the fly.
- [ ] Implement "Atmosphere Control": ensuring the lighting and texture match the narrative tone (e.g., sunny vs. gloomy).
- Deliverable: Generating 4 sequential manga panels that visually match the intensity of the text.

### Phase 4: The Director (UI & Final Polish)

- [ ] Full React/Streamlit GUI.
- [ ] "Director Mode": Allow users to edit specific generated sentences or redraw specific panels to refine the tone.
- Deliverable: The complete standalone application.

## 7. Non-Functional Requirements

- Steerability: The model must prioritize user instruction over default safety filters (assuming local model usage for sensitive content).
- Privacy: All story data and generations remain local or on private user API keys.
- Scalability: Capable of handling short stories (5k words) to epic sagas (2M+ words).

## 8. Risks & Mitigation

- Risk: Model refusal on mature content.
  - Mitigation: Support for "Uncensored" open-weights models (e.g., certain Llama finetunes) via local inference (Ollama/LM Studio) to ensure the "gory/adult" requirements can be met without API blocks.
- Risk: Style drift.
  - Mitigation: Strong few-shot prompting where the agents are constantly fed examples from the original text before writing new lines.

## 9. Suggested Repository Structure

Plaintext: `the-loom/`

```text
the-loom/
├── agents/
│   ├── archivist.py       # Ingestion & tonal analysis
│   ├── writer.py          # Text gen (supports all genres)
│   ├── artist.py          # Image gen (style & atmosphere control)
│   └── director.py        # Orchestrator & safety/rating tuner
├── core/
│   ├── graph_logic.py     # Tree branching mechanics
│   └── profiles.py        # Character & style LoRAs
├── models/                # Storage for local LLMs/diffusion weights
├── ui/                    # Frontend
│   ├── graph_view.jsx     # The node tree
│   └── editor.jsx         # Text/image manipulation
├── tests/
│   ├── test_childrens.py  # Validation on simple/wholesome inputs
│   └── test_seinen.py     # Validation on complex/mature inputs
└── requirements.txt
```
