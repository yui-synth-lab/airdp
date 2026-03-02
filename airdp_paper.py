import re
import os
import sys
import argparse
from pathlib import Path
from airdp_core import get_core


class AirdpPaper:
    def __init__(self, paper_dir, project_dir=".", orchestrator="gemini", writer="gemini", reviewer="claude", max_revisions=5):
        self.project_dir = Path(project_dir).resolve()
        self.paper_dir = self.project_dir / paper_dir
        self.orchestrator = orchestrator
        self.writer = writer
        self.reviewer = reviewer
        self.max_revisions = max_revisions
        self.core = get_core(self.project_dir)

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

            print(f"\n  [Orchestrator: {self.orchestrator}] Generating brief...")
            prompt = self.core.expand_prompt("paper_brief.md", {
                "BRIEF_PATH": brief_path,
                "SSOT_DIR": self.core.paths["ssot_dir"],
                "CYCLE_REPORTS": cycle_reports_str
            })
            self.core.invoke_ai(self.orchestrator, prompt, role="paper_brief")

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
                    self.core.invoke_ai(self.orchestrator, edit_prompt, role="paper_brief")
                    break  # 外側ループに戻って再確認

                elif decision == "stop":
                    print("  Halted.")
                    return False

                else:
                    print("  Please enter go / edit / stop.")

        return True

    def run_pipeline(self):
        print(f"\n{'='*50}")
        print(f"  AIRDP v3.0 Paper Pipeline")
        print(f"{'='*50}")
        print(f"  Paper Dir   : {self.paper_dir}")
        print(f"  Orchestrator: {self.orchestrator}")
        print(f"  Writer      : {self.writer}")
        print(f"  Reviewer    : {self.reviewer}")
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

        revision = 1
        finished = False
        while not finished:
            if revision > self.max_revisions:
                print(f"[LIMIT] Reached maximum revisions ({self.max_revisions}).")
                break

            print(f"\n--- Revision {revision:02d} ---")
            draft_path = self.paper_dir / f"draft_v{revision:02d}.md"
            review_path = self.paper_dir / f"review_v{revision:02d}.md"
            prev_draft = self.paper_dir / f"draft_v{revision-1:02d}.md" if revision > 1 else ""
            prev_review = self.paper_dir / f"review_v{revision-1:02d}.md" if revision > 1 else ""

            # 1. Writer
            print(f"  [{self.core.constants['lexicon'].get('role_executor', 'Writer')}] Writing...")
            writer_prompt = self.core.expand_prompt("paper_writer.md", {
                "BRIEF_PATH": brief_path,
                "DRAFT_PATH": draft_path,
                "PREV_DRAFT": prev_draft,
                "PREV_REVIEW": prev_review,
                "REVISION": revision,
                "PAPER_DIR": self.paper_dir,
                "SSOT_DIR": self.core.paths["ssot_dir"]
            })
            self.core.invoke_ai(self.writer, writer_prompt, role="paper_writer")

            if not draft_path.exists():
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
            self.core.invoke_ai(self.reviewer, reviewer_prompt, role="paper_reviewer")

            if not review_path.exists():
                print(f"  [ERROR] Review report was not generated. Stopping.")
                break

            # 3. Decision
            review_content = review_path.read_text(encoding="utf-8")
            if re.search(r"VERDICT\W+ACCEPT", review_content):
                print(f"\n[ACCEPTED] Revision {revision:02d} approved!")
                print(f"  Final document: {draft_path}")
                print(f"  Rename to 'paper_final.md' when ready.")
                finished = True
            elif re.search(r"VERDICT\W+REVISE", review_content):
                print(f"\n[REVISE] Revision {revision:02d} needs work. Moving to next revision.")
                revision += 1
            else:
                print(f"\n[ERROR] No VERDICT found in review. Stopping.")
                print(f"  Expected pattern: 'VERDICT: ACCEPT' or 'VERDICT: REVISE'")
                break


def main():
    parser = argparse.ArgumentParser(description="AIRDP v3.0 Paper Pipeline")
    parser.add_argument("--paper-dir", required=True, help="Directory for the paper (relative to project root)")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--orchestrator", default="gemini", help="AI for brief generation")
    parser.add_argument("--writer", default="gemini")
    parser.add_argument("--reviewer", default="claude")
    parser.add_argument("--max-revisions", type=int, default=5)

    args = parser.parse_args()

    pipeline = AirdpPaper(
        paper_dir=args.paper_dir,
        project_dir=args.project_dir,
        orchestrator=args.orchestrator,
        writer=args.writer,
        reviewer=args.reviewer,
        max_revisions=args.max_revisions
    )
    pipeline.run_pipeline()


if __name__ == "__main__":
    main()
