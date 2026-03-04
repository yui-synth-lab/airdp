import re
import os
import sys
import shutil
import argparse
from pathlib import Path
from airdp_core import get_core
from airdp_orchestrator import _load_config, _parse_model_spec, _build_models


class AirdpPaper:
    def __init__(self, paper_dir, project_dir=".", models=None, max_revisions=5, start_revision=None):
        self.project_dir = Path(project_dir).resolve()
        self.paper_dir = self.project_dir / paper_dir
        self.models = models or _build_models(self.project_dir, {})
        self.max_revisions = max_revisions
        self.start_revision = start_revision
        self.core = get_core(self.project_dir)
        self.core.paths["session_dir"] = self.paper_dir / ".sessions"
        self.core.paths["log"] = self.paper_dir / "output_log.md"

    def _collect_cycle_reports(self):
        """cycles/ 配下の全 cycle_report.md のパスを新しい順に返す。"""
        cycles_dir = self.project_dir / "cycles"
        reports = sorted(
            cycles_dir.glob("cycle_*/cycle_report.md"),
            key=lambda p: p.parent.name
        )
        return reports

    def _run_brief_gate(self, brief_path):
        """brief.md を AI で生成し、go/edit/stop ゲートで人間が承認するまでループする。
        承認されれば True、停止なら False を返す。"""
        self.paper_dir.mkdir(parents=True, exist_ok=True)

        approved = False
        while not approved:
            # AI に brief を生成させる
            reports = self._collect_cycle_reports()
            cycle_reports_str = "\n".join(str(p) for p in reports) if reports else "(none)"

            orch = self.models["orchestrator"]
            orch_label = f"{orch['backend']}:{orch['model']}" if orch.get("model") else orch["backend"]
            print(f"\n  [Orchestrator: {orch_label}] Generating brief...")
            prompt = self.core.expand_prompt("paper_brief.md", {
                "BRIEF_PATH": brief_path,
                "SSOT_DIR": self.core.paths["ssot_dir"],
                "CYCLE_REPORTS": cycle_reports_str
            })
            self.core.invoke_ai(orch, prompt, role="paper_brief")

            if not brief_path.exists():
                print(f"  [ERROR] brief.md was not generated: {brief_path}")
                retry = input("  Retry? [y/n]: ").strip().lower()
                if retry != "y":
                    return False
                continue

            print(f"\n  Brief generated: {brief_path}")
            print()
            print("  [go]   → Start pipeline")
            print("  [edit] → Enter revision request and regenerate")
            print("  [stop] → Halt")

            while True:
                decision = input("\n  Decision [go/edit/stop]: ").strip().lower()

                if decision == "go":
                    approved = True
                    break

                elif decision == "edit":
                    edit_request = input("  Enter revision request: ").strip()
                    if not edit_request:
                        print("  Revision request is empty. Please try again.")
                        continue
                    edit_prompt = (
                        f"Apply the following revision and regenerate brief.md ({brief_path}).\n\n"
                        f"Revision:\n{edit_request}"
                    )
                    self.core.invoke_ai(self.models["orchestrator"], edit_prompt, role="paper_brief")
                    break  # 外側ループに戻って再確認

                elif decision == "stop":
                    print("  Halted.")
                    return False

                else:
                    print("  Please enter go / edit / stop.")

        return True

    def _detect_start_revision(self):
        """paper_dir 内の既存ファイルから再開すべき revision 番号を自動検出する。
        --start-revision が指定されていればそれを優先する。"""
        if self.start_revision is not None:
            return self.start_revision
        # draft_v{N}.md が存在する最大の N+1 から開始
        revision = 1
        while (self.paper_dir / f"draft_v{revision:02d}.md").exists():
            revision += 1
        return revision

    def run_pipeline(self):
        print(f"\n{'='*50}")
        print(f"  AIRDP v3.0 Paper Pipeline")
        print(f"{'='*50}")
        print(f"  Paper Dir   : {self.paper_dir}")
        def _label(spec): return f"{spec['backend']}:{spec['model']}" if spec.get("model") else spec["backend"]
        print(f"  Orchestrator: {_label(self.models['orchestrator'])}")
        print(f"  Writer      : {_label(self.models['writer'])}")
        print(f"  Reviewer    : {_label(self.models['reviewer'])}")
        print(f"{'-'*50}\n")

        brief_path = self.paper_dir / "brief.md"

        # ── Gate: brief.md の生成 → 人間承認 ──
        if not brief_path.exists():
            proceed = self._run_brief_gate(brief_path)
            if not proceed:
                return
        else:
            # 既存の brief.md がある場合も go/edit/stop で確認
            print(f"  Brief     : {brief_path}")
            print()
            print("  [go]   → Start pipeline with existing brief")
            print("  [edit] → Regenerate brief from cycle results")
            print("  [stop] → Halt")
            while True:
                decision = input("\n  Decision [go/edit/stop]: ").strip().lower()
                if decision == "go":
                    break
                elif decision == "edit":
                    brief_path.unlink()
                    proceed = self._run_brief_gate(brief_path)
                    if not proceed:
                        return
                    break
                elif decision == "stop":
                    print("  Halted.")
                    return
                else:
                    print("  Please enter go / edit / stop.")

        self.paper_dir.mkdir(parents=True, exist_ok=True)

        start_revision = self._detect_start_revision()
        if start_revision > 1:
            print(f"  [RESUME] Resuming from Revision {start_revision:02d} "
                  f"(found draft_v{start_revision-1:02d}.md + review_v{start_revision-1:02d}.md)")
        revision = start_revision
        limit = start_revision + self.max_revisions - 1
        finished = False
        while not finished:
            if revision > limit:
                print(f"[LIMIT] Reached maximum revisions ({self.max_revisions} from revision {start_revision:02d}).")
                break

            print(f"\n--- Revision {revision:02d} ---")
            draft_path = self.paper_dir / f"draft_v{revision:02d}.md"
            review_path = self.paper_dir / f"review_v{revision:02d}.md"
            prev_draft = self.paper_dir / f"draft_v{revision-1:02d}.md" if revision > 1 else ""
            prev_review = self.paper_dir / f"review_v{revision-1:02d}.md" if revision > 1 else ""

            # 1. Writer
            print(f"  [{self.core.constants['lexicon'].get('role_executor', 'Writer')}] Writing...")
            prev_draft_mtime = prev_draft.stat().st_mtime if prev_draft and Path(prev_draft).exists() else None
            writer_prompt = self.core.expand_prompt("paper_writer.md", {
                "BRIEF_PATH": brief_path,
                "DRAFT_PATH": draft_path,
                "PREV_DRAFT": prev_draft,
                "PREV_REVIEW": prev_review,
                "REVISION": revision,
                "PAPER_DIR": self.paper_dir,
                "SSOT_DIR": self.core.paths["ssot_dir"]
            })
            self.core.invoke_ai(self.models["writer"], writer_prompt, role=f"paper_writer_r{revision:02d}")

            if not draft_path.exists():
                # AI が別パスに書いた可能性を検索してリカバリ
                recovered = False
                # 1. prev_draft を上書きしたケース（mtime 変化で検出）
                if prev_draft and Path(prev_draft).exists() and prev_draft_mtime is not None:
                    if Path(prev_draft).stat().st_mtime != prev_draft_mtime:
                        print(f"  [RECOVER] AI overwrote {prev_draft}, copying to {draft_path}")
                        shutil.copy2(prev_draft, draft_path)
                        recovered = True
                # 2. ゼロ埋めなし等の別名パターンに書いたケース（paper_dir 内を探す）
                if not recovered:
                    candidates = [
                        self.paper_dir / f"draft_v{revision}.md",       # draft_v1.md
                        self.paper_dir / f"draft_v{revision:02d}.md",   # draft_v01.md (念のため)
                        self.paper_dir / f"draft_{revision:02d}.md",    # draft_01.md
                        self.paper_dir / f"draft_{revision}.md",        # draft_1.md
                    ]
                    for candidate in candidates:
                        if candidate != draft_path and candidate.exists():
                            print(f"  [RECOVER] AI wrote to {candidate}, moving to {draft_path}")
                            shutil.move(str(candidate), draft_path)
                            recovered = True
                            break
                if not recovered:
                    print(f"  [ERROR] Draft was not generated. Stopping.")
                    break

            # 2. Reviewer
            print(f"  [{self.core.constants['lexicon'].get('role_validator', 'Reviewer')}] Reviewing...")
            reviewer_prompt = self.core.expand_prompt("paper_reviewer.md", {
                "BRIEF_PATH": brief_path,
                "DRAFT_PATH": draft_path,
                "REVIEW_PATH": review_path,
                "REVISION": revision,
                "SSOT_DIR": self.core.paths["ssot_dir"]
            })
            self.core.invoke_ai(self.models["reviewer"], reviewer_prompt, role=f"paper_reviewer_r{revision:02d}")

            if not review_path.exists():
                # ゼロ埋めなし等の別名パターンに書いたケースを検索
                review_candidates = [
                    self.paper_dir / f"review_v{revision}.md",
                    self.paper_dir / f"review_{revision:02d}.md",
                    self.paper_dir / f"review_{revision}.md",
                ]
                review_recovered = False
                for candidate in review_candidates:
                    if candidate != review_path and candidate.exists():
                        print(f"  [RECOVER] AI wrote to {candidate}, moving to {review_path}")
                        shutil.move(str(candidate), review_path)
                        review_recovered = True
                        break
                if not review_recovered:
                    print(f"  [ERROR] Review report was not generated. Stopping.")
                    break

            # 3. Decision
            review_content = review_path.read_text(encoding="utf-8")
            if re.search(r"VERDICT\W+ACCEPT", review_content):
                print(f"\n[ACCEPTED] Revision {revision:02d} approved!")
                print(f"  Final document: {draft_path}")
                print(f"  Rename to 'paper_final.md' when ready.")
                finished = True
            elif re.search(r"VERDICT\W+STOP", review_content):
                print(f"\n[STOPPED] Revision {revision:02d} — fatal issue detected by reviewer.")
                print(f"  See review: {review_path}")
                break
            elif re.search(r"VERDICT\W+REVISE", review_content):
                print(f"\n[REVISE] Revision {revision:02d} needs work. Moving to next revision.")
                revision += 1
            else:
                print(f"\n[ERROR] No VERDICT found in review. Stopping.")
                print(f"  Expected pattern: 'VERDICT: ACCEPT', 'VERDICT: REVISE', or 'VERDICT: STOP'")
                break


