import os
import sys
import argparse
from pathlib import Path
from airdp_core import get_core


class AirdpOrchestrator:
    def __init__(self, project_dir=".", cycle_id="auto", models=None, start_phase=2, end_phase=5,
                 skip_approval=False):
        self.project_dir = Path(project_dir).resolve()
        self.models = models or {
            "orchestrator": "gemini",
            "researcher": "gemini",
            "reviewer": "claude",
            "judge": "claude"
        }
        self.cycle_id = self._resolve_cycle_id(cycle_id)
        self.core = get_core(self.project_dir, self.cycle_id)
        self.start_phase = start_phase
        self.end_phase = end_phase
        self.skip_approval = skip_approval

    def _resolve_cycle_id(self, cycle_id):
        cycles_dir = self.project_dir / "cycles"
        cycles_dir.mkdir(parents=True, exist_ok=True)

        if cycle_id == "auto":
            existing = sorted([d.name for d in cycles_dir.iterdir()
                                if d.is_dir() and d.name.startswith("cycle_")])
            if not existing:
                return "01"
            # Use latest existing cycle (do not create new)
            return existing[-1].replace("cycle_", "")
        if cycle_id == "new":
            existing = sorted([d.name for d in cycles_dir.iterdir()
                                if d.is_dir() and d.name.startswith("cycle_")])
            last_num = int(existing[-1].replace("cycle_", "")) if existing else 0
            return f"{last_num + 1:02d}"
        return cycle_id

    def run_pipeline(self):
        print(f"\n{'='*50}")
        print(f"  AIRDP v3.0 Pipeline Start: Cycle {self.cycle_id}")
        print(f"{'='*50}")
        print(f"  Project : {self.core.constants.get('project_info', {}).get('name')}")
        print(f"  Domain  : {self.core.constants.get('project_info', {}).get('domain')}")
        print(f"  Range   : Phase {self.start_phase} to {self.end_phase}")
        print(f"  Models  : {self.models}")
        print(f"{'-'*50}\n")

        if self.start_phase <= 2 <= self.end_phase:
            proceed = self.run_phase_2()
            if not proceed:
                print("\n[STOPPED] Pipeline halted at Phase 2.")
                return

        if self.start_phase <= 3 <= self.end_phase:
            self.run_phase_3()

        if self.start_phase <= 4 <= self.end_phase:
            self.run_phase_4()

        if self.start_phase <= 5 <= self.end_phase:
            self.run_phase_5()

        print(f"\n[COMPLETE] Cycle {self.cycle_id} processing finished.")

    # ── Phase 2: Plan ──────────────────────────────────────────────────

    def run_phase_2(self):
        """Generate roadmap and obtain human approval via go/edit/stop gate.
        Returns True to proceed, False to halt."""
        print(f"\n>>> Phase 2: Planning (Orchestrator: {self.models['orchestrator']})")

        seed_path = self.core.paths["cycle_dir"] / "seed.md"
        if not seed_path.exists():
            print(f"  [ERROR] seed.md not found at {seed_path}")
            print("  Please create seed.md (Phase 1) before running Phase 2.")
            return False

        approved = False
        while not approved:
            prompt = self.core.expand_prompt("orchestrator_phase2.md", {
                "SEED_PATH": self.core.paths["cycle_dir"] / "seed.md",
                "cycle_id": self.cycle_id,
                "max_iterations_per_objective": self.core.constants.get("pipeline_limits", {}).get("max_iterations_per_objective", 10)
            })
            self.core.invoke_ai(self.models["orchestrator"], prompt, role="orchestrator_phase2")

            roadmap_path = self.core.paths["roadmap"]
            if not roadmap_path.exists():
                print(f"  [ERROR] roadmap.md was not generated: {roadmap_path}")
                retry = input("  Retry? [y/n]: ").strip().lower()
                if retry != "y":
                    return False
                continue

            print(f"\n  Roadmap generated: {roadmap_path}")

            if self.skip_approval:
                print("  [skip_approval] Proceeding to Phase 3.")
                return True

            # ── Gate ──
            print("\n  [go]   → Proceed to Phase 3")
            print("  [edit] → Enter revision request and regenerate")
            print("  [stop] → Halt pipeline")

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
                        f"Apply the following revision and regenerate roadmap.md ({roadmap_path}).\n\n"
                        f"Revision:\n{edit_request}"
                    )
                    self.core.invoke_ai(self.models["orchestrator"], edit_prompt,
                                        role="orchestrator_phase2")
                    break  # Return to outer loop for re-review after regeneration

                elif decision == "stop":
                    print("  Halted.")
                    return False

                else:
                    print("  Please enter go / edit / stop.")

        return True

    # ── Phase 3: Execute ───────────────────────────────────────────────

    def run_phase_3(self):
        print(f"\n>>> Phase 3: Execution "
              f"(Researcher: {self.models['researcher']} / Reviewer: {self.models['reviewer']})")
        print("  * Press Ctrl+C for emergency stop → proceed to Phase 4 (Judge)")

        limits = self.core.constants.get("pipeline_limits", {})
        max_iters = limits.get("max_iterations_per_objective", 10)
        iteration = 1

        # Find resume point if iterations already exist
        cycle_complete_path = self.core.paths["cycle_dir"] / "cycle_complete.md"
        if cycle_complete_path.exists():
            print("  [SKIP] Cycle already complete (cycle_complete.md found).")
            return

        go_path = self.core.paths["cycle_dir"] / "go.md"
        ng_path = self.core.paths["cycle_dir"] / "ng.md"

        if self.core.paths["iterations"].exists():
            existing = sorted([
                d.name for d in self.core.paths["iterations"].iterdir()
                if d.is_dir() and d.name.startswith("iter_")
            ])
            if existing:
                iteration = int(existing[-1].replace("iter_", ""))
                if go_path.exists():
                    go_path.unlink()
                    iteration += 1
                    print(f"  [RESUME] Previously approved → resuming from Iteration {iteration:02d}")
                elif ng_path.exists():
                    ng_path.unlink()
                    print(f"  [RESUME] Previously rejected → retrying Iteration {iteration:02d}")

        finished = False
        try:
            while not finished:
                if iteration > max_iters:
                    print(f"  [LIMIT] Reached maximum iterations ({max_iters}).")
                    break

                print(f"\n--- Iteration {iteration:02d} ---")
                iter_dir = self.core.paths["iterations"] / f"iter_{iteration:02d}"
                iter_dir.mkdir(parents=True, exist_ok=True)
                (iter_dir / "code").mkdir(exist_ok=True)

                # 1. Researcher
                print(f"  [{self.core.constants['lexicon']['role_executor']}] Working...")
                res_prompt = self.core.expand_prompt("researcher.md", {
                    "ITER_DIR": iter_dir,
                    "NG_PATH": ng_path,
                    "GO_PATH": go_path
                })
                self.core.invoke_ai(self.models["researcher"], res_prompt, role="researcher")

                # 2. Reviewer
                print(f"  [{self.core.constants['lexicon']['role_validator']}] Reviewing...")
                rev_prompt = self.core.expand_prompt("reviewer.md", {
                    "ITER_DIR": iter_dir,
                    "CYCLE_COMPLETE_PATH": cycle_complete_path
                })
                self.core.invoke_ai(self.models["reviewer"], rev_prompt, role="reviewer")

                # 3. Decision
                if cycle_complete_path.exists():
                    print(f"  [COMPLETE] All iterations done. Proceeding to Phase 4.")
                    finished = True
                elif go_path.exists():
                    print(f"  [APPROVED] Iteration {iteration:02d} cleared. Continuing to next.")
                    go_path.unlink()
                    iteration += 1
                elif ng_path.exists():
                    print(f"  [REJECTED] Addressing issues in next iteration.")
                    ng_path.unlink()
                    iteration += 1
                else:
                    print("  [ERROR] No decision file (go.md/ng.md/cycle_complete.md) found. Stopping.")
                    finished = True

        except KeyboardInterrupt:
            self._handle_emergency_stop()

    def _handle_emergency_stop(self):
        """Handle Ctrl+C emergency stop. Log reason and proceed to Phase 4."""
        import datetime
        print("\n\n  [EMERGENCY STOP] Ctrl+C detected.")
        reason = input("  Enter stop reason (optional): ").strip()

        stop_dir = self.project_dir / "audit" / "emergency_stops"
        stop_dir.mkdir(parents=True, exist_ok=True)
        stop_path = stop_dir / f"emergency_stop_cycle{self.cycle_id}.md"

        content = (
            f"# Emergency Stop — Cycle {self.cycle_id}\n\n"
            f"**Timestamp:** {datetime.datetime.now().isoformat()}\n"
            f"**Reason:** {reason or '(not provided)'}\n\n"
            f"Proceeding directly to Phase 4 (Judge).\n"
        )
        stop_path.write_text(content, encoding="utf-8")
        print(f"  [LOGGED] {stop_path}")
        print("  Proceeding to Phase 4 (Judge)...")

    # ── Phase 4: Judge ────────────────────────────────────────────────

    def run_phase_4(self):
        print(f"\n>>> Phase 4: Judging (Judge: {self.models['judge']})")
        prompt = self.core.expand_prompt("judge_phase4.md", {
            "ITERATIONS_DIR": self.core.paths["iterations"]
        })
        self.core.invoke_ai(self.models["judge"], prompt, role="judge")
        verdict_path = self.core.paths["cycle_dir"] / "verdict.md"
        if verdict_path.exists():
            print(f"  Final verdict: {verdict_path}")
        else:
            print(f"  [WARNING] verdict.md not found.")

    # ── Phase 5: Report ───────────────────────────────────────────────

    def run_phase_5(self):
        print(f"\n>>> Phase 5: Reporting")
        prompt = self.core.expand_prompt("orchestrator_phase5.md", {
            "VERDICT_PATH": self.core.paths["cycle_dir"] / "verdict.md",
            "IDEA_QUEUE_PATH": self.core.paths["idea_queue"]
        })
        self.core.invoke_ai(self.models["orchestrator"], prompt, role="orchestrator_phase5")
        report_path = self.core.paths["cycle_dir"] / "cycle_report.md"
        if report_path.exists():
            print(f"  Cycle report: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="AIRDP v3.0 Orchestrator")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--cycle-id", default="auto",
                        help="Cycle ID: '01' etc., 'auto'=use latest existing, 'new'=create next")
    parser.add_argument("--start", type=int, default=2, choices=[2, 3, 4, 5],
                        help="Phase to start from")
    parser.add_argument("--end", type=int, default=5, choices=[2, 3, 4, 5],
                        help="Phase to end at")
    parser.add_argument("--orchestrator", default="gemini",
                        help="AI for orchestration (gemini, claude, copilot, codex)")
    parser.add_argument("--researcher", default="gemini",
                        help="AI for execution (gemini, claude, copilot, codex)")
    parser.add_argument("--reviewer", default="claude",
                        help="AI for validation (gemini, claude, copilot, codex)")
    parser.add_argument("--judge", default="claude",
                        help="AI for judging (gemini, claude, copilot, codex)")
    parser.add_argument("--skip-approval", action="store_true",
                        help="Skip human approval gates (for CI/automation)")

    args = parser.parse_args()

    models = {
        "orchestrator": args.orchestrator,
        "researcher": args.researcher,
        "reviewer": args.reviewer,
        "judge": args.judge
    }

    orchestrator = AirdpOrchestrator(
        project_dir=args.project_dir,
        cycle_id=args.cycle_id,
        models=models,
        start_phase=args.start,
        end_phase=args.end,
        skip_approval=args.skip_approval
    )
    orchestrator.run_pipeline()


if __name__ == "__main__":
    main()
