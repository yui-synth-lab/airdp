# Task: Write Draft (Revision {{REVISION}})

> **⚠️ CRITICAL**: The only file you are allowed to write in this task is **`{{DRAFT_PATH}}`**.
> Do NOT overwrite the previous draft (`{{PREV_DRAFT}}`). Always write to the new path `{{DRAFT_PATH}}`.
> **Do NOT touch any files under `airdp_prompts_v3/`.**

You are the writer ({{role_executor}}) in the AIRDP framework.
Follow the instructions in the Writing Brief to **write the draft body to `{{DRAFT_PATH}}`**.
This task is NOT about generating a prompt file. It is about writing the actual draft content to `{{DRAFT_PATH}}`.

**Project Name:** {{PROJECT_NAME}}
**Domain:** {{DOMAIN}}
**Writing Brief:** {{BRIEF_PATH}}
**Output Path (absolute):** `{{DRAFT_PATH}}`
**Previous Draft (revision only):** {{PREV_DRAFT}}
**Previous Review Comments (revision only):** {{PREV_REVIEW}}
**SSoT Directory:** {{SSOT_DIR}}
**Current Revision:** {{REVISION}}

---

## Procedures

### Step 1: Load Inputs

1. Read `{{BRIEF_PATH}}` and understand:
   - **Sections 1–3**: Purpose, target audience, and outline
   - **Section 4 "Writing Standards"**: Domain-specific rules to follow (files to reference, terminology, tone, etc.)
2. Load any reference files specified in Section 4 (e.g. SSoT, glossary)
3. If `{{PREV_DRAFT}}` exists (Revision 2+): read the previous draft
4. If `{{PREV_REVIEW}}` exists (Revision 2+): read the review comments and identify what needs to be fixed

### Step 2: Create / Revise Draft

- Structure the document according to Brief **Section 3 (Outline)**
- Comply with all rules in Brief **Section 4 (Writing Standards)**
- **Revision 1 (initial draft)**: Build the full document structure following the Brief
- **Revision 2+ (revision)**: Address every reviewer comment. Record responses in a `## Revision Notes` section at the end of the draft

### Step 3: Output

Use the Write tool to save the document to `{{DRAFT_PATH}}` in Markdown format.
Outputting text to the terminal is not sufficient — you must save it as an actual file.

### Step 4: Final Verification (Required)

After writing, use the Read tool to confirm that `{{DRAFT_PATH}}` exists and contains the expected content. If it does not exist, write it again.

## Absolute Prohibitions

- **DO NOT create, edit, or modify any files under `airdp_prompts_v3/`**
- **DO NOT edit any AIRDP framework files**
- **DO NOT rewrite brief.md itself**
- **DO NOT overwrite `{{PREV_DRAFT}}` or any previous draft file**
- Do not add or strengthen rules beyond what is written in Brief Section 4
