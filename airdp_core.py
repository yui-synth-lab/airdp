import os
import sys
import uuid
import json
import subprocess
from pathlib import Path
from datetime import datetime


class AirdpCore:
    def __init__(self, project_dir=".", cycle_id="01"):
        self.project_dir = Path(project_dir).resolve()
        self.cycle_id = cycle_id
        self.paths = self._resolve_paths()
        self.constants = self._load_constants()

    def _resolve_paths(self):
        cycle_dir = self.project_dir / "cycles" / f"cycle_{self.cycle_id}"
        ssot_dir = self.project_dir / "ssot"
        # プロンプトテンプレートは airdp_core.py と同じディレクトリ配下を優先し、
        # 存在しなければ project_dir 配下にフォールバックする
        framework_dir = Path(__file__).parent
        prompts_dir = framework_dir / "airdp_prompts_v3"
        if not prompts_dir.exists():
            prompts_dir = self.project_dir / "airdp_prompts_v3"
        return {
            "project_dir": self.project_dir,
            "cycle_dir": cycle_dir,
            "ssot_dir": ssot_dir,
            "roadmap": cycle_dir / "roadmap.md",
            "log": cycle_dir / "output_log.md",
            "iterations": cycle_dir / "iterations",
            "session_dir": cycle_dir / ".sessions",
            "constants": ssot_dir / "constants.json",
            "prompts": prompts_dir,
            "idea_queue": self.project_dir / "idea_queue.md",
            "src": self.project_dir / "src"
        }

    def _load_constants(self):
        if self.paths["constants"].exists():
            with open(self.paths["constants"], "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def expand_prompt(self, template_name, extra_vars=None):
        lang = self.constants.get("project_info", {}).get("language", "en")
        template_path = self.paths["prompts"] / lang / template_name

        if not template_path.exists():
            template_path = self.paths["prompts"] / "en" / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_name} in {lang} or en")

        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        dqr = self.constants.get("domain_quality_rules", {})

        info = self.constants.get("project_info", {})
        template_vars = {
            "PROJECT_NAME": info.get("name", "AIRDP Project"),
            "DOMAIN": info.get("domain", "General"),
            "GOAL": info.get("goal", "") or info.get("description", ""),
            **self.constants.get("lexicon", {}),
            **{k: v.as_posix() if isinstance(v, Path) else v for k, v in self.paths.items()},
            "DOMAIN_PROHIBITIONS": "\n".join(
                f"- {p}" for p in dqr.get("researcher_prohibitions", [])
            ) or "（ドメイン固有の禁止事項は未設定）",
            "DOMAIN_CHECKLIST": "\n".join(
                f"□ {c}" for c in dqr.get("reviewer_checklist", [])
            ) or "（ドメイン固有のチェックリストは未設定）",
            "JUDGE_ACCEPT_CRITERIA": "\n".join(
                f"- {c}" for c in dqr.get("judge_accept_criteria", [])
            ) or "（ドメイン固有の ACCEPT 条件は未設定）",
            "FAILURE_PATTERNS": "\n".join(
                f"- {p}" for p in dqr.get("common_failure_patterns", [])
            ) or "（ドメイン固有の失敗パターンは未設定）",
        }
        for k, v in (extra_vars or {}).items():
            template_vars[k] = v.as_posix() if isinstance(v, Path) else v

        for k, v in template_vars.items():
            content = content.replace(f"{{{{{k}}}}}", str(v))

        return content

    # ── セッション管理 ──────────────────────────────

    def _session_file(self, role):
        """ロール別セッションIDファイルのパスを返す。"""
        self.paths["session_dir"].mkdir(parents=True, exist_ok=True)
        return self.paths["session_dir"] / f"{role}_session_id.txt"

    def load_session_id(self, role):
        """保存済みセッションIDを読み込む。なければ None。"""
        path = self._session_file(role)
        if path.exists():
            sid = path.read_text(encoding="utf-8").strip()
            return sid if sid else None
        return None

    def save_session_id(self, role, session_id):
        """セッションIDを保存する。"""
        self._session_file(role).write_text(session_id, encoding="utf-8")

    def clear_session_id(self, role):
        """セッションIDを削除する（新サイクル開始時など）。"""
        path = self._session_file(role)
        if path.exists():
            path.unlink()

    def _get_gemini_session_ids(self):
        """現在存在する Gemini セッション ID 一覧を返す。"""
        import re
        try:
            result = subprocess.run(
                ["gemini", "--list-sessions"],
                capture_output=True, text=True, encoding="utf-8",
                shell=(sys.platform == "win32")
            )
            # 各行末の [UUID] を抽出: e.g. "1. Title (1 hour ago) [uuid-here]"
            return set(re.findall(r'\[([0-9a-f-]{36})\]', result.stdout))
        except Exception:
            return set()

    # ── AI 呼び出し ────────────────────────────────

    def invoke_ai(self, ai_name, prompt, role=None):
        """AI呼び出し。role を指定するとセッションを引き継ぐ。"""
        print(f"  [AI: {ai_name}] Invoking...")

        # Gemini セッション差分検出用: 呼び出し前のスナップショット
        if ai_name == "gemini" and role and self.load_session_id(role) is None:
            self._before_gemini_sessions = self._get_gemini_session_ids()
        else:
            self._before_gemini_sessions = set()

        try:
            cmd = self._build_cmd(ai_name, prompt, role)
            if cmd is None:
                print(f"  [SKIP] AI backend {ai_name} not implemented.")
                return ""

            # Claude Code のネスト実行を防ぐため環境変数を除外
            run_env = os.environ.copy()
            if ai_name == "claude":
                for key in ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_VERSION"]:
                    run_env.pop(key, None)

            stdout_lines = []

            # Gemini はプロンプトを stdin 経由で渡す（長プロンプト・特殊文字対策）
            # Gemini は npm .cmd なので Windows では shell=True が必要
            # Claude は -p 引数で渡すが shell=False で CreateProcess に直接渡す（長プロンプトの壊れ防止）
            use_stdin = (ai_name == "gemini")
            use_shell = (sys.platform == "win32") and (ai_name != "claude")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if use_stdin else subprocess.DEVNULL,
                text=True, encoding="utf-8",
                shell=use_shell,
                env=run_env
            )

            if use_stdin:
                proc.stdin.write(prompt)
                proc.stdin.close()

            # stdout をリアルタイムで表示しながら収集
            for line in proc.stdout:
                print(line, end="", flush=True)
                stdout_lines.append(line)

            # stderr も収集（エラー表示用）
            stderr_text = proc.stderr.read()

            proc.wait()
            stdout_text = "".join(stdout_lines)

            # Gemini: 新規セッションIDを取得して保存
            if ai_name == "gemini" and role:
                sid = self.load_session_id(role)
                if sid is None:
                    after = self._get_gemini_session_ids()
                    new_ids = after - self._before_gemini_sessions
                    if new_ids:
                        new_sid = sorted(new_ids)[-1]
                        self.save_session_id(role, new_sid)
                        print(f"  [Session] Gemini session saved: {new_sid}")

            # Codex: JSONL から thread.started イベントの thread_id を抽出して保存
            elif ai_name == "codex" and role and self.load_session_id(role) is None:
                for line in stdout_lines:
                    try:
                        obj = json.loads(line)
                        if obj.get("type") == "thread.started" and obj.get("thread_id"):
                            self.save_session_id(role, obj["thread_id"])
                            print(f"  [Session] Codex session saved: {obj['thread_id']}")
                            break
                    except (json.JSONDecodeError, AttributeError):
                        continue

            # Copilot: 事前生成したUUIDをそのまま保存（Claudeと同方式）
            elif ai_name == "copilot" and role and self.load_session_id(role) is None:
                preset_sid = getattr(self, "_copilot_preset_session_id", None)
                if preset_sid:
                    self.save_session_id(role, preset_sid)
                    print(f"  [Session] Copilot session saved: {preset_sid}")
                    self._copilot_preset_session_id = None

            # Claude: --session-id で事前指定したUUIDをそのまま保存
            elif ai_name == "claude" and role and self.load_session_id(role) is None:
                preset_sid = getattr(self, "_claude_preset_session_id", None)
                if preset_sid:
                    self.save_session_id(role, preset_sid)
                    print(f"  [Session] Claude session saved: {preset_sid}")
                    self._claude_preset_session_id = None

            # ログへの記録
            log_path = self.paths["log"]
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n## AI Interaction: {ai_name} / role={role} ({datetime.now().isoformat()})\n")
                f.write(f"### Output:\n\n{stdout_text}\n")
                if stderr_text:
                    f.write(f"### Errors:\n\n{stderr_text}\n")
                f.write("\n---\n")

            if proc.returncode != 0:
                print(f"  [ERROR] AI call failed (returncode={proc.returncode}): {stderr_text[:200]}")
                return ""

            return stdout_text

        except Exception as e:
            print(f"  [EXCEPTION] Failed to invoke {ai_name}: {e}")
            return ""

    def _build_cmd(self, ai_name, prompt, role):
        """AIバックエンドとセッション状態に応じてコマンドを組み立てる。
        Gemini はプロンプトを stdin 経由で渡す（Windows の shell=True でも特殊文字が壊れないため）。
        Claude/Copilot/Codex は -p 引数で渡す。"""
        session_id = self.load_session_id(role) if role else None

        if ai_name == "gemini":
            base_cmd = ["gemini", "--approval-mode", "yolo"]
            if session_id:
                print(f"  [Session] Gemini resume: {session_id}")
                return base_cmd + ["-r", session_id]
            else:
                return base_cmd

        elif ai_name == "claude":
            claude_base = ["claude", "-p", prompt,
                           "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
                           "--permission-mode", "bypassPermissions"]
            if session_id:
                print(f"  [Session] Claude resume: {session_id}")
                return ["claude", "--resume", session_id, "-p", prompt,
                        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
                        "--permission-mode", "bypassPermissions"]
            elif role:
                # 新規セッション: UUIDを事前生成して --session-id で指定
                new_sid = str(uuid.uuid4())
                self._claude_preset_session_id = new_sid
                return claude_base + ["--session-id", new_sid]
            else:
                return claude_base

        elif ai_name == "copilot":
            if session_id:
                print(f"  [Session] Copilot resume: {session_id}")
                return ["copilot", "--resume", session_id, "-p", prompt, "--yolo"]
            elif role:
                # 新規セッション: UUIDを事前生成して --resume で指定
                new_sid = str(uuid.uuid4())
                self._copilot_preset_session_id = new_sid
                return ["copilot", "--resume", new_sid, "-p", prompt, "--yolo"]
            else:
                return ["copilot", "-p", prompt, "--yolo"]

        elif ai_name == "codex":
            # Codex: PS版同様にプロンプトを positional argument で渡す
            base_flags = ["--dangerously-bypass-approvals-and-sandbox", "--json"]
            if session_id:
                print(f"  [Session] Codex resume: {session_id}")
                return ["codex", "exec", "resume", session_id] + base_flags + [prompt]
            else:
                return ["codex", "exec"] + base_flags + [prompt]

        return None


