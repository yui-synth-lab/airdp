# Paper Brief Generation Prompt

> **⚠️ CRITICAL**: The only file you are allowed to write in this task is **`{{BRIEF_PATH}}`**.
> Writing to any other path — including any existing brief.md — is strictly forbidden.

You are the Orchestrator of the AIRDP framework.
Based on the accumulated cycle results, create a writing brief for the paper/document pipeline.

**Project Name:** {{PROJECT_NAME}}
**Domain:** {{DOMAIN}}
**Ultimate Goal:** {{GOAL}}
**SSoT Directory:** {{SSOT_DIR}}
**Cycle Reports to Reference:** {{CYCLE_REPORTS}}
**Output Path (absolute):** `{{BRIEF_PATH}}`

---

## Procedures

### Step 1: Load Inputs

1. Read `{{SSOT_DIR}}/constants.json` to understand project terminology and constraints
2. Read all cycle reports listed in `{{CYCLE_REPORTS}}` to understand:
   - Accumulated results and confirmed findings
   - Rules and constants added to the SSoT
   - Unresolved issues and directions for the next step
3. If any cycle report contains an "## Iteration Deliverables Index" table, **read every deliverable file path listed in that table**. This table is the index to actual iteration outputs. The outline in brief Section 3 must be based on the **actual content of each iter file**, not on the cycle_report summary alone.

### Step 2: Create brief.md

**Write** `{{BRIEF_PATH}}` to disk using the Write tool (or equivalent file-write command).
Outputting text to the terminal is not sufficient — you must save it as an actual file at `{{BRIEF_PATH}}`.

Use the following structure:

```markdown
# Writing Brief

## 1. Purpose
[What this document aims to achieve. State the relationship to cycle results.]

## 2. Target Audience
[Who this is written for]

## 3. Structure / Outline
[Sections to include and key points for each]
1. ...
2. ...

## 4. Writing Standards (Domain-Specific Rules)
[Rules the {{role_executor}} must follow]
- Reference files: [List specific file paths under SSoT]
- Terminology: Use terms defined in {{ssot_name}}
- Tone / Style: [Specific instructions suited to the domain]
- (Other domain-specific rules)

## 5. Review Standards (Domain-Specific Rules)
[Checklist the {{role_validator}} uses to decide ACCEPT/REVISE]
- [ ] [Specific check item]
- [ ] ...

## 6. Notes
[Any supplementary information]
```

## Absolute Prohibitions

- **DO NOT edit any AIRDP framework files**
- **DO NOT modify `ssot/constants.json`**
- Your sole output for this phase is `{{BRIEF_PATH}}`

### Step 3: Final Verification (Required)

After writing with the Write tool, use the Read tool to confirm that `{{BRIEF_PATH}}` exists and contains the expected content. If it does not exist, write it again.
