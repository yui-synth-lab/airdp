# AIRDP v3.0: Universal Framework Design Document
## AIRDP v3.0: 汎用AI駆動型パイプライン設計書

**Version:** 3.0 (Python / Universal / Multilingual)
**Last Updated:** 2026-03-02

---

## 1. Vision & Background / ビジョンと背景

**English:**
AIRDP (AI-Driven Research & Development Process) was originally developed for scientific discovery (KSAU Project). v3.0 evolves this system into a universal framework applicable to any domain, including software development, business strategy, and creative writing.

**日本語:**
AIRDP は、元々科学的発見（KSAU Project）のために開発されました。v3.0 では、このシステムをソフトウェア開発、ビジネス戦略、クリエイティブライティングなど、あらゆる分野に適用可能な汎用フレームワークへと進化させました。

---

## 2. Universal Lexicon & Multi-Language / 汎用用語集と多言語対応

**English:**
The framework dynamically adapts its terminology (Lexicon) based on the project domain. This ensures that AI agents interact in a natural and professional manner for each specific field.

**日本語:**
フレームワークは、プロジェクトのドメインに基づいて用語（Lexicon）を動的に適応させます。これにより、AIエージェントが各専門分野において自然かつプロフェッショナルな対話を行うことを保証します。

| Term / 用語 | Scientific (en) | Software (jp) | General (en/jp) |
| :--- | :--- | :--- | :--- |
| **Objective** | Hypothesis | 機能/タスク | Unit Objective / 目標 |
| **Executor** | Researcher | リード開発者 | Executor / 実行者 |
| **Validator** | Reviewer | QAエンジニア | Validator / 検証者 |
| **Criteria** | p-value/FPR | テスト/仕様 | Success Metrics / 成功指標 |
| **SSoT** | Constants | 技術仕様書 | Source of Truth / プロジェクト制約 |

---

## 3. Core Architecture / コアアーキテクチャ

**English:**
The pipeline is now fully implemented in Python, replacing the old PowerShell-based orchestration.

1.  **`airdp_init.py`**: Interactive setup for domain, language, and goals.
2.  **`airdp_core.py`**: Common utilities for path resolution, multilingual prompt expansion, and AI CLI invocation.
3.  **`airdp_orchestrator.py`**: The central hub managing the 5-phase lifecycle and iterative loops.
4.  **`airdp_paper.py`**: A specialized pipeline for collaborative document writing.

**日本語:**
パイプラインは完全に Python で実装され、以前の PowerShell ベースの制御からリプレイスされました。

1.  **`airdp_init.py`**: ドメイン、言語、目標のインタラクティブ・セットアップ。
2.  **`airdp_core.py`**: パス解決、多言語プロンプト展開、AI CLI 呼び出しの共通ユーティリティ。
3.  **`airdp_orchestrator.py`**: 5フェーズのライフサイクルとイテレーションループを管理するハブ。
4.  **`airdp_paper.py`**: 協調的なドキュメント執筆に特化したパイプライン。

---

## 4. Phase-Gate Control / フェーズゲート制御

**English:**
AIRDP rigorously restricts human intervention during the "Execute" phase to eliminate bias.

- **Phase 1 (Seed)**: Human intervention allowed (Objective setting).
- **Phase 2 (Plan)**: Human approval required for the roadmap.
- **Phase 3 (Execute)**: **Human intervention strictly prohibited** (AI autonomous iteration).
- **Phase 4 (Judge)**: Final verdict by an independent Judge AI.
- **Phase 5 (Report)**: Results delivery and next-cycle proposal.

**日本語:**
AIRDP は、バイアスを排除するために「実行」フェーズ中の人間による介入を厳格に制限します。

- **Phase 1 (Seed)**: 人間の介入可能（目標設定）。
- **Phase 2 (Plan)**: ロードマップに対する人間の承認が必要。
- **Phase 3 (Execute)**: **人間の介入は厳禁**（AIによる自律イテレーション）。
- **Phase 4 (Judge)**: 独立した判定AIによる最終評価。
- **Phase 5 (Report)**: 成果物の提供と次サイクルの提案。

---

## 5. Implementation Policy / 実装ポリシー

**English:**
- **Python-Native**: Cross-platform portability (Win/macOS/Linux).
- **No Hardcoding**: All project constraints must be managed in SSoT (ssot/constants.json).
- **Traceability**: All AI communications and intermediate results are logged.

**日本語:**
- **Pythonネイティブ**: クロスプラットフォーム対応 (Win/macOS/Linux)。
- **ハードコード禁止**: すべてのプロジェクト制約は SSoT (ssot/constants.json) で管理。
- **追跡可能性**: AI間のすべての通信と中間結果をログに記録。

---

*AIRDP Framework Design v3.0 — 2026-03-02*
*"The best framework is one that knows when to stop."*