def invoke_ai_simple(ai_name, prompt):
    """セッション管理・ログなしの最小 AI 呼び出し。airdp_init.py などプロジェクト初期化前に使用する。
    stdout テキストをそのまま返す。失敗時は空文字列。"""
    print(f"  [AI: {ai_name}] Invoking...")
    try:
        run_env = os.environ.copy()
        if ai_name == "gemini":
            # Gemini はプロンプトを stdin 経由で渡す
            cmd = [ai_name, "--approval-mode", "yolo"]
            use_stdin = True
        elif ai_name == "claude":
            for key in ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_VERSION"]:
                run_env.pop(key, None)
            cmd = [ai_name, "-p", prompt,
                   "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
                   "--permission-mode", "bypassPermissions"]
            use_stdin = False
        else:
            cmd = [ai_name, "-p", prompt]
            use_stdin = False

        use_shell = (sys.platform == "win32") and (ai_name != "claude")
        stdout_lines = []
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE if use_stdin else subprocess.DEVNULL,
            text=True, encoding="utf-8",
            shell=use_shell,
            env=run_env
        )
        if use_stdin:
            proc.stdin.write(prompt)
            proc.stdin.close()
        for line in proc.stdout:
            print(line, end="", flush=True)
            stdout_lines.append(line)
        stderr_text = proc.stderr.read()
        proc.wait()

        if proc.returncode != 0:
            print(f"  [ERROR] AI call failed (returncode={proc.returncode}): {stderr_text[:200]}")
            return ""
        return "".join(stdout_lines)
    except Exception as e:
        print(f"  [EXCEPTION] Failed to invoke {ai_name}: {e}")
        return ""


# Singleton-like access
def get_core(project_dir=".", cycle_id="01"):
    return AirdpCore(project_dir, cycle_id)
