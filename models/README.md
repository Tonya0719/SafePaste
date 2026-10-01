# Local Model Files

Do not commit GLiNER model weights to Git.

Expected local path for this workspace:

```text
models/gliner_multi_pii-v1
```

Download command:

```powershell
python -c "from huggingface_hub import snapshot_download; print(snapshot_download(repo_id='urchade/gliner_multi_pii-v1', local_dir=r'C:\Users\DELL\Desktop\safepaste\models\gliner_multi_pii-v1'))"
```

Set `SAFEPASTE_GLINER_MODEL` to the local directory before running GLiNER or Hybrid experiments.
