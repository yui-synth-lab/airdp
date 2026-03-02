# AIRDP v3.0: Universal AI-Driven Pipeline
## AI-Driven Research & Development Process (Universal Edition)

**Version:** 3.0 (Python / Universal / Multilingual)
**Last Updated:** 2026-03-02

---

## 1. What is AIRDP? / AIRDPとは

**English:**
AIRDP is a framework for autonomous AI-driven workflows. It allows humans to provide "Seeds" (ideas/objectives), and AI agents autonomously verify, execute, and validate those tasks through a structured phase-gate process.

**日本語:**
AIRDP は、AIエージェントが自律的にタスクを検証・実行・評価する自律型ワークフロー・フレームワークです。人間が「Seed（アイデアや目標）」を提供し、AIエージェントが構造化されたフェーズゲートを通じて自律的に作業を進めます。

---

## 2. Architecture / アーキテクチャ

AIRDP follows a 5-phase structured lifecycle:

```
Phase 1: Seed     ← Human provides objectives in seed.md
Phase 2: Plan     ← Orchestrator generates roadmap.md
Phase 3: Execute  ← Iterative loop between Executor (Researcher) ↔ Validator (Reviewer)
Phase 4: Judge    ← Final arbiter (Judge) makes the final verdict
Phase 5: Report   ← Orchestrator generates a cycle report
```

---

## 3. Features / 主な特徴

- **Universal Lexicon (汎用用語集)**: Automatically adapts roles and terms (e.g., "Researcher" for Science, "Lead Developer" for Software) based on the domain.
- **Multilingual (多言語対応)**: Fully supports English and Japanese for both CLI and prompts.
- **Python Native (Pythonネイティブ)**: No more PowerShell dependency. Portable and easy to integrate.
- **SSoT (Single Source of Truth)**: Centralized management of project constraints, rules, and constants.

---

## 4. Getting Started / 使い方

### Step 1: Initialize Project
Run the interactive setup tool to define your domain, language, and goals.

```bash
python airdp_init.py
```

### Step 2: Define Objectives
Edit `cycles/cycle_01/seed.md` to describe what you want the AI to achieve.

### Step 3: Run the Pipeline
Run the main orchestrator to start the automated workflow.

```bash
python airdp_orchestrator.py
```

### Step 4: Resume/Specific Phases
You can resume from a specific phase or run only selected phases.

```bash
# Start from Phase 3 (Execution)
python airdp_orchestrator.py --start 3
```

---

## 5. Directory Structure / ディレクトリ構成

```
project_root/
├── airdp_init.py           # Project setup (Interactive)
├── airdp_core.py           # Core logic (AI & Prompt handling)
├── airdp_orchestrator.py   # Main pipeline hub
├── airdp_paper.py          # Document writing pipeline
├── airdp_prompts_v3/       # Multilingual prompt templates
│   ├── en/
│   └── jp/
├── ssot/                   # Single Source of Truth
│   ├── constants.json      # Project info, Lexicon, Limits
│   └── hypotheses/         # Objective definitions (JSON)
└── cycles/                 # Cycle work directories
    └── cycle_01/
        ├── seed.md         # Initial seed
        ├── roadmap.md      # Generated roadmap
        └── iterations/     # Phase 3 iterations
```

---

## 6. Document Pipeline / ドキュメント執筆

For writing papers, reports, or manuals, use the dedicated paper pipeline:

```bash
python airdp_paper.py --paper-dir papers/paper_01
```

---

## License
MIT License. Based on the KSAU Project legacy.
