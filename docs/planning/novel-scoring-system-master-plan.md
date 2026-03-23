# Novel Scoring System Plan

## Goal
This document defines a full implementation plan for reproducing the novel scoring experience of the analyzed site while using the provided `SYSTEM_PROMPT` as the primary scoring authority.

Project priority:
1. Reproduce the current product behavior and output contract as closely as possible.
2. Add stability and quality improvements only after the replica path is working.

This is intentionally a copy-first plan, not a redesign-first plan.

## Confirmed Frontend Facts From Analysis
The captured frontend assets show several hard constraints that the replica should follow.

### 1. Main entry and API shape
The analyzed site loads a frontend bundle and sends scoring requests to `/api/analyze`.
Relevant references:
- `D:/PythonProject/novel_evaluation/output/playwright/page.html:33`
- `D:/PythonProject/novel_evaluation/output/playwright/page.html:48`
- `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:70470`
- `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:70473`

Observed request body:

```json
{
  "text": "user novel excerpt or outline",
  "isBuiltIn": true,
  "userConfig": {
    "modelId": "gemini-3-pro-preview",
    "endpoint": "",
    "apiKey": ""
  }
}
```

Implication:
- The replica should keep the same request contract for maximum compatibility.
- The full scoring prompt should live on the server side, not in the browser.

### 2. Output must be strict JSON
The analyzed frontend concatenates streamed chunks, strips an optional ```json wrapper, and then runs `JSON.parse()` directly.
Relevant references:
- `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:70462`
- `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:70463`
- `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:70481`

Implication:
- The model must return valid JSON.
- No extra prose should appear outside the JSON body.
- Streaming is fine, but the final concatenated text must still be valid JSON.

### 3. Frontend-consumed result fields
The frontend already expects these fields.

Top-level numeric scores:
- `signingProbability` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71453`
- `commercialValue` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71461`
- `writingQuality` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71469`
- `innovationScore` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71477`

Platform recommendation section:
- `sortingHat.platforms` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71485`
- `platforms[0].name` is treated as the best-fit platform - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71555`
- `name`, `percentage`, `reason` are rendered from each platform item - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71594`, `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71602`, `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71613`

Verdict fields:
- `editorVerdict` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71641`
- `marketFit` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71648`

Detailed analysis fields:
- `detailedAnalysis.plot` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71668`
- `detailedAnalysis.character` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71676`
- `detailedAnalysis.pacing` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71684`
- `detailedAnalysis.worldBuilding` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71692`

List fields:
- `strengths` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71749`
- `weaknesses` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71755`

Score range:
- Radar chart uses `0-100` - `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71728`, `D:/PythonProject/novel_evaluation/output/playwright/formatted.js:71729`

Implication:
- The replica should preserve these field names exactly.
- All score values should be integers in the `0-100` range.

## Copy-First Product Definition
The replica should preserve the following product identity.

### Core product behavior
- Accept a novel opening, chapter excerpt, or outline.
- Evaluate it in a harsh chief-editor voice.
- Produce four headline scores.
- Produce a platform-routing result via `sortingHat.platforms`.
- Produce a short market judgment and a sharp editor verdict.
- Produce four focused analysis paragraphs.
- Produce short strengths and weaknesses lists.

### Copy-first constraints
- Use the provided `SYSTEM_PROMPT` as-is as the main scoring rulebook.
- Do not soften the tone during the copy phase.
- Do not rename output fields.
- Do not add user-facing fields in phase one.
- Do not move prompt logic into the frontend.

## Prompt Integration Plan

### Prompt storage
Store the provided `SYSTEM_PROMPT` on the server.
Recommended location:
- place it under the repository's controlled prompt assets directory
- keep the prompt path and runtime loading strategy independent from any specific language or framework

### Prompt usage
Use a minimal message structure:

```text
system:
  [use the provided SYSTEM_PROMPT exactly]

user:
  Evaluate the following web novel excerpt or outline and return strict JSON only.

  {{text}}
```

Rationale:
- This keeps the existing scoring philosophy intact.
- The user message only injects the manuscript text and does not redefine the rules.

### Prompt governance
For the copy phase:
- Freeze prompt wording.
- Track prompt versions in source control.
- Record model name and prompt version with each scored sample.

