# Local Model Files

Do not commit GLiNER model weights to Git.

Expected path from the repository root:

```text
models/gliner_multi_pii-v1
```

Download command:

```powershell
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='urchade/gliner_multi_pii-v1', local_dir='models/gliner_multi_pii-v1')"
```

Install the `ml` extra first with `python -m pip install -e ".[ml]"`. Copy `.env.example` to `.env` from the repository root; it points to this relative model directory. Run `python -m safepaste.cli analyze "Hi, I am Mei Tan." --mode hybrid` to check that a GLiNER span appears and no unavailable warning is returned. Downloading requires network access; subsequent analysis loads local model files only.
