"""スプシ連携モジュール — 記事管理DBの読み書き"""
from __future__ import annotations

import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# スプシの設定
SPREADSHEET_ID = "1X-jGv8TFHQ88UBHe8zXnRPKMDxus2EIHilEXAPmehIQ"
TASK_TAB = "_タスク管理"  # タスク管理用タブ（新規作成）
CREDS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")

def get_client():
    """認証済みgspreadクライアントを返す（ローカル: credentials.json / Cloud: secrets）"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    # Streamlit Cloudではsecretsから読む
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception:
        pass
    # ローカルではファイルから読む
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
    return gspread.authorize(creds)


def get_spreadsheet():
    """スプシを開く"""
    gc = get_client()
    return gc.open_by_key(SPREADSHEET_ID)


# ==================
# 記事データの読み込み
# ==================
def get_all_articles() -> list[dict]:
    """全タブから記事データを読み込む"""
    sh = get_spreadsheet()
    all_articles = []

    # 記事タブ（_で始まらないタブが記事データ）
    for ws in sh.worksheets():
        if ws.title.startswith("_") or ws.title.strip() == "シート1":
            continue
        rows = ws.get_all_records()
        for row in rows:
            row["サイト"] = ws.title
        all_articles.extend(rows)

    return all_articles


def get_site_articles(site_name: str) -> list[dict]:
    """指定サイトの記事データを読み込む"""
    sh = get_spreadsheet()
    ws = sh.worksheet(site_name)
    return ws.get_all_records()


# ==================
# タスク管理
# ==================
def _get_or_create_task_tab():
    """タスク管理タブを取得（なければ作成）"""
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(TASK_TAB)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=TASK_TAB, rows=500, cols=12)
        ws.update(values=[
            ["ID", "サイト", "記事タイトル", "URL", "タスク種別", "タスク内容",
             "担当者", "ステータス", "期限", "作成者", "作成日", "完了日"]
        ], range_name="A1:L1")
    return ws


def get_all_tasks() -> list[dict]:
    """全タスクを取得"""
    ws = _get_or_create_task_tab()
    return ws.get_all_records()


def get_tasks_for_user(user_name: str) -> list[dict]:
    """指定ユーザーのタスクを取得"""
    tasks = get_all_tasks()
    return [t for t in tasks if t.get("担当者") == user_name and t.get("ステータス") != "完了"]


def add_task(site: str, title: str, url: str, task_type: str,
             description: str, assignee: str, due_date: str, created_by: str) -> dict:
    """タスクを追加"""
    ws = _get_or_create_task_tab()
    all_rows = ws.get_all_values()
    next_id = len(all_rows)  # ヘッダー含むので+1不要

    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    new_row = [
        next_id, site, title, url, task_type, description,
        assignee, "未対応", due_date, created_by, now, ""
    ]
    ws.append_row(new_row)

    return {
        "ID": next_id,
        "サイト": site,
        "記事タイトル": title,
        "担当者": assignee,
        "タスク内容": description,
        "ステータス": "未対応",
    }


def complete_task(task_id: int, user_name: str) -> dict | None:
    """タスクを完了にする"""
    ws = _get_or_create_task_tab()
    all_rows = ws.get_all_values()

    for i, row in enumerate(all_rows):
        if i == 0:
            continue  # ヘッダースキップ
        if str(row[0]) == str(task_id):
            now = datetime.now().strftime("%Y/%m/%d %H:%M")
            ws.update_cell(i + 1, 8, "完了")  # H列=ステータス
            ws.update_cell(i + 1, 12, now)    # L列=完了日
            return {
                "ID": task_id,
                "記事タイトル": row[2],
                "ステータス": "完了",
                "完了日": now,
            }
    return None


def update_assignee(site: str, article_title: str, new_assignee: str) -> bool:
    """記事の担当者を変更（タスク管理タブ内）"""
    ws = _get_or_create_task_tab()
    all_rows = ws.get_all_values()

    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if row[1] == site and row[2] == article_title:
            ws.update_cell(i + 1, 7, new_assignee)  # G列=担当者
            return True
    return False


# ==================
# インターンタスク
# ==================
INTERN_TAB = "_インターンタスク"

def _get_or_create_intern_tab():
    """インターンタスクタブを取得（なければ作成）"""
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(INTERN_TAB)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=INTERN_TAB, rows=500, cols=10)
        ws.update(values=[
            ["ID", "インターン名", "次回出勤日", "タスク内容", "記事タイトル",
             "URL", "ステータス", "作成者", "作成日", "完了日"]
        ], range_name="A1:J1")
    return ws


def add_intern_task(intern_name: str, task_description: str,
                    article_title: str = "", url: str = "",
                    next_work_date: str = "", created_by: str = "") -> dict:
    """インターンにタスクを振る"""
    ws = _get_or_create_intern_tab()
    all_rows = ws.get_all_values()
    next_id = len(all_rows)

    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    new_row = [
        next_id, intern_name, next_work_date, task_description,
        article_title, url, "未対応", created_by, now, ""
    ]
    ws.append_row(new_row)

    return {
        "ID": next_id,
        "インターン名": intern_name,
        "タスク内容": task_description,
        "ステータス": "未対応",
    }


def get_intern_tasks(intern_name: str) -> list[dict]:
    """指定インターンの未完了タスクを取得"""
    ws = _get_or_create_intern_tab()
    all_tasks = ws.get_all_records()
    return [t for t in all_tasks
            if t.get("インターン名") == intern_name and t.get("ステータス") != "完了"]


# ==================
# GSCデータのスプシ転記
# ==================
def _gsc_tab_name(site_name: str, data_type: str) -> str:
    """GSCタブ名を生成（例: _GSC_ほんべ_ページ）"""
    return f"_GSC_{site_name}_{data_type}"


def save_gsc_pages(df, site_name: str = "ほんべ") -> int:
    """ページ別GSCデータをスプシに保存（上書き）"""
    sh = get_spreadsheet()
    tab_name = _gsc_tab_name(site_name, "ページ")
    try:
        ws = sh.worksheet(tab_name)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=max(len(df) + 1, 100), cols=10)

    headers = df.columns.tolist()
    rows = [headers] + df.astype(str).values.tolist()
    ws.update(values=rows, range_name=f"A1:{chr(64 + len(headers))}{len(rows)}")
    return len(df)


def save_gsc_queries(df, site_name: str = "ほんべ") -> int:
    """クエリ別GSCデータをスプシに保存（上書き）"""
    sh = get_spreadsheet()
    tab_name = _gsc_tab_name(site_name, "クエリ")
    try:
        ws = sh.worksheet(tab_name)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=max(len(df) + 1, 100), cols=10)

    headers = df.columns.tolist()
    rows = [headers] + df.astype(str).values.tolist()
    ws.update(values=rows, range_name=f"A1:{chr(64 + len(headers))}{len(rows)}")
    return len(df)


def get_gsc_pages(site_name: str = "ほんべ"):
    """スプシからページ別GSCデータを読み込み"""
    sh = get_spreadsheet()
    tab_name = _gsc_tab_name(site_name, "ページ")
    try:
        ws = sh.worksheet(tab_name)
        records = ws.get_all_records()
        if records:
            import pandas as pd
            return pd.DataFrame(records)
    except gspread.exceptions.WorksheetNotFound:
        pass
    return None


def get_gsc_queries(site_name: str = "ほんべ"):
    """スプシからクエリ別GSCデータを読み込み"""
    sh = get_spreadsheet()
    tab_name = _gsc_tab_name(site_name, "クエリ")
    try:
        ws = sh.worksheet(tab_name)
        records = ws.get_all_records()
        if records:
            import pandas as pd
            return pd.DataFrame(records)
    except gspread.exceptions.WorksheetNotFound:
        pass
    return None


def complete_intern_task(task_id: int) -> dict | None:
    """インターンタスクを完了にする"""
    ws = _get_or_create_intern_tab()
    all_rows = ws.get_all_values()

    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if str(row[0]) == str(task_id):
            now = datetime.now().strftime("%Y/%m/%d %H:%M")
            ws.update_cell(i + 1, 7, "完了")   # G列=ステータス
            ws.update_cell(i + 1, 10, now)      # J列=完了日
            return {
                "ID": task_id,
                "タスク内容": row[3],
                "ステータス": "完了",
                "完了日": now,
            }
    return None
