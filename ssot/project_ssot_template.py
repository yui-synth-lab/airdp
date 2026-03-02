"""
project_ssot_template.py — AIRDP プロジェクト SSoT ローダー テンプレート

このファイルはプロジェクト固有の SSoT ローダーのテンプレートです。
新しいプロジェクトでは、このファイルをコピーして以下を実装してください:

1. ファイル名を変更（例: my_project_ssot.py）
2. クラス名はそのまま SSOT を使用
3. _DATA_DIR をプロジェクトのデータディレクトリに合わせて設定
4. load_data() メソッドをプロジェクト固有のデータ読み込みに合わせて実装
5. 必要に応じてプロジェクト固有のアクセサメソッドを追加

使い方（Researcher のコード冒頭に記述）:

    import sys
    sys.path.insert(0, r"<SSOT_DIR>")
    from <your_project_ssot> import SSOT

    ssot = SSOT()
    consts = ssot.constants()
    data = ssot.load_data()

このファイル自身が ssot/ にあるため、SSOT_DIR は自動解決される。
パスをコードに書く必要はない。
"""

import json
from abc import abstractmethod
from pathlib import Path
from typing import Any

# このファイルが置かれている場所 = ssot/
_SSOT_DIR = Path(__file__).parent

# プロジェクトのデータディレクトリ（プロジェクトに合わせて変更すること）
# 例: ssot/ の隣の data/ にある場合
_DATA_DIR = _SSOT_DIR.parent / "data"


class SSOTBase:
    """
    AIRDP SSoT ローダーの基底クラス。

    全プロジェクト共通のインターフェースを定義する。
    プロジェクト固有のローダーはこのクラスを継承し、
    load_data() を実装すること。
    """

    def constants(self) -> dict:
        """ssot/constants.json を読み込んで返す。"""
        with open(_SSOT_DIR / "constants.json", encoding="utf-8") as f:
            return json.load(f)

    def parameters(self) -> dict:
        """ssot/parameters.json を読み込んで返す。"""
        with open(_SSOT_DIR / "parameters.json", encoding="utf-8") as f:
            return json.load(f)

    def hypothesis(self, hid: str) -> dict:
        """
        ssot/hypotheses/H*.json を読み込んで返す。

        Args:
            hid: 仮説ID（例: "H3"）

        Returns:
            仮説定義の辞書

        Raises:
            FileNotFoundError: 指定された仮説ファイルが存在しない場合
        """
        path = _SSOT_DIR / "hypotheses" / f"{hid}.json"
        if not path.exists():
            raise FileNotFoundError(f"Hypothesis file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def analysis_params(self) -> dict:
        """constants.json の analysis_parameters セクションを返す。"""
        return self.constants().get("analysis_parameters", {})

    def statistical_thresholds(self) -> dict:
        """constants.json の statistical_thresholds セクションを返す。"""
        return self.constants().get("statistical_thresholds", {})

    @abstractmethod
    def load_data(self) -> Any:
        """
        プロジェクト固有のデータを読み込んで返す。

        このメソッドはプロジェクトごとに実装すること。
        返り値の型はプロジェクトに依存する（DataFrame, dict, tuple 等）。

        例:
            - 単一の DataFrame を返す
            - 複数の DataFrame をタプルで返す
            - dict で構造化データを返す
        """
        raise NotImplementedError(
            "load_data() must be implemented by the project-specific SSOT loader."
        )

    @property
    def ssot_dir(self) -> Path:
        """SSoT ディレクトリの Path オブジェクト（デバッグ用）。"""
        return _SSOT_DIR

    @property
    def data_dir(self) -> Path:
        """データディレクトリの Path オブジェクト（デバッグ用）。"""
        return _DATA_DIR


class SSOT(SSOTBase):
    """
    プロジェクト固有の SSoT ローダー。

    SSOTBase を継承し、load_data() をプロジェクトのデータ形式に合わせて実装する。
    以下はテンプレートの実装例。実際のプロジェクトではこのクラスを書き換えること。
    """

    def load_data(self) -> Any:
        """
        プロジェクトの実データを読み込んで返す。

        ここをプロジェクト固有のデータ読み込みロジックに書き換えること。

        例（CSV を読み込む場合）:

            import pandas as pd
            data_path = self.data_dir / "experiment_data.csv"
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found: {data_path}")
            return pd.read_csv(data_path)

        例（複数データソースを返す場合）:

            import pandas as pd
            main_df = pd.read_csv(self.data_dir / "main_data.csv")
            ref_df = pd.read_csv(self.data_dir / "reference_data.csv")
            return main_df, ref_df

        Returns:
            プロジェクト固有のデータ（型はプロジェクトに依存）

        Raises:
            FileNotFoundError: データファイルが見つからない場合
            NotImplementedError: 未実装の場合
        """
        raise NotImplementedError(
            "load_data() is not yet implemented for this project. "
            "Edit this method in your project's SSOT loader to load real data."
        )

    # ──────────────────────────────────────────
    # プロジェクト固有のアクセサメソッド（必要に応じて追加）
    # ──────────────────────────────────────────

    # 例: 特定のデータセクションへのショートカット
    #
    # def experiment_config(self) -> dict:
    #     """constants.json の experiment_config セクションを返す。"""
    #     return self.constants().get("experiment_config", {})
    #
    # def model_parameters(self) -> dict:
    #     """constants.json の model_parameters セクションを返す。"""
    #     return self.constants().get("model_parameters", {})
