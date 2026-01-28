# teams transcript notion sync

## ディレクトリ構成

teams-transcript-notion-sync/
  ├─ pyproject.toml
  ├─ uv.lock
  ├─ .env.example
  ├─ .gitignore
  ├─ src/
  │   └─ teams_transcript_notion_sync/
  │       ├─ __init__.py
  │       ├─ config.py
  │       ├─ db.py
  │       ├─ scanner.py
  │       ├─ transcribe.py
  │       ├─ summarizer.py
  │       ├─ notion_writer.py
  │       └─ main.py
  ├─ tests/
  │   ├─ conftest.py
  │   ├─ test_config.py
  │   ├─ test_scanner.py
  │   ├─ test_transcribe.py
  │   ├─ test_summarizer.py
  │   └─ test_notion_writer.py
  ├─ data/
  ├─ transcripts/
  ├─ summaries/
  ├─ Dockerfile
  └─ docker-compose.yml

## 初回セットアップ

```
uv init --package teams-transcript-notion-sync

uv add notion-client python-dotenv requests openai pytest
```

## 環境変数設定

## テスト

```
uv run pytest -q
```

### pyannote 統合テスト（任意）

Hugging Face のトークンとネットワークが必要です。

```
RUN_PYANNOTE_INTEGRATION=1 HF_TOKEN=hf_xxx uv run pytest -q -m integration
```

## whisper.cppの環境設定

- CoreMLモデルを使いたい場合は事前に利用予定のモデルに対して下記を実行する必要があり
```
./models/generate-coreml-model.sh base
```

## Notionインテグレーション
- Notion API secretを取得した後は接続先となるDBをnotion側で指定しておく必要がある