## Target Output Contract
The service should return JSON in this shape:

```json
{
  "signingProbability": 0,
  "commercialValue": 0,
  "writingQuality": 0,
  "innovationScore": 0,
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["risk 1", "risk 2"],
  "sortingHat": {
    "platforms": [
      {
        "name": "platform name",
        "percentage": 0,
        "reason": "short reason"
      }
    ]
  },
  "marketFit": "short market comment",
  "editorVerdict": "sharp chief editor verdict",
  "detailedAnalysis": {
    "plot": "plot and hook analysis",
    "character": "character analysis",
    "pacing": "writing and pacing analysis",
    "worldBuilding": "worldbuilding analysis"
  }
}
```

## Scoring Execution Plan
This section translates the provided prompt into implementation-ready scoring behavior.

### 1. `signingProbability`
Use this as the final contractability score.

Rules to preserve:
- It must be derived from `commercialValue`, `writingQuality`, and `innovationScore`.
- It must not float far above the base scores.
- It should drop hard when the text triggers low-grade hooks, stale formula writing, puppet-system protagonists, shallow face-slapping conflict, or strong AI-generated manual-like writing.

### 2. `commercialValue`
Judge serialized market potential.

Focus points:
- hook strength
- reader retention potential
- platform compatibility
- long-form update potential
- monetizable conflict and character momentum

### 3. `writingQuality`
Judge readability and execution rather than literary prestige.

Strong penalties:
- AI-manual tone
- empty decorative phrasing
- low-skill exposition dumps
- awkward mixed-language naming pollution
- concept-term spam
- extremely childish prose

### 4. `innovationScore`
Judge useful freshness, not random weirdness.

Strong penalties:
- stale formulas
- obvious recycled arcs
- old trope patchwork
- clumsy hybridization of game jargon, memes, or real-world slang

### 5. `strengths` and `weaknesses`
Implementation rules:
- Keep each array short and readable.
- Prefer 2-4 items in each array.
- Each item should be a direct point, not a paragraph.
- Weaknesses should identify real failure points, not vague negativity.

### 6. `sortingHat.platforms`
Implementation rules:
- Recommend 1-3 platforms.
- Each platform item must contain `name`, `percentage`, and `reason`.
- The most suitable platform must be the first element because the current UI highlights `platforms[0]`.
- `reason` should stay short.
- Percentages should be integers and should ideally sum to 100.

### 7. Verdict and detailed analysis
Implementation rules:
- `marketFit` should be a concise market positioning statement.
- `editorVerdict` should be the strongest one-line editorial label.
- `detailedAnalysis.plot` should explain hook, conflict, and suspense efficiency.
- `detailedAnalysis.character` should explain desire, agency, and differentiation.
- `detailedAnalysis.pacing` should explain readability, density, rhythm, and AI-feel.
- `detailedAnalysis.worldBuilding` should explain novelty, clarity, and story usefulness.

## Service Interface Reproduction Plan

### Endpoint
Reproduce `POST /api/analyze` first.

Request body:

```json
{
  "text": "manuscript text",
  "isBuiltIn": true,
  "userConfig": {
    "modelId": "model name",
    "endpoint": "provider endpoint",
    "apiKey": "secret"
  }
}
```

Response mode:
- Prefer a streaming-compatible response mode if needed for compatibility with the analyzed frontend flow.
- Keep the transport details provider-neutral at the planning stage.
- Ensure the final concatenated payload is valid JSON.

### Service flow
1. Receive request.
2. Load prompt and model configuration.
3. Build messages.
4. Call the selected provider.
5. Return content through the chosen response strategy.
6. Validate final JSON.
7. Return structured failure if validation fails.

### Built-in vs custom model mode
Mirror the current product behavior:
- `isBuiltIn=true` uses the service's own configured model route.
- `isBuiltIn=false` uses user-provided model configuration.

## User Interface Reproduction Plan

### Input panel
Keep the current interaction model:
- text input area
- optional file upload for `.txt`, `.md`, `.docx`
- one primary score button

### Output panel
Render the same conceptual blocks:
- four score cards
- sorting hat platform section
- editor verdict block
- market fit block
- four detailed analysis cards
- radar chart
- strengths and weaknesses lists

