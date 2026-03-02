import os
import sys
import uuid
import json
import tempfile
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
        return {
            "project_dir": self.project_dir,
            "cycle_dir": cycle_dir,
            "ssot_dir": ssot_dir,
            "roadmap": cycle_dir / "roadmap.md",
            "log": cycle_dir / "output_log.md",
            "iterations": cycle_dir / "iterations",
            "session_dir": cycle_dir / ".sessions",
            "constants": ssot_dir / "constants.json",
            "prompts": self.project_dir / "airdp_prompts_v3",
            "idea_queue": self.project_dir / "idea_queue.md"
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

        vars = {
            "PROJECT_NAME": self.constants.get("project_info", {}).get("name", "AIRDP Project"),
            "DOMAIN": self.constants.get("project_info", {}).get("domain", "General"),
            "GOAL": self.constants.get("project_info", {}).get("goal", ""),
            **self.constants.get("lexicon", {}),
            **self.paths,
            **(extra_vars or {})
        }

        for k, v in vars.items():
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

        # プロンプトをプロジェクト内の一時ディレクトリに書き出す
        tmp_dir = self.project_dir / ".airdp_tmp"
        tmp_dir.mkdir(exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", encoding="utf-8",
            delete=False, prefix="airdp_prompt_", dir=tmp_dir
        )
        tmp_path = None
        try:
            tmp.write(prompt)
            tmp.close()
            tmp_path = tmp.name

            cmd = self._build_cmd(ai_name, tmp_path, role)
            if cmd is None:
                print(f"  [SKIP] AI backend {ai_name} not implemented.")
                return ""

            # Claude Code のネスト実行を防ぐため環境変数を除外
            run_env = os.environ.copy()
            if ai_name == "claude":
                for key in ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_VERSION"]:
                    run_env.pop(key, None)

            stdout_lines = []

            # Codex はプロンプトを stdin 経由で受け取る
            stdin_data = prompt if ai_name == "codex" else None

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if stdin_data else None,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8",
                shell=(sys.platform == "win32"),
                env=run_env
            )

            if stdin_data:
                proc.stdin.write(stdin_data)
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
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def _build_cmd(self, ai_name, tmp_path, role):
        """AIバックエンドとセッション状態に応じてコマンドを組み立てる。"""
        session_id = self.load_session_id(role) if role else None

        if ai_name == "gemini":
            if session_id:
                print(f"  [Session] Gemini resume: {session_id}")
                return ["gemini", "-r", session_id, "-p", f"@{tmp_path}", "-y"]
            else:
                return ["gemini", "-p", f"@{tmp_path}", "-y"]

        elif ai_name == "claude":
            claude_base = ["claude", "-p", f"@{tmp_path}",
                           "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
                           "--permission-mode", "bypassPermissions"]
            if session_id:
                print(f"  [Session] Claude resume: {session_id}")
                return ["claude", "--resume", session_id, "-p", f"@{tmp_path}",
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
                return ["copilot", "--resume", session_id, "-p", f"@{tmp_path}", "--yolo"]
            elif role:
                # 新規セッション: UUIDを事前生成して --resume で指定
                new_sid = str(uuid.uuid4())
                self._copilot_preset_session_id = new_sid
                return ["copilot", "--resume", new_sid, "-p", f"@{tmp_path}", "--yolo"]
            else:
                return ["copilot", "-p", f"@{tmp_path}", "--yolo"]

        elif ai_name == "codex":
            # Codex はプロンプトを stdin から受け取る（@file 記法非対応）
            # invoke_ai 側で stdin=prompt を渡す必要があるためフラグのみ返す
            base_flags = ["--dangerously-bypass-approvals-and-sandbox", "--json", "-"]
            if session_id:
                print(f"  [Session] Codex resume: {session_id}")
                return ["codex", "exec", "resume", session_id] + base_flags
            else:
                return ["codex", "exec"] + base_flags

        return None


# Singleton-like access
def get_core(project_dir=".", cycle_id="01"):
    return AirdpCore(project_dir, cycle_id)
