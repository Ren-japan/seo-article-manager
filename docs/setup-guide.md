# SEO Article Manager セットアップ手順書

> **対象**: チームメンバー全員（エンジニアじゃなくてOK。Claude Codeが使える人向け）
>
> **ゴール**: 自分のPCでこのツールを動かせるようにして、チーム共通のスプレッドシートを読み書きできる状態にする
>
> **所要時間**: 約10分

---

## 事前に必要なもの

| 必要なもの | 確認方法 |
|---|---|
| Mac（またはWindows/Linux） | - |
| Python 3.9以上 | ターミナルで `python3 --version` と打って `3.9` 以上ならOK |
| Git（ファイルのバージョン管理ツール） | ターミナルで `git --version` と打ってバージョンが出ればOK |
| Claude Code | 普段使ってるやつでOK |

> **Pythonが入ってない・バージョンが古い場合**: れんくんに聞いてください。一緒にインストールします。

---

## Step 1: プロジェクトをダウンロードする

ターミナル（Macなら「ターミナル」アプリ）を開いて、以下を **そのままコピペ** して実行してください。

```bash
cd ~/Desktop && git clone https://github.com/your-org/seo-article-manager.git
```

**何が起きるか**: GitHubからプロジェクトのファイル一式が、デスクトップの `seo-article-manager` フォルダにダウンロードされます。

**成功したら**: デスクトップに `seo-article-manager` というフォルダが出現します。

> **エラーが出たら**:
> - `Permission denied` → れんくんにGitHubのアクセス権をもらってください
> - `command not found: git` → Gitが入ってません。れんくんに聞いてください

---

## Step 2: 認証ファイルを配置する

**credentials.json**（スプレッドシートにアクセスするための鍵ファイル）を正しい場所に置きます。

### 2-1. ファイルを受け取る

Slackでれんくんから `credentials.json` を受け取ってください。まだもらってなければDMで「credentials.jsonください」と送ればOKです。

### 2-2. ファイルを移動する

受け取った `credentials.json` を、**Step 1でダウンロードしたフォルダの直下** に置きます。

**一番かんたんな方法**: Slackからダウンロードした `credentials.json` を、デスクトップの `seo-article-manager` フォルダにドラッグ&ドロップ。

**ターミナルでやる場合**:

```bash
mv ~/Downloads/credentials.json ~/Desktop/seo-article-manager/
```

### 2-3. 置けたか確認する

```bash
ls ~/Desktop/seo-article-manager/credentials.json
```

ファイルパスが表示されればOK。`No such file` と出たら、ファイルの場所が間違ってます。

> **credentials.jsonをなくした場合**: れんくんに言えば再発行してもらえます。

---

## Step 3: ライブラリをインストールする

プロジェクトが使う外部ツール（ライブラリ）をインストールします。

```bash
cd ~/Desktop/seo-article-manager && pip install gspread google-auth
```

**何が起きるか**: Pythonがスプレッドシートと通信するために必要な部品2つがインストールされます。
- `gspread`（Google スプレッドシートを操作するツール）
- `google-auth`（Googleに「自分は許可された人です」と証明するツール）

**成功したら**: `Successfully installed ...` と表示されます。

> **エラーが出たら**:
> - `pip: command not found` → `pip3` に変えて試してください:
>   ```bash
>   cd ~/Desktop/seo-article-manager && pip3 install gspread google-auth
>   ```
> - `Permission denied` → 先頭に `sudo` をつけてください（PCのパスワードを聞かれます）:
>   ```bash
>   cd ~/Desktop/seo-article-manager && sudo pip3 install gspread google-auth
>   ```

---

## Step 4: 動作確認する

すべて正しくセットアップできたか、テストします。

```bash
cd ~/Desktop/seo-article-manager && python3 -c "from lib.spreadsheet import get_all_articles; print(f'{len(get_all_articles())}件の記事データ取得OK')"
```

### 成功パターン

```
42件の記事データ取得OK
```

（数字は記事の数なのでタイミングによって変わります）

**この表示が出たらセットアップ完了です!**

### 失敗パターンと対処法

| エラーメッセージ | 原因 | 対処 |
|---|---|---|
| `FileNotFoundError: credentials.json` | 認証ファイルが見つからない | Step 2をやり直す。ファイルの置き場所を確認 |
| `ModuleNotFoundError: No module named 'gspread'` | ライブラリが入ってない | Step 3をやり直す |
| `google.auth.exceptions.DefaultCredentialsError` | credentials.jsonの中身が壊れている | れんくんから再発行してもらう |
| `PermissionError` または `403` | スプシへのアクセス権がない | れんくんにスプシの共有設定を確認してもらう |

---

## 絶対やっちゃダメなこと

### credentials.json を GitHub に push しない

`credentials.json` はスプレッドシートの鍵です。GitHubに上げると **誰でもスプシを触れてしまう** ので、絶対にpushしないでください。

（`.gitignore` で自動的に除外される設定にしてありますが、念のため注意してください）

もし間違ってpushしちゃった場合は、**すぐにれんくんに連絡** してください。鍵の無効化と再発行が必要です。

---

## 困ったときは

何かうまくいかないときは、**エラーメッセージのスクショ** をれんくんに送ってください。テキストで送るよりスクショの方が解決が早いです。
