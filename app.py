"""記事管理DB — スプシ連携版"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import json
from lib.spreadsheet import get_all_articles, get_all_tasks

# ページ設定
st.set_page_config(page_title="記事管理DB", page_icon="📊", layout="wide")

# =====================
# GSC CSVアップロード（サイドバー）
# =====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GSC_PAGES_PATH = os.path.join(DATA_DIR, "gsc_pages.csv")
GSC_QUERIES_PATH = os.path.join(DATA_DIR, "gsc_queries.csv")

with st.sidebar:
    st.markdown("### 📂 データ管理")

    st.markdown("**GSCデータ**")
    st.caption("GSC → 検索パフォーマンス → エクスポート（ページ別・クエリ別どちらもOK）")
    gsc_file = st.file_uploader("CSVアップロード", type=["csv"], key="gsc_csv")
    if gsc_file:
        gsc_df = pd.read_csv(gsc_file)
        cols = gsc_df.columns.tolist()
        # ページ別かクエリ別か自動判定（1列目がURLっぽいかどうか）
        first_col_vals = gsc_df.iloc[:, 0].astype(str)
        is_pages = first_col_vals.str.startswith("http").any()
        if is_pages:
            gsc_df.to_csv(GSC_PAGES_PATH, index=False)
            st.success(f"✅ ページ別 {len(gsc_df)}行 保存済み")
        else:
            gsc_df.to_csv(GSC_QUERIES_PATH, index=False)
            st.success(f"✅ クエリ別 {len(gsc_df)}行 保存済み")

    st.markdown("---")

    # 保存済みデータの状況
    st.markdown("**📊 保存済みデータ**")
    if os.path.exists(GSC_PAGES_PATH):
        saved_pages = pd.read_csv(GSC_PAGES_PATH)
        st.caption(f"ページ別: {len(saved_pages)}行")
    else:
        st.caption("ページ別: なし")
    if os.path.exists(GSC_QUERIES_PATH):
        saved_queries = pd.read_csv(GSC_QUERIES_PATH)
        st.caption(f"クエリ別: {len(saved_queries)}行")
    else:
        st.caption("クエリ別: なし")

    st.markdown("---")
    use_real_data = st.checkbox("📡 実データを使う", value=os.path.exists(GSC_PAGES_PATH))
    st.caption("OFFにするとダミーデータ表示")

# === カスタムCSS ===
st.markdown("""
<style>
/* KPIカード */
.kpi-card {
    background: #f8f9fb;
    border: 1px solid #e0e4ea;
    border-radius: 8px;
    padding: 16px 20px;
    min-height: 90px;
}
.kpi-card .label { font-size: 11px; color: #607d8b; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
.kpi-card .value { font-size: 28px; font-weight: 700; color: #263238; margin: 4px 0; }
.kpi-card .sub { font-size: 12px; color: #90a4ae; }

/* アラートカード */
.alert-card {
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 8px;
    border-left: 4px solid #ccc;
}
.alert-card.danger { background: #fce4ec; border-left-color: #c62828; }
.alert-card.warning { background: #fff8e1; border-left-color: #f9a825; }
.alert-card.ok { background: #e8f5e9; border-left-color: #2e7d32; }
.alert-card.info { background: #e3f2fd; border-left-color: #1565c0; }
.alert-card .a-title { font-size: 14px; font-weight: 600; color: #263238; }
.alert-card .a-sub { font-size: 12px; color: #607d8b; margin-top: 4px; }

/* ジャンルカード */
.genre-card {
    background: #f8f9fb;
    border: 1px solid #e0e4ea;
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid #1565c0;
    margin-bottom: 8px;
}
.genre-card.good { border-left-color: #2e7d32; }
.genre-card.ok { border-left-color: #e65100; }
.genre-card.bad { border-left-color: #c62828; }
.genre-card .g-title { font-size: 15px; font-weight: 700; color: #263238; }
.genre-card .g-stats { font-size: 12px; color: #607d8b; margin-top: 6px; }
.genre-card .g-rate { font-size: 24px; font-weight: 700; margin-top: 4px; }
.genre-card .g-rate.good { color: #2e7d32; }
.genre-card .g-rate.ok { color: #e65100; }
.genre-card .g-rate.bad { color: #c62828; }

/* メンバーカード */
.member-card {
    background: #f8f9fb;
    border: 1px solid #e0e4ea;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
    border-left: 4px solid #ccc;
}
.member-card.good { border-left-color: #2e7d32; }
.member-card.ok { border-left-color: #e65100; }
.member-card.bad { border-left-color: #c62828; }
.member-card .m-name { font-size: 13px; font-weight: 600; color: #37474f; }
.member-card .m-count { font-size: 22px; font-weight: 700; color: #263238; margin: 4px 0; }
.member-card .m-sub { font-size: 11px; color: #90a4ae; }

/* セクションタイトル */
.sec-title {
    font-size: 14px;
    font-weight: 700;
    color: #37474f;
    margin: 20px 0 8px 0;
    padding: 6px 12px;
    background: #eceff1;
    border-radius: 4px;
    border-left: 3px solid #546e7a;
}

/* テーブルヘッダー */
div[data-testid="stDataFrame"] th {
    background-color: #eceff1 !important;
    color: #37474f !important;
    font-weight: 600 !important;
}

button[data-baseweb="tab"] {
    font-size: 14px !important;
    font-weight: 600 !important;
}

/* 効果カード */
.effect-card {
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 8px;
    border-left: 4px solid #ccc;
    background: #f8f9fb;
}
.effect-card.up { border-left-color: #2e7d32; background: #e8f5e9; }
.effect-card.down { border-left-color: #c62828; background: #fce4ec; }
.effect-card.flat { border-left-color: #9e9e9e; background: #f5f5f5; }
</style>
""", unsafe_allow_html=True)


# =====================
# GSC実データ読み込み
# =====================
def load_gsc_real_data():
    """GSC CSVからほんべ記事の実データを読み込み、記事管理DBフォーマットに変換"""
    from data.real_articles import REAL_ARTICLES

    if not os.path.exists(GSC_PAGES_PATH):
        return None, None

    # ページ別データ読み込み
    gsc_pages = pd.read_csv(GSC_PAGES_PATH)
    # ヘッダー名を統一（GSCエクスポートは「上位のページ」「掲載順位」等）
    col_map_pages = {gsc_pages.columns[0]: "URL", gsc_pages.columns[1]: "クリック数", gsc_pages.columns[2]: "表示回数", gsc_pages.columns[3]: "CTR", gsc_pages.columns[4]: "順位"}
    gsc_pages = gsc_pages.rename(columns=col_map_pages)
    gsc_pages["CTR"] = gsc_pages["CTR"].astype(str).str.replace("%", "").astype(float)

    # クエリ別データ（あれば）
    gsc_queries = None
    if os.path.exists(GSC_QUERIES_PATH):
        gsc_queries = pd.read_csv(GSC_QUERIES_PATH)
        col_map_q = {gsc_queries.columns[0]: "クエリ", gsc_queries.columns[1]: "クリック数", gsc_queries.columns[2]: "表示回数", gsc_queries.columns[3]: "CTR", gsc_queries.columns[4]: "順位"}
        gsc_queries = gsc_queries.rename(columns=col_map_q)
        gsc_queries["CTR"] = gsc_queries["CTR"].astype(str).str.replace("%", "").astype(float)

    # スプシ35記事 × GSCデータをURLでマッチング
    articles = []
    assignees = ["札幌A", "札幌B", "東京C", "東京D", "インターンE", "インターンF"]
    random.seed(42)

    for art in REAL_ARTICLES:
        url = art["URL"]
        if not url:
            url = "（未公開）"
        title = art.get("タイトル", "")

        # GSCデータとマッチング（パラメータ違いのURLも合算）
        if url != "（未公開）":
            base_url = url.rstrip("/")
            gsc_match = gsc_pages[gsc_pages["URL"].str.startswith(base_url)]
            if not gsc_match.empty:
                # 複数行あれば合算
                clicks = int(gsc_match["クリック数"].sum())
                impressions = int(gsc_match["表示回数"].sum())
                ctr = round(clicks / impressions * 100, 1) if impressions > 0 else 0
                # 順位は加重平均
                position = round((gsc_match["順位"] * gsc_match["表示回数"]).sum() / gsc_match["表示回数"].sum(), 1) if impressions > 0 else 99.9
                current_pv = clicks
            else:
                clicks = 0
                impressions = 0
                ctr = 0
                position = 999  # 圏外
                current_pv = 0
        else:
            clicks = 0
            impressions = 0
            ctr = 0
            position = 999
            current_pv = 0

        # 公開日パース（フォーマット: "2025-10-31 18:08:36" or "2025/04/04" or ""）
        pub_str = art.get("公開日", "")
        update_str = art.get("更新日", "")
        try:
            if " " in pub_str:
                pub_date = datetime.strptime(pub_str.split(" ")[0], "%Y-%m-%d")
            elif "/" in pub_str:
                pub_date = datetime.strptime(pub_str, "%Y/%m/%d")
            else:
                pub_date = None
        except:
            pub_date = None

        if pub_date:
            pub_display = pub_date.strftime("%Y/%m/%d")
            deadline = pub_date + timedelta(days=14)
            deadline_str = deadline.strftime("%Y/%m/%d")
        else:
            pub_display = "-"
            deadline_str = "-"

        # 更新日
        try:
            if " " in update_str:
                update_date = datetime.strptime(update_str.split(" ")[0], "%Y-%m-%d")
                update_display = update_date.strftime("%Y/%m/%d")
            elif "/" in update_str:
                update_date = datetime.strptime(update_str, "%Y/%m/%d")
                update_display = update_date.strftime("%Y/%m/%d")
            else:
                update_display = "-"
        except:
            update_display = "-"

        # 先月PVは仮（推移データから計算予定）
        last_month_pv = max(100, int(current_pv * random.uniform(0.8, 1.3))) if current_pv > 0 else 0
        pv_ratio = round(current_pv / last_month_pv * 100) if last_month_pv > 0 else 0

        # 前回順位は仮
        prev_position = round(position + random.uniform(-3, 3), 1)
        prev_position = max(1, prev_position)
        pos_change = round(position - prev_position, 1)

        # ステータス自動判定
        if position >= 100:
            status = "圏外"
        elif pv_ratio < 80 and pv_ratio > 0:
            status = "要改善"
        elif current_pv == 0:
            status = "データなし"
        else:
            status = "正常"

        article_id = f"{art['サイト']}_{art['メインKW']}"
        articles.append({
            "ID": article_id,
            "サイト": art["サイト"],
            "ドメイン": art["ドメイン"],
            "ジャンル": art["ジャンル"],
            "分類": art["分類"],
            "メインKW": art["メインKW"],
            "タイトル": title,
            "URL": url,
            "公開日": pub_display,
            "更新期限": deadline_str,
            "前回更新": update_display,
            "担当": random.choice(assignees) if random.random() > 0.2 else "",
            "先月PV": last_month_pv,
            "現PV": current_pv,
            "PV比": pv_ratio,
            "順位": position,
            "前回順位": prev_position,
            "順位変動": pos_change,
            "Impr": impressions,
            "Click": clicks,
            "CTR": ctr,
            "ステータス": status,
            "競合1位": 0,
            "競合2位": 0,
            "競合3位": 0,
            "競合変動": 0,
            "データソース": "実データ",
        })

    # スプシが正。GSCだけにあるURLは追加しない（パラメータ重複等）

    return pd.DataFrame(articles), gsc_queries


# =====================
# データ生成（ダミー）
# =====================
from data.real_articles import REAL_ARTICLES

@st.cache_data
def generate_data():
    """記事データ + 30日分の推移データ生成"""
    random.seed(42)
    np.random.seed(42)

    assignees = ["札幌A", "札幌B", "東京C", "東京D", "インターンE", "インターンF"]
    articles = []
    history = []  # 推移データ

    # === ほんべ: 実データ ===
    for art in REAL_ARTICLES:
        pub_str = art["公開日"]
        pub_date = None
        if pub_str:
            try:
                if " " in pub_str and "-" in pub_str:
                    pub_date = datetime.strptime(pub_str.split(" ")[0], "%Y-%m-%d")
                elif "/" in pub_str:
                    pub_date = datetime.strptime(pub_str, "%Y/%m/%d")
                elif "-" in pub_str:
                    pub_date = datetime.strptime(pub_str, "%Y-%m-%d")
            except:
                pass
        if not pub_date:
            pub_date = datetime.now() - timedelta(days=random.randint(30, 90))
            pub_str = pub_date.strftime("%Y/%m/%d")

        deadline = pub_date + timedelta(days=14)
        last_update = pub_date + timedelta(days=random.randint(3, 30)) if random.random() > 0.35 else None
        # PV: 前月比で算出
        last_month_pv = random.randint(200, 2500)
        current_pv = int(last_month_pv * random.uniform(0.35, 1.4))
        pv_ratio = round(current_pv / last_month_pv * 100) if last_month_pv > 0 else 0

        # 順位: 100以上は圏外
        position = round(random.uniform(1, 120), 1)
        prev_position = round(position + random.uniform(-10, 10), 1)
        prev_position = max(1, prev_position)
        pos_change = round(position - prev_position, 1)
        impressions = random.randint(100, 5000)
        clicks = random.randint(10, max(11, int(impressions * 0.3)))
        ctr = round(clicks / impressions * 100, 1)

        # 競合データ（ダミー）
        competitor_positions = [round(random.uniform(1, 20), 1) for _ in range(3)]
        competitor_change = round(random.uniform(-5, 5), 1)

        if pv_ratio < 80 or (deadline < datetime.now() and last_update is None):
            status = "未対応"
        elif last_update and (datetime.now() - last_update).days < 7:
            status = "完了"
        elif random.random() > 0.7:
            status = "対応中"
        else:
            status = "監視中"

        article_id = f"{art['サイト']}_{art['メインKW']}"
        articles.append({
            "ID": article_id,
            "サイト": art["サイト"],
            "ドメイン": art["ドメイン"],
            "ジャンル": art["ジャンル"],
            "分類": art["分類"],
            "メインKW": art["メインKW"],
            "URL": art["URL"] if art["URL"] else "（未公開）",
            "公開日": pub_str,
            "更新期限": deadline.strftime("%Y/%m/%d"),
            "前回更新": last_update.strftime("%Y/%m/%d") if last_update else "-",
            "担当": random.choice(assignees) if random.random() > 0.3 else "",
            "先月PV": last_month_pv,
            "現PV": current_pv,
            "PV比": pv_ratio,
            "順位": position,
            "前回順位": prev_position,
            "順位変動": pos_change,
            "Impr": impressions,
            "Click": clicks,
            "CTR": ctr,
            "ステータス": status,
            "競合1位": competitor_positions[0],
            "競合2位": competitor_positions[1],
            "競合3位": competitor_positions[2],
            "競合変動": competitor_change,
        })

        # 30日分の推移データ生成
        base_pv = current_pv
        base_pos = position
        for day_offset in range(30, -1, -1):
            d = datetime.now() - timedelta(days=day_offset)
            # 更新日があれば、その前後でPV・順位を変動させる
            if last_update:
                lu = datetime.strptime(last_update.strftime("%Y/%m/%d"), "%Y/%m/%d")
                days_since_update = (d - lu).days
                if days_since_update > 0:
                    # 更新後は改善傾向
                    pv_adj = base_pv * (1 + random.uniform(0, 0.15) * min(days_since_update / 14, 1))
                    pos_adj = base_pos * (1 - random.uniform(0, 0.1) * min(days_since_update / 14, 1))
                else:
                    # 更新前はやや悪化傾向
                    pv_adj = base_pv * (1 - random.uniform(0, 0.2))
                    pos_adj = base_pos * (1 + random.uniform(0, 0.15))
            else:
                pv_adj = base_pv * random.uniform(0.85, 1.15)
                pos_adj = base_pos * random.uniform(0.9, 1.1)

            history.append({
                "ID": article_id,
                "日付": d.strftime("%Y/%m/%d"),
                "PV": max(0, int(pv_adj + random.randint(-50, 50))),
                "順位": max(1, round(pos_adj + random.uniform(-2, 2), 1)),
            })

    # ダミーデータなし（ほんべのみ）

    return pd.DataFrame(articles), pd.DataFrame(history)


# データ読み込み
@st.cache_data(ttl=300)  # 5分キャッシュ
def load_from_spreadsheet():
    """スプシから記事データを読み込み、ダッシュボード用フォーマットに変換"""
    raw_articles = get_all_articles()
    if not raw_articles:
        return None

    random.seed(42)
    articles = []
    assignees = ["札幌A", "札幌B", "東京C", "東京D", "インターンE", "インターンF"]

    # GSCデータ読み込み（あれば）
    gsc_pages = None
    if os.path.exists(GSC_PAGES_PATH):
        gsc_pages = pd.read_csv(GSC_PAGES_PATH)
        col_map = {gsc_pages.columns[0]: "URL", gsc_pages.columns[1]: "クリック数",
                   gsc_pages.columns[2]: "表示回数", gsc_pages.columns[3]: "CTR", gsc_pages.columns[4]: "順位"}
        gsc_pages = gsc_pages.rename(columns=col_map)
        gsc_pages["CTR"] = gsc_pages["CTR"].astype(str).str.replace("%", "").astype(float)

    for art in raw_articles:
        site = art.get("サイト", "")
        title = art.get("記事タイトル", art.get("タイトル", ""))
        url = art.get("URL", art.get("記事URL", ""))
        if not url:
            url = "（未公開）"

        # GSCとマッチング
        clicks, impressions, ctr, position = 0, 0, 0, 999
        if gsc_pages is not None and url != "（未公開）":
            base_url = url.rstrip("/")
            match = gsc_pages[gsc_pages["URL"].str.startswith(base_url)]
            if not match.empty:
                clicks = int(match["クリック数"].sum())
                impressions = int(match["表示回数"].sum())
                ctr = round(clicks / impressions * 100, 1) if impressions > 0 else 0
                position = round((match["順位"] * match["表示回数"]).sum() / match["表示回数"].sum(), 1) if impressions > 0 else 999

        current_pv = clicks
        # 先月PVは仮（推移データから計算予定）
        last_month_pv = max(100, int(current_pv * random.uniform(0.8, 1.3))) if current_pv > 0 else 0
        pv_ratio = round(current_pv / last_month_pv * 100) if last_month_pv > 0 else 0

        # 順位変動（仮）
        prev_position = round(position + random.uniform(-3, 3), 1)
        prev_position = max(1, prev_position)
        pos_change = round(position - prev_position, 1)

        # 公開日パース
        pub_str = str(art.get("公開日", art.get("published", "")))
        try:
            if "T" in pub_str:
                pub_date = datetime.strptime(pub_str[:10], "%Y-%m-%d")
            elif " " in pub_str and "-" in pub_str:
                pub_date = datetime.strptime(pub_str.split(" ")[0], "%Y-%m-%d")
            elif "/" in pub_str:
                pub_date = datetime.strptime(pub_str, "%Y/%m/%d")
            else:
                pub_date = None
        except:
            pub_date = None

        pub_display = pub_date.strftime("%Y/%m/%d") if pub_date else "-"
        deadline_str = (pub_date + timedelta(days=14)).strftime("%Y/%m/%d") if pub_date else "-"

        # 更新日
        update_str = str(art.get("更新日", art.get("modified", "")))
        try:
            if "T" in update_str:
                update_display = datetime.strptime(update_str[:10], "%Y-%m-%d").strftime("%Y/%m/%d")
            elif " " in update_str and "-" in update_str:
                update_display = datetime.strptime(update_str.split(" ")[0], "%Y-%m-%d").strftime("%Y/%m/%d")
            elif "/" in update_str:
                update_display = update_str
            else:
                update_display = "-"
        except:
            update_display = "-"

        # ステータス自動判定
        if position >= 100:
            status = "圏外"
        elif pv_ratio < 80 and pv_ratio > 0:
            status = "要改善"
        elif current_pv == 0:
            status = "データなし"
        else:
            status = "正常"

        # 分類
        category = art.get("分類", art.get("カテゴリー", art.get("記事区分1", "")))
        # 記事タイプ（M列: CV型/PV型）
        article_type = art.get("記事区分2", "")
        if not article_type:
            # 記事区分1がノウハウならPV型、それ以外はCV型（デフォルト）
            if category == "ノウハウ":
                article_type = "PV型"
            else:
                article_type = "CV型"
        genre = art.get("ジャンル", art.get("カテゴリ", site))
        slug = url.rstrip("/").split("/")[-1] if url != "（未公開）" else ""

        # KW表示（メインKWがあればそれ、なければスラッグ）
        main_kw = art.get("メインKW", "")
        if not main_kw:
            tags = art.get("タグ（キーワード）", "")
            main_kw = tags.split(",")[0].strip() if tags else slug

        articles.append({
            "ID": f"{site}_{slug}",
            "サイト": site,
            "ジャンル": genre,
            "分類": category,
            "記事タイプ": article_type,
            "メインKW": main_kw,
            "タイトル": title,
            "スラッグ": slug,
            "URL": url,
            "公開日": pub_display,
            "更新期限": deadline_str,
            "前回更新": update_display,
            "担当": art.get("担当者", "") if art.get("担当者", "") else random.choice(["（仮）札幌A", "（仮）札幌B", "（仮）東京C", "（仮）東京D", "（仮）インターンE"]),
            "先月PV": last_month_pv,
            "現PV": current_pv,
            "PV比": pv_ratio,
            "順位": position,
            "前回順位": prev_position,
            "順位変動": pos_change,
            "Impr": impressions,
            "Click": clicks,
            "CTR": ctr,
            "ステータス": status,
            "競合1位": round(random.uniform(1, 20), 1),
            "競合2位": round(random.uniform(1, 20), 1),
            "競合3位": round(random.uniform(1, 20), 1),
            "競合変動": round(random.uniform(-5, 5), 1),
            "データソース": "スプシ" if gsc_pages is not None else "スプシのみ",
        })

    return pd.DataFrame(articles)


# データ読み込み分岐
if use_real_data:
    spreadsheet_df = load_from_spreadsheet()
    if spreadsheet_df is not None and not spreadsheet_df.empty:
        df = spreadsheet_df
        _, history_df = generate_data()  # 推移データはまだダミー
    else:
        st.warning("⚠️ スプシからデータ取得できませんでした。ダミーデータを表示します。")
        df, history_df = generate_data()
else:
    df, history_df = generate_data()


# =====================
# ヘルパー
# =====================
def rate_class(rate):
    if rate >= 90: return "good"
    if rate >= 70: return "ok"
    return "bad"

def pos_color(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    if v <= 3: return "background-color: #28a745; color: white"
    elif v <= 10: return "background-color: #c8e6c9"
    elif v <= 30: return "background-color: #fff9c4"
    elif v <= 50: return "background-color: #ffe0b2"
    else: return "background-color: #f8d7da"

def change_color(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    if v >= 3: return "background-color: #f8d7da; color: #721c24"
    elif v >= 1: return "background-color: #fff3cd; color: #856404"
    elif v <= -3: return "background-color: #d4edda; color: #155724"
    elif v <= -1: return "background-color: #d4edda; color: #155724"
    return ""

def pv_color(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    if v < 60: return "background-color: #f8d7da; color: #721c24"
    elif v < 80: return "background-color: #fff3cd; color: #856404"
    elif v >= 100: return "background-color: #d4edda; color: #155724"
    return ""

def draw_sparkline(hist_subset, col="PV", color="#1565c0"):
    """ミニ推移グラフを描画"""
    import altair as alt
    hist_subset = hist_subset.copy()
    hist_subset["日付"] = pd.to_datetime(hist_subset["日付"])
    chart = alt.Chart(hist_subset).mark_area(
        line={"color": color},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color=color, offset=1),
                alt.GradientStop(color="white", offset=0),
            ],
            x1=1, x2=1, y1=1, y2=0,
        ),
        opacity=0.3,
    ).encode(
        x=alt.X("日付:T", axis=alt.Axis(format="%m/%d", labelAngle=-45, title=None)),
        y=alt.Y(f"{col}:Q", title=None),
    ).properties(height=150)
    line = alt.Chart(hist_subset).mark_line(color=color, strokeWidth=2).encode(
        x="日付:T", y=f"{col}:Q",
    )
    return chart + line


# =====================
# ヘッダー + フィルタ（サイト軸追加）
# =====================
col_h1, col_h2, col_h3, col_h4 = st.columns([2.5, 1, 1, 0.5])
with col_h1:
    st.markdown("## 📊 記事管理DB")
with col_h2:
    site_filter = st.selectbox("サイト", ["全サイト"] + sorted(df["サイト"].unique().tolist()), label_visibility="collapsed")
with col_h3:
    genre_filter = st.selectbox("ジャンル", ["全体"] + sorted(df["ジャンル"].unique().tolist()), label_visibility="collapsed")
with col_h4:
    st.caption(f"更新: {datetime.now().strftime('%H:%M')}")

# フィルタ適用
filtered = df.copy()
if site_filter != "全サイト":
    filtered = filtered[filtered["サイト"] == site_filter]
if genre_filter != "全体":
    filtered = filtered[filtered["ジャンル"] == genre_filter]


# =====================
# タブ
# =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 概要", "📋 記事一覧", "🔔 アラート", "📈 効果計測", "👥 メンバー"])


# ========== 概要タブ ==========
with tab1:
    total = len(filtered)
    # 記事タイプ別カウント
    type_col = "記事タイプ" if "記事タイプ" in filtered.columns else "分類"
    pv_type_count = len(filtered[filtered[type_col] == "PV型"]) if type_col == "記事タイプ" else len(filtered[filtered["分類"] == "ノウハウ"])
    cv_type_count = len(filtered[filtered[type_col] == "CV型"]) if type_col == "記事タイプ" else len(filtered[filtered["分類"] == "CV"])

    alert_df = filtered[filtered["PV比"] < 80]
    alert_count = len(alert_df)
    alert_pv = len(alert_df[alert_df[type_col] == "PV型"]) if type_col == "記事タイプ" else 0
    alert_cv = len(alert_df[alert_df[type_col] == "CV型"]) if type_col == "記事タイプ" else 0

    pos_drop_df = filtered[filtered["順位変動"] >= 5]
    pos_drop_count = len(pos_drop_df)
    pos_drop_pv = len(pos_drop_df[pos_drop_df[type_col] == "PV型"]) if type_col == "記事タイプ" else 0
    pos_drop_cv = len(pos_drop_df[pos_drop_df[type_col] == "CV型"]) if type_col == "記事タイプ" else 0

    avg_pos = filtered["順位"].mean()
    avg_pv_ratio = filtered["PV比"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="label">総記事数</div>
            <div class="value">{total}</div>
            <div class="sub">{pv_type_count} ノウハウ(PV型) / {cv_type_count} CV型</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card">
            <div class="label">PVアラート</div>
            <div class="value" style="color: {'#c62828' if alert_count > 5 else '#e65100' if alert_count > 0 else '#2e7d32'}">{alert_count}件</div>
            <div class="sub">ノウハウ {alert_pv} / CV {alert_cv}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card">
            <div class="label">順位急落</div>
            <div class="value" style="color: {'#c62828' if pos_drop_count > 3 else '#e65100' if pos_drop_count > 0 else '#2e7d32'}">{pos_drop_count}件</div>
            <div class="sub">ノウハウ {pos_drop_pv} / CV {pos_drop_cv}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        pv_type_df = filtered[filtered[type_col] == "PV型"] if type_col == "記事タイプ" else pd.DataFrame()
        cv_type_df = filtered[filtered[type_col] == "CV型"] if type_col == "記事タイプ" else pd.DataFrame()
        avg_pos_pv = pv_type_df["順位"].mean() if not pv_type_df.empty else 0
        avg_pos_cv = cv_type_df["順位"].mean() if not cv_type_df.empty else 0
        st.markdown(f"""<div class="kpi-card">
            <div class="label">平均順位</div>
            <div class="value">{avg_pos:.1f}</div>
            <div class="sub">ノウハウ {avg_pos_pv:.1f} / CV {avg_pos_cv:.1f}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        avg_pv_pv = pv_type_df["PV比"].mean() if not pv_type_df.empty else 0
        avg_pv_cv = cv_type_df["PV比"].mean() if not cv_type_df.empty else 0
        rc = rate_class(avg_pv_ratio)
        st.markdown(f"""<div class="kpi-card">
            <div class="label">平均PV前月比</div>
            <div class="value g-rate {rc}">{avg_pv_ratio:.0f}%</div>
            <div class="sub">ノウハウ {avg_pv_pv:.0f}% / CV {avg_pv_cv:.0f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ジャンル別カード
    st.markdown('<div class="sec-title">📁 ジャンル別</div>', unsafe_allow_html=True)
    genres = filtered["ジャンル"].unique()
    cols = st.columns(min(len(genres), 5))
    for i, genre in enumerate(genres):
        gdf = filtered[filtered["ジャンル"] == genre]
        g_total = len(gdf)
        g_completed = len(gdf[gdf["ステータス"] == "完了"])
        g_alert = len(gdf[gdf["PV比"] < 80])
        g_pos_drop = len(gdf[gdf["順位変動"] >= 5])
        g_rate = round(g_completed / g_total * 100) if g_total > 0 else 0
        cls = rate_class(g_rate)

        with cols[i % len(cols)]:
            st.markdown(f"""<div class="genre-card {cls}">
                <div class="g-title">{genre}</div>
                <div class="g-rate {cls}">{g_rate}%</div>
                <div class="g-stats">{g_completed}/{g_total}記事完了 | 平均順位 {gdf['順位'].mean():.1f}</div>
                <div class="g-stats">{'🔴 PV ' + str(g_alert) + '件' if g_alert > 0 else '🟢 PV OK'} | {'⚡ 急落 ' + str(g_pos_drop) + '件' if g_pos_drop > 0 else ''}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # 直近アラート（PV + 順位急落 統合）
    st.markdown('<div class="sec-title">⚡ 直近アラート</div>', unsafe_allow_html=True)

    # PVアラート
    pv_alerts = filtered[filtered["PV比"] < 80].sort_values("PV比").head(3)
    # 順位急落
    pos_alerts = filtered[filtered["順位変動"] >= 5].sort_values("順位変動", ascending=False).head(3)

    al1, al2 = st.columns(2)
    with al1:
        st.caption("📉 PV低下")
        if pv_alerts.empty:
            st.markdown('<div class="alert-card ok"><div class="a-title">🟢 なし</div></div>', unsafe_allow_html=True)
        for _, row in pv_alerts.iterrows():
            cls = "danger" if row["PV比"] < 60 else "warning"
            st.markdown(f"""<div class="alert-card {cls}">
                <div class="a-title">{'🔴' if cls == 'danger' else '🟡'} {row['メインKW']}（{row['ジャンル']}）</div>
                <div class="a-sub">前月比 {row['PV比']}% | 順位 {'圏外' if row['順位'] >= 100 else row['順位']} | 担当: {row['担当'] if row['担当'] else '未割当'}</div>
            </div>""", unsafe_allow_html=True)

    with al2:
        st.caption("⚡ 順位急落（5位以上悪化）")
        if pos_alerts.empty:
            st.markdown('<div class="alert-card ok"><div class="a-title">🟢 なし</div></div>', unsafe_allow_html=True)
        for _, row in pos_alerts.iterrows():
            st.markdown(f"""<div class="alert-card danger">
                <div class="a-title">⚡ {row['メインKW']}（{row['ジャンル']}）</div>
                <div class="a-sub">順位 {'圏外' if row['前回順位'] >= 100 else f"{row['前回順位']:.1f}"} → {'圏外' if row['順位'] >= 100 else row['順位']} ({row['順位変動']:+.1f}) | 前月比 {row['PV比']}%{f" | 競合: {row['競合変動']:+.1f}" if '競合変動' in row.index else ''}</div>
            </div>""", unsafe_allow_html=True)


# ========== 記事一覧タブ ==========
with tab2:
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])
    with fc1:
        cat_filter = st.selectbox("分類", ["すべて", "ノウハウ", "CV", "商標", "地域"], key="cat_f")
    with fc2:
        status_filter = st.selectbox("ステータス", ["すべて", "未対応", "対応中", "完了", "監視中"], key="st_f")
    with fc3:
        sort_option = st.selectbox("並び替え", ["PV比（低い順）", "順位（悪い順）", "順位変動（大きい順）", "Impr（多い順）"], key="sort_f")
    with fc4:
        pv_alert_only = st.checkbox("🔴 PVアラートのみ", key="pv_alert")

    tdf = filtered.copy()
    if cat_filter != "すべて":
        tdf = tdf[tdf["分類"] == cat_filter]
    if status_filter != "すべて":
        tdf = tdf[tdf["ステータス"] == status_filter]
    if pv_alert_only:
        tdf = tdf[tdf["PV比"] < 80]

    sort_map = {
        "PV比（低い順）": ("PV比", True),
        "順位（悪い順）": ("順位", False),
        "順位変動（大きい順）": ("順位変動", False),
        "Impr（多い順）": ("Impr", False),
    }
    s_col, s_asc = sort_map[sort_option]
    tdf = tdf.sort_values(s_col, ascending=s_asc)

    # スラッグ列を追加（URLから生成）
    tdf = tdf.copy()
    tdf["スラッグ"] = tdf["URL"].apply(lambda x: x.rstrip("/").split("/")[-1] if isinstance(x, str) and x.startswith("http") else "-")

    all_display_cols = ["ステータス", "サイト", "分類", "タイトル", "スラッグ", "PV比", "先月PV", "現PV", "順位", "順位変動", "Impr", "Click", "CTR", "公開日", "前回更新", "URL"]
    display_cols = [c for c in all_display_cols if c in tdf.columns]
    st.markdown(f'<div class="sec-title">📋 {len(tdf)}件表示</div>', unsafe_allow_html=True)

    # 順位の圏外表示用にコピー
    display_df = tdf[display_cols].copy()
    display_df["順位"] = display_df["順位"].apply(lambda x: "圏外" if x >= 100 else f"{x:.1f}")

    def pos_color_with_rankout(val):
        if val == "圏外": return "background-color: #d32f2f; color: white"
        try:
            return pos_color(float(val))
        except (ValueError, TypeError):
            return ""

    style_maps = []
    if "順位" in display_df.columns:
        style_maps.append(("順位", pos_color_with_rankout))
    if "順位変動" in display_df.columns:
        style_maps.append(("順位変動", change_color))
    if "PV比" in display_df.columns:
        style_maps.append(("PV比", pv_color))

    styled = display_df.style
    for col, func in style_maps:
        styled = styled.applymap(func, subset=[col])

    fmt = {}
    if "順位変動" in display_df.columns:
        fmt["順位変動"] = "{:+.1f}"
    if "CTR" in display_df.columns:
        fmt["CTR"] = "{:.1f}%"
    if "PV比" in display_df.columns:
        fmt["PV比"] = "{}%"
    if fmt:
        styled = styled.format(fmt)

    st.dataframe(styled, use_container_width=True, height=600)

    # 記事詳細（推移グラフ）
    st.markdown('<div class="sec-title">🔍 記事詳細（推移グラフ）</div>', unsafe_allow_html=True)
    article_options = tdf["メインKW"].tolist()
    if article_options:
        selected_article = st.selectbox("記事を選択", article_options, key="article_detail")
        sel_row = tdf[tdf["メインKW"] == selected_article].iloc[0]
        sel_history = history_df[history_df["ID"] == sel_row["ID"]]

        if not sel_history.empty:
            dc1, dc2 = st.columns(2)
            with dc1:
                st.caption("📈 PV推移（30日）")
                st.altair_chart(draw_sparkline(sel_history, "PV", "#1565c0"), use_container_width=True)
            with dc2:
                st.caption("📉 順位推移（30日）※低いほど良い")
                st.altair_chart(draw_sparkline(sel_history, "順位", "#c62828"), use_container_width=True)

            # 競合比較
            if "競合1位" in sel_row.index:
                st.caption("🏆 競合ポジション比較")
                cc1, cc2, cc3, cc4 = st.columns(4)
                cc1.metric("自社順位", f"{sel_row['順位']:.1f}", delta=f"{sel_row['順位変動']:+.1f}", delta_color="inverse")
                cc2.metric("競合1位", f"{sel_row['競合1位']:.1f}")
                cc3.metric("競合2位", f"{sel_row['競合2位']:.1f}")
                cc4.metric("競合3位", f"{sel_row['競合3位']:.1f}")
                st.caption(f"競合の平均変動: {sel_row['競合変動']:+.1f}（+は競合が悪化 = チャンス）")


# ========== アラートタブ ==========
with tab3:
    ac1, ac2, ac3 = st.columns(3)

    with ac1:
        st.markdown('<div class="sec-title">🔴 PVアラート（80%以下）</div>', unsafe_allow_html=True)
        pv_alerts_full = filtered[filtered["PV比"] < 80].sort_values("PV比")
        if pv_alerts_full.empty:
            st.success("なし")
        for _, row in pv_alerts_full.iterrows():
            cls = "danger" if row["PV比"] < 60 else "warning"
            with st.expander(f"{'🔴' if cls == 'danger' else '🟡'} {row['メインKW']} — 前月比 {row['PV比']}%"):
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("現PV", f"{row['現PV']:,}")
                mc2.metric("先月PV", f"{row['先月PV']:,}")
                pos_display = "圏外" if row["順位"] >= 100 else f"{row['順位']:.1f}"
                mc3.metric("順位", pos_display, delta=f"{row['順位変動']:+.1f}", delta_color="inverse")
                mc4.metric("CTR", f"{row['CTR']}%")
                st.caption(f"{row['ジャンル']} / {row['分類']} / 担当: {row['担当'] if row['担当'] else '未割当'}")
                # ミニ推移
                sel_h = history_df[history_df["ID"] == row["ID"]]
                if not sel_h.empty:
                    st.altair_chart(draw_sparkline(sel_h, "PV", "#c62828"), use_container_width=True)

    with ac2:
        st.markdown('<div class="sec-title">⚡ 順位急落（5位以上）</div>', unsafe_allow_html=True)
        pos_alerts_full = filtered[filtered["順位変動"] >= 5].sort_values("順位変動", ascending=False)
        if pos_alerts_full.empty:
            st.success("なし")
        for _, row in pos_alerts_full.iterrows():
            with st.expander(f"⚡ {row['メインKW']} — {row['順位変動']:+.1f}位"):
                mc1, mc2, mc3 = st.columns(3)
                pos_display = "圏外" if row["順位"] >= 100 else f"{row['順位']:.1f}"
                mc1.metric("順位", pos_display, delta=f"{row['順位変動']:+.1f}", delta_color="inverse")
                mc2.metric("PV前月比", f"{row['PV比']}%")
                if "競合変動" in row.index:
                    mc3.metric("競合変動", f"{row['競合変動']:+.1f}")
                    st.caption(f"競合が{'改善' if row['競合変動'] < 0 else '悪化'}傾向 → {'競合に抜かれた可能性' if row['競合変動'] < 0 else '自社の問題の可能性'}")
                sel_h = history_df[history_df["ID"] == row["ID"]]
                if not sel_h.empty:
                    st.altair_chart(draw_sparkline(sel_h, "順位", "#c62828"), use_container_width=True)

    with ac3:
        st.markdown('<div class="sec-title">⏰ 更新期限切れ</div>', unsafe_allow_html=True)
        today_str = datetime.now().strftime("%Y/%m/%d")
        overdue_df = filtered[(filtered["更新期限"] < today_str) & (filtered["ステータス"] != "完了")].sort_values("更新期限")
        if overdue_df.empty:
            st.success("なし")
        for _, row in overdue_df.iterrows():
            try:
                days_over = (datetime.now() - datetime.strptime(row["更新期限"], "%Y/%m/%d")).days
            except:
                days_over = 0
            cls = "danger" if days_over > 14 else "warning"
            st.markdown(f"""<div class="alert-card {cls}">
                <div class="a-title">⏰ {row['メインKW']}（{row['ジャンル']}）</div>
                <div class="a-sub">{days_over}日超過 | 担当: {row['担当'] if row['担当'] else '未割当'}</div>
            </div>""", unsafe_allow_html=True)


# ========== 効果計測タブ（NEW） ==========
with tab4:
    st.markdown('<div class="sec-title">📈 更新後の効果計測</div>', unsafe_allow_html=True)
    st.caption("前回更新がある記事の、更新前後のPV・順位変化を表示")

    updated_articles = filtered[filtered["前回更新"] != "-"].copy()

    if updated_articles.empty:
        st.info("更新済み記事がありません")
    else:
        # 効果スコア計算（ダミー: PV比と順位変動から推定）
        updated_articles["効果スコア"] = updated_articles.apply(
            lambda r: "改善" if r["PV比"] >= 100 and r["順位変動"] <= 0 else ("悪化" if r["PV比"] < 80 else "横ばい"), axis=1
        )

        # サマリー
        improved = len(updated_articles[updated_articles["効果スコア"] == "改善"])
        worsened = len(updated_articles[updated_articles["効果スコア"] == "悪化"])
        flat = len(updated_articles[updated_articles["効果スコア"] == "横ばい"])

        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.markdown(f"""<div class="kpi-card">
                <div class="label">改善</div>
                <div class="value" style="color: #2e7d32">{improved}件</div>
                <div class="sub">PV100%以上 & 順位維持/改善</div>
            </div>""", unsafe_allow_html=True)
        with ec2:
            st.markdown(f"""<div class="kpi-card">
                <div class="label">横ばい</div>
                <div class="value" style="color: #f9a825">{flat}件</div>
                <div class="sub">PV80-100%</div>
            </div>""", unsafe_allow_html=True)
        with ec3:
            st.markdown(f"""<div class="kpi-card">
                <div class="label">悪化</div>
                <div class="value" style="color: #c62828">{worsened}件</div>
                <div class="sub">更新しても PV80%以下</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # 記事ごとの効果
        for score_label, score_cls in [("改善", "up"), ("横ばい", "flat"), ("悪化", "down")]:
            subset = updated_articles[updated_articles["効果スコア"] == score_label].sort_values("PV比", ascending=(score_label == "悪化"))
            if not subset.empty:
                icon = {"改善": "🟢", "横ばい": "🟡", "悪化": "🔴"}[score_label]
                st.markdown(f'<div class="sec-title">{icon} {score_label}（{len(subset)}件）</div>', unsafe_allow_html=True)
                for _, row in subset.iterrows():
                    with st.expander(f"{icon} {row['メインKW']}（{row['ジャンル']}・{row['分類']}）— PV {row['PV比']}% / 順位 {row['順位変動']:+.1f}"):
                        erc1, erc2 = st.columns(2)
                        with erc1:
                            st.metric("PV前月比", f"{row['PV比']}%", delta=f"{row['PV比'] - 100}%")
                            st.metric("順位変動", f"{row['順位']}", delta=f"{row['順位変動']:+.1f}", delta_color="inverse")
                        with erc2:
                            sel_h = history_df[history_df["ID"] == row["ID"]]
                            if not sel_h.empty:
                                st.altair_chart(draw_sparkline(sel_h, "PV", "#1565c0" if score_label != "悪化" else "#c62828"), use_container_width=True)
                        st.caption(f"更新日: {row['前回更新']} | 担当: {row['担当'] if row['担当'] else '未割当'}")


# ========== メンバータブ ==========
with tab5:
    assigned = filtered[filtered["担当"] != ""]
    members = sorted(assigned["担当"].unique()) if not assigned.empty else []

    member_options = ["全体サマリー"] + members
    selected_member = st.selectbox("メンバー選択", member_options, key="member_select")

    if selected_member == "全体サマリー":
        st.markdown('<div class="sec-title">👥 メンバー別進捗</div>', unsafe_allow_html=True)

        cols = st.columns(min(len(members), 6)) if members else []
        for i, member in enumerate(members):
            mdf = assigned[assigned["担当"] == member]
            m_total = len(mdf)
            m_done = len(mdf[mdf["ステータス"] == "完了"])
            m_alert = len(mdf[mdf["PV比"] < 80])
            m_rate = round(m_done / m_total * 100) if m_total > 0 else 0
            cls = rate_class(m_rate)

            with cols[i % len(cols)]:
                st.markdown(f"""<div class="member-card {cls}">
                    <div class="m-name">{member}</div>
                    <div class="m-count">{m_done}/{m_total}</div>
                    <div class="m-sub">完了率 {m_rate}% | アラート {m_alert}件</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("")
        st.markdown('<div class="sec-title">📊 メンバー × ジャンル</div>', unsafe_allow_html=True)

        if not assigned.empty:
            pivot = assigned.pivot_table(index="担当", columns="ジャンル", values="メインKW", aggfunc="count", fill_value=0)
            pivot["合計"] = pivot.sum(axis=1)
            pivot = pivot.sort_values("合計", ascending=False)
            st.dataframe(pivot, use_container_width=True)

    else:
        # === 個別メンバー画面（GOALベース） ===
        mdf = filtered[filtered["担当"] == selected_member]
        m_knowhow = mdf[mdf["分類"] == "ノウハウ"]
        m_cv = mdf[mdf["分類"] == "CV"]
        m_other = mdf[~mdf["分類"].isin(["ノウハウ", "CV"])]

        # --- GOAL: ノウハウ記事 ---
        st.markdown('<div class="sec-title">🎯 ノウハウ記事 — 全記事を更新サイクルに乗せる</div>', unsafe_allow_html=True)

        if not m_knowhow.empty:
            kh_total = len(m_knowhow)
            kh_overdue = len(m_knowhow[(m_knowhow["更新期限"] < datetime.now().strftime("%Y/%m/%d")) & (m_knowhow["ステータス"] != "完了")])
            kh_alert = len(m_knowhow[m_knowhow["PV比"] < 80])
            kh_ok = max(0, kh_total - kh_overdue - kh_alert)
            kh_clear_rate = max(0, round(kh_ok / kh_total * 100) if kh_total > 0 else 0)

            bar_color = "#2e7d32" if kh_clear_rate >= 80 else "#e65100" if kh_clear_rate >= 50 else "#c62828"
            st.markdown(f"""
            <div style="margin: 8px 0 4px 0;">
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                    <span style="font-size:13px; color:#607d8b;">更新サイクル達成率</span>
                    <span style="font-size:28px; font-weight:700; color:{bar_color};">{kh_clear_rate}%</span>
                </div>
                <div style="background:#e0e4ea; border-radius:6px; height:12px; margin:6px 0;">
                    <div style="background:{bar_color}; border-radius:6px; height:12px; width:{kh_clear_rate}%;"></div>
                </div>
                <div style="display:flex; gap:24px; font-size:12px; color:#607d8b; margin-top:4px;">
                    <span>📝 全{kh_total}本</span>
                    <span style="color:#c62828;">⏰ 期限切れ {kh_overdue}本</span>
                    <span style="color:#e65100;">📉 PVアラート {kh_alert}本</span>
                    <span style="color:#2e7d32;">✅ 問題なし {kh_ok}本</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            kh_action = m_knowhow[(m_knowhow["更新期限"] < datetime.now().strftime("%Y/%m/%d")) | (m_knowhow["PV比"] < 80)]
            kh_action = kh_action[kh_action["ステータス"] != "完了"].sort_values("PV比")

            if not kh_action.empty:
                for _, row in kh_action.iterrows():
                    reasons = []
                    if row["PV比"] < 80:
                        reasons.append(f"📉 PV {row['PV比']}%")
                    try:
                        if row["更新期限"] < datetime.now().strftime("%Y/%m/%d"):
                            days_over = (datetime.now() - datetime.strptime(row["更新期限"], "%Y/%m/%d")).days
                            reasons.append(f"⏰ {days_over}日超過")
                    except:
                        pass
                    if row["順位変動"] >= 5:
                        reasons.append(f"⚡ 順位急落 {row['順位変動']:+.1f}")
                    reason_str = " / ".join(reasons)
                    cls = "danger" if row["PV比"] < 60 else "warning"
                    st.markdown(f"""<div class="alert-card {cls}">
                        <div class="a-title">{'🔴' if cls == 'danger' else '🟡'} {row['メインKW']}（{row['ジャンル']}）</div>
                        <div class="a-sub">{reason_str} | 順位 {'圏外' if row['順位'] >= 100 else row['順位']} | ステータス: {row['ステータス']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-card ok"><div class="a-title">✅ ノウハウ記事は全部クリア！</div></div>', unsafe_allow_html=True)
        else:
            st.caption("ノウハウ記事の担当なし")

        st.markdown("")

        # --- GOAL: CV記事 ---
        st.markdown('<div class="sec-title">🎯 CV記事 — 週1更新を維持する</div>', unsafe_allow_html=True)

        if not m_cv.empty:
            cv_total = len(m_cv)
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y/%m/%d")
            cv_updated_this_week = len(m_cv[m_cv["前回更新"] >= week_start])
            cv_not_updated = cv_total - cv_updated_this_week
            cv_rate = round(cv_updated_this_week / cv_total * 100) if cv_total > 0 else 0
            days_left = max(0, 6 - today.weekday())

            bar_color = "#2e7d32" if cv_rate >= 80 else "#e65100" if cv_rate >= 50 else "#c62828"
            st.markdown(f"""
            <div style="margin: 8px 0 4px 0;">
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                    <span style="font-size:13px; color:#607d8b;">今週の更新率</span>
                    <span style="font-size:28px; font-weight:700; color:{bar_color};">{cv_updated_this_week}/{cv_total}</span>
                </div>
                <div style="background:#e0e4ea; border-radius:6px; height:12px; margin:6px 0;">
                    <div style="background:{bar_color}; border-radius:6px; height:12px; width:{cv_rate}%;"></div>
                </div>
                <div style="display:flex; gap:24px; font-size:12px; color:#607d8b; margin-top:4px;">
                    <span>✅ 更新済み {cv_updated_this_week}本</span>
                    <span style="color:#c62828;">❌ 未更新 {cv_not_updated}本</span>
                    <span>📅 今週あと{days_left}日</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            cv_todo = m_cv[m_cv["前回更新"] < week_start].sort_values("PV比")
            if not cv_todo.empty:
                for _, row in cv_todo.iterrows():
                    cls = "danger" if row["PV比"] < 80 else "warning"
                    st.markdown(f"""<div class="alert-card {cls}">
                        <div class="a-title">{'🔴' if row['PV比'] < 80 else '🟡'} {row['メインKW']}（{row['ジャンル']}）</div>
                        <div class="a-sub">今週未更新 | PV {row['PV比']}% | 順位 {'圏外' if row['順位'] >= 100 else row['順位']} | 前回: {row['前回更新']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-card ok"><div class="a-title">✅ CV記事は今週全部更新済み！</div></div>', unsafe_allow_html=True)
        else:
            st.caption("CV記事の担当なし")

        st.markdown("")

        # その他
        if not m_other.empty:
            st.markdown(f'<div class="sec-title">📋 その他の担当記事（{len(m_other)}本）</div>', unsafe_allow_html=True)
            for _, row in m_other[m_other["ステータス"] != "完了"].sort_values("PV比").iterrows():
                cls = "danger" if row["PV比"] < 80 else ""
                st.markdown(f"""<div class="alert-card {cls if cls else ''}">
                    <div class="a-title">{row['メインKW']}（{row['ジャンル']}・{row['分類']}）</div>
                    <div class="a-sub">PV {row['PV比']}% | 順位 {'圏外' if row['順位'] >= 100 else row['順位']} | ステータス: {row['ステータス']}</div>
                </div>""", unsafe_allow_html=True)

        # 完了実績
        done = mdf[mdf["ステータス"] == "完了"]
        if not done.empty:
            st.markdown(f'<div class="sec-title">✅ 完了（{len(done)}本）</div>', unsafe_allow_html=True)
            for _, row in done.iterrows():
                st.markdown(f"""<div class="alert-card ok">
                    <div class="a-title">✅ {row['メインKW']}（{row['ジャンル']}・{row['分類']}）</div>
                    <div class="a-sub">PV {row['PV比']}% | 順位 {'圏外' if row['順位'] >= 100 else row['順位']} | 更新: {row['前回更新']}</div>
                </div>""", unsafe_allow_html=True)