def main():
    parser = argparse.ArgumentParser(
        description="AIRDP v3.0 Paper Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Model spec format: backend[:model]\n"
            "  e.g. gemini                  → use backend default from airdp_config.json\n"
            "       gemini:gemini-2.5-pro   → override model explicitly\n"
            "       claude:claude-opus-4-5  → override model explicitly\n"
            "\nDefaults are loaded from airdp_config.json (project-dir first, then framework dir)."
        )
    )
    parser.add_argument("--paper-dir", required=True, help="Directory for the paper (relative to project root)")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--orchestrator", default=None, help="AI for brief generation. Format: backend[:model]")
    parser.add_argument("--writer", default=None, help="AI for writing. Format: backend[:model]")
    parser.add_argument("--reviewer", default=None, help="AI for reviewing. Format: backend[:model]")
    parser.add_argument("--max-revisions", type=int, default=5)
    parser.add_argument("--start-revision", type=int, default=None,
                        help="Revision number to start from (default: auto-detect from existing files)")

    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve()

    cli_overrides = {
        "orchestrator": args.orchestrator,
        "writer": args.writer,
        "reviewer": args.reviewer,
    }
    models = _build_models(project_dir, cli_overrides, roles=("orchestrator", "writer", "reviewer"))

    pipeline = AirdpPaper(
        paper_dir=args.paper_dir,
        project_dir=args.project_dir,
        models=models,
        max_revisions=args.max_revisions,
        start_revision=args.start_revision
    )
    pipeline.run_pipeline()


if __name__ == "__main__":
    main()
