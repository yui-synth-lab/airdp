import os
import json
import sys
from pathlib import Path
from airdp_core import invoke_ai_simple

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def ask(question, options=None, default=None):
    print(f"\n[?] {question}")
    if options:
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        while True:
            choice = input(f"Select (1-{len(options)}) [{'default:'+str(default) if default else ''}]: ").strip()
            if not choice and default:
                return default
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice)-1]
    else:
        ans = input(f"Input [{'default:'+str(default) if default else ''}]: ").strip()
        return ans if ans else default

def invoke_ai_init(ai_name, prompt):
    """初期化用 AI 呼び出し。invoke_ai_simple を使い JSON を抽出して返す。"""
    print(f"\n[AI: {ai_name}] プロジェクトの性質を分析中...")
    try:
        output = invoke_ai_simple(ai_name, prompt)
        if "{" in output:
            json_str = output[output.find("{"):output.rfind("}")+1]
            return json.loads(json_str)
        return None
    except Exception as e:
        print(f"[ERROR] AI分析に失敗しました ({ai_name}): {e}")
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AIRDP v3.0 Project Initializer")
    parser.add_argument("--ai", default="gemini", help="AI model to use for profiling (e.g., gemini, claude)")
    args = parser.parse_args()

    clear_screen()
    print("========================================")
    print("   AIRDP v3.0: AI-Powered Architect")
    print("========================================\n")

    # ... (言語、プロジェクト名、説明のヒアリングは共通)

    # 0. 言語の選択
    lang = ask("Language / 言語", options=["English", "日本語"], default="English")
    is_jp = (lang == "日本語")

    # 1. 基本ヒアリング
    project_name = ask("Project Name", default="my_universal_project")
    description = ask("Description / 目標 (例: 江戸時代の歴史小説を書きたい、ReactでToDoアプリを作りたい等)")

    # 2. AIによるプロファイリング（メタプロンプト）
    meta_prompt = f"""
    You are a Project Architect for the AIRDP framework.
    Task: Design the optimal Lexicon (terminology), constraints, and domain-specific quality rules for this project.
    Project Description: {description}
    Language: {lang}

    Output ONLY a valid JSON object with the following keys:
    - "domain": A concise name for this domain.
    - "lexicon": {{
        "role_executor": "The specific title for the person doing the work (e.g., 'Historical Writer', 'Frontend Developer')",
        "role_validator": "The specific title for the person checking the work (e.g., 'Historical Consultant', 'Senior QA')",
        "unit_objective": "What is being produced in each iteration (e.g., 'Chapter', 'Component', 'Module')",
        "unit_criteria": "How to measure quality (e.g., 'Historical accuracy', 'Unit tests passing')",
        "ssot_name": "What the source of truth is called (e.g., 'Chronology', 'Tech Specs')"
      }},
    - "suggested_success_criteria": ["Criterion 1", "Criterion 2"],
    - "suggested_exit_criteria": ["When to stop 1", "When to stop 2"],
    - "domain_quality_rules": {{
        "researcher_prohibitions": [
          "List 3-5 things the Executor must NEVER do in this domain.",
          "Be specific and detectable (e.g., 'Using modern vocabulary in historical fiction', 'Asserting unverified facts as truth')."
        ],
        "reviewer_checklist": [
          "List 5-8 yes/no checklist items the Validator uses to judge deliverables.",
          "Each item must be answerable with yes or no (e.g., 'Does the text contain anachronistic language?')."
        ],
        "judge_accept_criteria": [
          "List 3-5 binary conditions ALL of which must be true for ACCEPT.",
          "Be concrete and verifiable (e.g., 'All reviewer checklist items passed', 'No contradiction with SSoT')."
        ],
        "common_failure_patterns": [
          "List 3-5 domain-specific failure patterns that look correct but are actually wrong.",
          "Examples: 'Mixing modern idioms into Edo-period dialogue', 'Circular reasoning with synthetic data', 'Reporting untested code as working'."
        ]
      }}
    """
    
    config = invoke_ai_init(args.ai, meta_prompt)
    
    if not config:
        print("[WARNING] AI分析に失敗したため、デフォルト設定を使用します。")
        config = {
            "domain": "General",
            "lexicon": {
                "role_executor": "Executor",
                "role_validator": "Validator",
                "unit_objective": "Objective",
                "unit_criteria": "Quality Metrics",
                "ssot_name": "Source of Truth"
            },
            "suggested_success_criteria": ["Requirement satisfied"],
            "suggested_exit_criteria": ["Logical failure"],
            "domain_quality_rules": {
                "researcher_prohibitions": [
                    "SSoT に定義されていない事実の断定的記述",
                    "ロードマップに記載のないタスクの自己判断による追加"
                ],
                "reviewer_checklist": [
                    "SSoT の制約と成果物が矛盾していないか",
                    "ロードマップのタスクが完全に完了しているか",
                    "根拠のない主張が含まれていないか"
                ],
                "judge_accept_criteria": [
                    "全 Reviewer チェック項目をクリアしていること",
                    "SSoT との矛盾がゼロであること"
                ],
                "common_failure_patterns": [
                    "表面的には完成しているが検証が不十分な成果物",
                    "指摘への対応が部分的でありながら完了と報告する"
                ]
            }
        }

    # 3. ディレクトリ作成
    lang_code = "jp" if is_jp else "en"
    root = Path(os.getcwd())
    dirs = [
        f"airdp_prompts_v3/{lang_code}",
        "ssot/hypotheses",
        "cycles/cycle_01",
        "audit/communication",
        "data"
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    # 4. constants.json の生成
    constants = {
        "project_info": {
            "name": project_name,
            "domain": config["domain"],
            "description": description,
            "language": lang_code
        },
        "lexicon": config["lexicon"],
        "pipeline_limits": {
            "max_objectives_per_cycle": 3,
            "max_iterations_per_objective": 10,
            "consecutive_stop_limit": 2
        },
        "domain_quality_rules": config["domain_quality_rules"]
    }
    with open(root / "ssot" / "constants.json", "w", encoding="utf-8") as f:
        json.dump(constants, f, indent=2, ensure_ascii=False)

    # domain_quality_rules の確認ゲート
    print("\n[確認] 生成されたドメイン品質ルールを確認してください:")
    print(json.dumps(config["domain_quality_rules"], indent=2, ensure_ascii=False))
    print("\n  [ok]   → このまま続行")
    print("  [edit] → constants.json を手動編集後に続行")
    while True:
        gate = input("\n  確認 [ok/edit]: ").strip().lower()
        if gate == "ok":
            break
        elif gate == "edit":
            input("  ssot/constants.json の domain_quality_rules を編集後、Enter を押してください。")
            # 編集後の値を再読み込み
            with open(root / "ssot" / "constants.json", "r", encoding="utf-8") as f:
                constants = json.load(f)
            config["domain_quality_rules"] = constants.get("domain_quality_rules", {})
            break
        else:
            print("  ok または edit を入力してください。")

    # 5. 初期 seed.md の作成（AIの提案を含む）
    success_str = "\n".join([f"- {c}" for c in config.get("suggested_success_criteria", [])])
    exit_str = "\n".join([f"- {c}" for c in config.get("suggested_exit_criteria", [])])
    
    if is_jp:
        seed_content = f"""# Seed: Cycle 01 — {project_name}

## 1. 核心的な目標 (Core Objectives)
1. 

## 2. 背景 / コンテキスト
{description}

## 3. 境界条件 (撤退・却下基準)
{exit_str}

## 4. 成功基準 (Success Criteria)
{success_str}
"""
    else:
        seed_content = f"""# Seed: Cycle 01 — {project_name}

## 1. Core Objectives
1. 

## 2. Background / Context
{description}

## 3. Boundary (When to stop/reject)
{exit_str}

## 4. Success Criteria
{success_str}
"""
    with open(root / "cycles" / "cycle_01" / "seed.md", "w", encoding="utf-8") as f:
        f.write(seed_content)

    # 6. idea_queue.md の作成（既存の場合はスキップ）
    idea_queue_path = root / "idea_queue.md"
    if not idea_queue_path.exists():
        if is_jp:
            idea_queue_path.write_text(
                "# Idea Queue\n\n"
                "Phase 3 実行中に思いついたアイデアをここに追記してください。\n"
                "現在のサイクルには影響しません。Phase 5 で次サイクルの seed.md 候補として参照されます。\n\n"
                "---\n\n"
                "<!-- 例: - フィルター処理を並列化して速度を改善する -->\n",
                encoding="utf-8"
            )
        else:
            idea_queue_path.write_text(
                "# Idea Queue\n\n"
                "Add ideas here during Phase 3 execution.\n"
                "These do not affect the current cycle. They will be referenced in Phase 5 as candidates for the next cycle's seed.md.\n\n"
                "---\n\n"
                "<!-- Example: - Parallelize filter processing to improve speed -->\n",
                encoding="utf-8"
            )
        print(f"[Init] Created: idea_queue.md")

    # 7. AI コンテキストファイルの生成
    generate_ai_context_files(root, constants)

    print(f"\n[SUCCESS] Project '{project_name}' initialized by AI Architect!")
    print(f"  - Domain: {config['domain']}")
    print(f"  - Role: {config['lexicon']['role_executor']} & {config['lexicon']['role_validator']}")
    print(f"  - SSoT Name: {config['lexicon']['ssot_name']}")
    print("\nCheck 'ssot/constants.json' for full configuration.")


def generate_ai_context_files(root: Path, constants: dict):
    """各 AI CLI が自動読み込みするコンテキストファイルを生成する。既存ファイルは上書きしない。"""

    info = constants.get("project_info", {})
    lex  = constants.get("lexicon", {})
    lim  = constants.get("pipeline_limits", {})

    content = f"""# AIRDP Project Context

## Project
- Name   : {info.get('name', '')}
- Domain : {info.get('domain', '')}
- Goal   : {info.get('description', '')}
- Language: {info.get('language', 'en')}

## Roles (Lexicon)
- Executor  : {lex.get('role_executor', 'Executor')}
- Validator : {lex.get('role_validator', 'Validator')}
- Objective : {lex.get('unit_objective', 'Objective')}
- Criteria  : {lex.get('unit_criteria', 'Quality Metrics')}
- SSoT Name : {lex.get('ssot_name', 'Source of Truth')}

## Key Paths
- SSoT      : ssot/constants.json
- Cycle dir : cycles/cycle_XX/
- Roadmap   : cycles/cycle_XX/roadmap.md
- Iterations: cycles/cycle_XX/iterations/iter_XX/
- Decision  : cycles/cycle_XX/go.md  (approved) / ng.md (rejected)

## Pipeline Rules
- Max iterations per objective : {lim.get('max_iterations_per_objective', 5)}
- Max objectives per cycle     : {lim.get('max_objectives_per_cycle', 3)}
- NO hardcoding: all constants must come from ssot/constants.json
- Each phase is invoked separately by the Python orchestrator. You are called ONCE per phase.
- Execute ONLY the task described in the prompt you received. Do NOT proceed to other phases.
- Executor produces work; Validator writes go.md (CONTINUE) or ng.md (MODIFY/STOP)

## Security & Tool Permissions
- All filesystem operations are pre-approved via --approval-mode=yolo.
- You are allowed and encouraged to use 'write_file', 'replace', and 'run_shell_command' to complete your tasks.
- Non-interactive mode is active; do not wait for user confirmation.

## File Write Rules (ALWAYS ENFORCE)
- The output file path is always specified explicitly in the prompt you receive. Write ONLY to that exact path.
- NEVER write to a different path of your own choosing, even if a similarly named file already exists elsewhere.
- NEVER overwrite a previous draft or review file. Each revision gets its own new file (e.g. draft_v02.md, not draft_v01.md).
- Use the exact filename given, including zero-padded numbers (e.g. draft_v01.md, NOT draft_v1.md).
- NEVER create or modify any files under airdp_prompts_v3/. Those are framework files.
- After writing, verify the file exists by reading it back. If it does not exist, write it again.
"""

    files = [
        root / "GEMINI.md",
        root / "CLAUDE.md",
        root / "AGENTS.md",
        root / ".github" / "copilot-instructions.md",
    ]

    created = []
    skipped = []
    for path in files:
        if path.exists():
            skipped.append(path.name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path.relative_to(root))

    if created:
        print(f"\n[AI Context] Created: {', '.join(str(p) for p in created)}")
    if skipped:
        print(f"[AI Context] Skipped (already exist): {', '.join(skipped)}")


if __name__ == "__main__":
    main()