### Error handling
Even if the original frontend is rigid, the replica should add a thin safety layer:
- show invalid JSON errors cleanly
- default missing arrays to empty lists
- default missing text fields to empty strings
- default missing scores to `0`

## Validation and QA Plan
Copy-first does not mean trust-the-model blindly. Add programmatic checks behind the prompt.

### Schema validation
Validate:
- required top-level fields
- array types for `strengths`, `weaknesses`, and `sortingHat.platforms`
- object shape for `detailedAnalysis`
- string presence in required narrative fields

### Numeric validation
Validate:
- all four headline scores are integers
- score range is `0-100`
- platform percentages are integers
- platform count is `1-3`

### Logic validation
Enforce prompt-consistent sanity checks:
- `signingProbability` should not be much higher than the three base scores
- low-grade-hook cases should be capped aggressively
- visual-pollution cases should cap `writingQuality`
- platform list should be sorted by suitability descending

### Retry strategy
Recommended order:
1. Parse and repair minor JSON formatting issues.
2. Retry once with an added format reminder if needed.
3. Return structured error instead of broken output after repeated failure.

## Test Plan

### Positive test set
Prepare cases for:
- strong commercial hook opening
- competent mainstream serialized fiction
- polished prose with weaker commercial power
- known high-quality web fiction or famous works

Success criteria:
- good texts score clearly above average
- verdicts stay sharp but grounded
- platform recommendations feel plausible

### Negative test set
Prepare cases for:
- stale formula openings
- vulgar low-grade hooks
- heavy AI-manual-style prose
- naming pollution and terminology spam
- non-fiction content such as news copy or game guide text

Success criteria:
- low scores are applied consistently
- punishment platforms appear when appropriate
- verdict tone remains stable

### Protocol test set
Prepare output robustness tests for:
- fenced JSON
- raw JSON
- missing fields
- out-of-range numbers
- empty platform list
- typoed field names

## Improvement Plan
These are second-phase upgrades. They should improve reliability without changing the supplied prompt's philosophy.

### P0: structure hardening
- JSON schema validation
- numeric clamping
- platform percentage normalization
- standard error codes
- safer client fallbacks

### P1: two-pass generation
Use an internal hidden reasoning pass and a final strict-JSON pass.
Benefits:
- more stable structure
- more consistent scores
- fewer formatting failures

### P1: internal rule-hit logging
Add internal-only diagnostics such as:
- `lowGradeHook`
- `oldTrope`
- `visualPollution`
- `aiGeneratedFeel`
- `nonNovelContent`

Keep these in logs, not in the phase-one UI.

### P2: better preprocessing
Add input normalization before scoring:
- strip extreme whitespace noise
- detect obvious non-novel submissions
- detect pure garbage, repeated punctuation, or unreadable text
- truncate very long text intelligently while preserving opening hook sections

### P2: output-length guidance
Without changing the scoring core, add soft output limits:
- `editorVerdict`: one sentence
- `marketFit`: one sentence
- `strengths` and `weaknesses`: short bullet-like items
- each detailed analysis field: compact paragraph length

### P3: multi-provider compatibility layer
Standardize support for multiple provider styles, including:
- general hosted provider endpoints
- provider-native endpoints
- self-hosted model endpoints
- future internal provider implementations

## Phased Delivery Plan

### Phase 1: faithful replica
Deliver:
- provided `SYSTEM_PROMPT`
- `POST /api/analyze`
- strict output contract
- frontend rendering with existing fields
- minimal JSON validation

### Phase 2: stability upgrades
Deliver:
- schema validation
- score sanity checks
- platform normalization
- retry logic
- cleaner errors

### Phase 3: production readiness
Deliver:
- sample set regression tests
- prompt version tracking
- model-provider abstraction
- internal scoring diagnostics
- operational logging

## Final Recommendation
Use the provided prompt as the scoring constitution, reproduce the current `/api/analyze` contract first, and only then add reliability layers.

The winning implementation strategy for this project is:
1. prompt fidelity first
2. API compatibility second
3. validation layer third
4. optimization last

That path preserves the original product feel while turning a prompt-only prototype into a stable scoring system.
