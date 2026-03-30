# 記事管理DB 設計書

## DB: Supabase
## UI: Streamlit（リーダー用ダッシュボード）
## 操作: Claude Code スキル（メンバー用）

---

## テーブル設計

### 1. sites（サイト）
| カラム | 型 | 説明 |
|--------|------|------|
| id | uuid | PK |
| name | text | サイト名（例: 茅ヶ崎） |
| domain | text | ドメイン（例: www.chigasaki-mc.com） |
| genre | text | ジャンル（例: 包茎、ダイエット、AGA） |
| created_at | timestamp | 作成日 |

### 2. articles（記事）
| カラム | 型 | 説明 |
|--------|------|------|
| id | uuid | PK |
| site_id | uuid | FK → sites |
| title | text | 記事タイトル |
| url | text | 記事URL |
| category | text | 分類（ノウハウ / CV / 一般 / 商標 / 地域） |
| main_kw | text | メインKW |
| sub_kws | text[] | サブKW（配列） |
| published_at | date | 公開日 |
| update_deadline | date | 更新期限（公開日+14日で自動計算） |
| last_updated_at | date | 前回更新日 |
| status | text | ステータス（未対応 / 対応中 / 完了 / 監視中） |
| assignee | text | 担当者 |
| pv_target | integer | PV目安ライン |
| created_at | timestamp | レコード作成日 |
| updated_at | timestamp | レコード更新日 |

### 3. article_metrics（記事の数値 ※定期スキャンで自動更新）
| カラム | 型 | 説明 |
|--------|------|------|
| id | uuid | PK |
| article_id | uuid | FK → articles |
| date | date | 計測日 |
| pv | integer | ページビュー（GSC） |
| impressions | integer | 表示回数（GSC） |
| clicks | integer | クリック数（GSC） |
| ctr | decimal | CTR（GSC） |
| position | decimal | 平均順位（GSC） |
| organic_traffic | integer | オーガニックトラフィック（Ahrefs） |
| organic_keywords | integer | オーガニックKW数（Ahrefs） |
| referring_domains | integer | 被リンクドメイン数（Ahrefs） |
| created_at | timestamp | レコード作成日 |

### 4. article_tasks（タスク ※記事に紐づく）
| カラム | 型 | 説明 |
|--------|------|------|
| id | uuid | PK |
| article_id | uuid | FK → articles |
| task_type | text | タスク種別（期限更新 / PVアラート / 週次更新） |
| description | text | タスク内容 |
| assignee | text | 担当者 |
| status | text | ステータス（未対応 / 対応中 / 完了） |
| due_date | date | 期限 |
| completed_at | timestamp | 完了日時 |
| created_at | timestamp | 作成日時 |

### 5. intern_tasks（インターンタスク ※記事に紐づかないものも含む）
| カラム | 型 | 説明 |
|--------|------|------|
| id | uuid | PK |
| intern_name | text | インターン名 |
| next_work_date | date | 次回出勤日 |
| task_description | text | やること |
| article_id | uuid | FK → articles（NULL可。記事に紐づかないタスクもある） |
| status | text | ステータス（未対応 / 対応中 / 完了） |
| created_by | text | 誰が作ったか |
| created_at | timestamp | 作成日時 |
| completed_at | timestamp | 完了日時 |

### 6. activity_logs（完了ログ ※週報自動生成の元データ）
| カラム | 型 | 説明 |
|--------|------|------|
| id | uuid | PK |
| article_id | uuid | FK → articles（NULL可） |
| user_name | text | 誰がやったか |
| action | text | 何をしたか（記事更新 / タスク完了 / etc） |
| detail | text | 詳細メモ |
| created_at | timestamp | 日時 |

---

## テーブル関連図

```
sites
  │
  │ 1:N
  ▼
articles ──── article_metrics（1:N 日次で蓄積）
  │
  │ 1:N
  ├──── article_tasks
  │
  ├──── intern_tasks（NULL可でarticleに紐づく）
  │
  └──── activity_logs
```

---

## 自動処理

### 定期スキャン（毎日）
- GSC API → article_metrics に PV / 表示回数 / CTR / 順位を書き込み
- Ahrefs API → article_metrics にオーガニックトラフィック / KW数 / 被リンク数を書き込み

### トリガー処理
- PVが目安ラインの80%以下 → article_tasks にアラートタスク自動生成
- 公開日+14日到達 → article_tasks に更新タスク自動生成
- CV記事 → 毎週月曜に article_tasks に週次更新タスク自動生成

### ステータス自動更新
- article_tasks が全て完了 → articles.status を「完了」に
- PVアラート発火 → articles.status を「未対応」に

---

## データソース整理

| カラム | ソース |
|--------|--------|
| サイト・ジャンル | 既存スプシから初回インポート |
| 記事タイトル・URL・KW | 既存スプシから初回インポート |
| 分類（ノウハウ/CV等） | 既存スプシから初回インポート |
| 公開日 | 既存スプシ or WordPress |
| PV・CTR・順位 | GSC API（自動） |
| オーガニックトラフィック | Ahrefs API（自動） |
| PV目安ライン | urara が設定（手動） |
| 担当者 | スキルで割り当て |
| ステータス | 自動判定 + スキルで変更 |
