# SafePaste 完整创建与实验执行计划

## 1 文档用途

本文件用于将 SafePaste 项目完整交接给 PyCharm 中的 Codex，并作为后续开发、实验、报告与演示的统一执行依据。

PyCharm Codex 在开始修改代码前，应先完整阅读本文件、项目根目录的 `README.md`、现有源码和测试。任何实验设计变更都应记录原因，不得为了提高最终测试成绩而修改冻结数据或反复调参。

## 2 最终提交要求

课程截图列出的最终提交物包括：

1. Problem statement；
2. Business and technical trade-off analysis，不超过 1,200 个英文单词；
3. GitHub repository 中可运行的代码；
4. Recorded video presentation / demo。

### 截止日期核实

截图显示截止时间为 **Sun 20 Sep 2026, 23:59**，但当前日期晚于该日期，而且老师此前反馈中提到过 4 October。开始最终排期前，必须以 LMS 最新页面或老师确认的信息为准，不要根据本文件猜测截止时间。

## 3 项目定义

### 3.1 一句话定义

SafePaste 是一个在用户把工作文本粘贴进公共 AI 助手之前，于本地检测、遮盖并允许恢复 PII 的 Hybrid 系统。

### 3.2 技术定义

SafePaste 结合：

- Presidio-based pattern recognisers：识别 email、phone、government-ID-shaped strings 等结构化 PII；
- 本地预训练 GLiNER：识别人名、地址等上下文 PII；
- Hybrid span orchestration：解决重复、重叠、冲突和优先级；
- Abstention：低置信度结果标记为 `[POSSIBLE_PII]`；
- Reversible placeholders：允许用户恢复误遮盖内容；
- Independent evaluation：比较 Presidio-only、GLiNER-only 和 Hybrid。

### 3.3 本项目不是什么

本项目当前**不是模型微调项目**。不更新 GLiNER 权重，不使用 2,000 条数据训练模型。

准确表述应为：

> SafePaste integrates Presidio-based pattern recognisers with a pretrained local GLiNER model. The project does not fine-tune model weights; the development set is used for label mapping, rule development and confidence-threshold calibration.

不要写：

> We fine-tuned GLiNER on 2,000 examples.

### 3.4 项目主要贡献

项目价值不在于发明新的 PII 模型，而在于：

- 本地隐私架构；
- 规则与预训练 NER 的合理组合；
- 明确的 abstention 和人工复核机制；
- 可逆遮盖；
- 不虚高 recall 的严谨评测；
- 对新加坡客服语言 domain gap 的独立检查。

### 3.5 PrivacyScrubber 的定位

PrivacyScrubber 是已有方案和 prior work，用来说明本项目不声称类别创新。除非后续代码确实 fork 或复用其源码，否则不要写成“SafePaste is built on PrivacyScrubber”。当前计划真正复用的是 Presidio 和 GLiNER。

## 4 当前项目状态

项目根目录：

```text
C:\Users\DELL\Desktop\safepaste
```

当前已有：

- 标准库实现的本地网页 MVP；
- Regex baseline；
- 可逆 placeholder；
- GLiNER adapter 骨架；
- Exact/overlap、typed/protective 评测函数；
- 30 条 Singapore-style stress records；
- AI4Privacy 数据准备脚本；
- 2,000 条 development set；
- 3,000 条 frozen evaluation set；
- 基础单元测试。

当前数据：

```text
data/
├── ai4privacy_split/
│   ├── development_2000.json
│   ├── frozen_evaluation_3000.json
│   └── manifest.json
└── singapore_stress.json
```

`manifest.json` 当前记录：

```json
{
  "dataset": "ai4privacy/pii-masking-300k",
  "seed": 6201,
  "development": 2000,
  "frozen_evaluation": 3000
}
```

因此，无需重新下载 AI4Privacy 数据。后续仍需完成数据审计、标签映射和 span 验证。

## 5 不可违反的实验纪律

1. `development_2000.json` 可用于标签映射、规则开发、阈值选择和故障排查。
2. `frozen_evaluation_3000.json` 只用于最终评测。
3. 一旦查看冻结集正式结果，不得再据此修改规则、标签映射、阈值或合并策略。
4. 30 条 Singapore-style stress set 必须单独报告，不能与 3,000 条主测试集合并。
5. 如果根据 stress set 修改系统，它就不再是独立测试集；因此应先冻结系统再运行 stress set。
6. `[POSSIBLE_PII]` 必须同时计入 protective 指标和 abstention rate，不得只展示提高后的 recall。
7. 所有系统必须使用相同数据、标签映射、span normalization 和评测程序。
8. 不得使用真实客户 PII；演示和报告示例必须来自合成或虚构文本。
9. 不得预先写“达到 80%”；80% 是目标，实际结果必须如实报告。

## 6 建议的最终仓库结构

```text
safepaste/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── configs/
│   ├── label_mapping.json
│   └── final_experiment.json
├── data/
│   ├── ai4privacy_split/
│   │   ├── development_2000.json
│   │   ├── frozen_evaluation_3000.json
│   │   └── manifest.json
│   └── singapore_stress.json
├── models/
│   └── README.md
├── scripts/
│   ├── prepare_ai4privacy.py
│   ├── audit_dataset.py
│   ├── build_label_mapping.py
│   ├── tune_thresholds.py
│   ├── run_experiment.py
│   ├── analyse_errors.py
│   └── export_report_tables.py
├── src/safepaste/
│   ├── types.py
│   ├── presidio_detector.py
│   ├── gliner_detector.py
│   ├── pipeline.py
│   ├── redaction.py
│   ├── evaluation.py
│   ├── cli.py
│   ├── server.py
│   └── static/index.html
├── tests/
├── artifacts/
│   ├── data_audit/
│   └── threshold_tuning/
├── results/
│   ├── runs/
│   ├── main_results.csv
│   ├── per_label_results.csv
│   ├── singapore_stress_results.csv
│   ├── error_categories.csv
│   └── runtime_summary.json
└── docs/
    ├── experiment_log.md
    ├── final_analysis_draft.md
    └── video_demo_script.md
```

### Git 管理要求

- 不提交大型模型权重；在 `.gitignore` 忽略 `models/*`，保留 `models/README.md`。
- 在 README 中写清楚模型下载步骤。
- 数据集是否能提交 GitHub 必须根据 AI4Privacy license 决定。若不适合提交，则忽略数据文件并保留生成脚本、manifest、hash 和说明。
- 不提交真实 PII、token、缓存、虚拟环境或恢复映射。

## 7 阶段一 下载并接通本地 GLiNER

### 目标

使 GLiNER-only 和 Hybrid 能在本机识别人名、地址等上下文 PII，并支持断网推理。

### 推荐模型

```text
urchade/gliner_multi_pii-v1
```

### 操作命令

```powershell
conda activate safepaste
cd C:\Users\DELL\Desktop\safepaste

python -c "from huggingface_hub import snapshot_download; print(snapshot_download(repo_id='urchade/gliner_multi_pii-v1', local_dir=r'C:\Users\DELL\Desktop\safepaste\models\gliner_multi_pii-v1'))"

$env:SAFEPASTE_GLINER_MODEL = "C:\Users\DELL\Desktop\safepaste\models\gliner_multi_pii-v1"
$env:PYTHONPATH = "src"
```

### 代码任务

- [ ] `GLiNERDetector` 只加载模型一次；
- [ ] 正式推理使用本地模型目录；
- [ ] 增加 `local_files_only=True`；
- [ ] 记录模型 repo、revision、模型文件 hash；
- [ ] 输出统一 `Span`；
- [ ] 增加 PERSON、ADDRESS 和低置信度 abstention 测试；
- [ ] 断网验证模型能运行。

### 验收标准

- `GLiNERDetector.available` 为 `True`；
- 示例人名和地址能产生候选 span；
- Hybrid 不再提示 GLiNER unavailable；
- 正式推理不访问 Hugging Face；
- 模型加载时间与逐条推理时间分开记录。

## 8 阶段二 正式接入 Presidio

### 目标

让报告中的 Regex-only baseline 真正由 Presidio recognizers 实现，与 milestone 的技术承诺一致。

### 推荐实现

创建 `src/safepaste/presidio_detector.py`：

- 使用 Presidio 内建 recognizers 处理 EMAIL、PHONE、CREDIT_CARD、IP_ADDRESS 等；
- 添加 Singapore recognizers：SG_NRIC、UNIT_NUMBER、POSTAL_CODE；
- 根据上下文约束六位邮编，降低把 order number 当邮编的风险；
- 将 Presidio entity names 映射为 SafePaste labels；
- 保存 detector source、recognizer name 和 score；
- 去除重复、包含和冲突 spans。

### 系统定义

- **Presidio-only**：只有 Presidio 结果；
- **GLiNER-only**：只有 GLiNER 结果；
- **Hybrid**：Presidio + GLiNER，经同一个 overlap resolver 合并。

报告可称 Presidio-only 为 regex/rule-based baseline，但必须说明其实际由 Presidio recognizers 实现。

### 验收标准

- Regex-only 输出 `source=presidio`；
- 新加坡电话号码、NRIC-shaped、unit number、邮编测试通过；
- 普通订单号负例不过度误报；
- 相同 span 不重复计分；
- Hybrid 明确包含两个 detector source。

## 9 阶段三 数据审计与标签映射

### 目标

将 AI4Privacy 的原始标签转换为三套系统共用的 SafePaste 标签空间，并证明 span 数据可用于评测。

### 只使用开发集完成以下工作

生成：

```text
artifacts/data_audit/development_label_counts.csv
artifacts/data_audit/development_label_examples.csv
artifacts/data_audit/invalid_spans.csv
artifacts/data_audit/unmapped_labels.csv
configs/label_mapping.json
```

### 审计内容

- 原始标签名和数量；
- 每类样例；
- `text[start:end]` 是否正确；
- 空 span、越界 span、重复 span；
- 同一文本中的重叠 gold spans；
- 每个原始标签纳入、合并或排除的理由。

### 建议统一标签

- PERSON；
- ADDRESS；
- EMAIL；
- PHONE；
- GOVERNMENT_ID；
- FINANCIAL；
- IP_ADDRESS；
- 其他由实际标签盘点决定的类型。

城市、国家、组织是否一律视为 PII，必须根据产品范围做出明确决定，不能在看到最终结果后改变。

### 验收标准

- 原始标签全部有映射或排除理由；
- `unmapped_labels.csv` 为零条；
- 无未处理的越界 span；
- 映射文件有版本号和生成日期；
- 三套系统使用完全相同的目标标签空间。

## 10 阶段四 在 2,000 条开发集上调阈值

### 目标

选择 GLiNER typed threshold 与 abstention threshold，并完成 Presidio 规则开发。此阶段允许迭代。

### 三段式预测规则

对于 GLiNER score `s`：

- `s >= typed_threshold`：输出明确类型；
- `abstain_threshold <= s < typed_threshold`：输出 `[POSSIBLE_PII]`；
- `s < abstain_threshold`：不输出。

### 建议阈值网格

```text
typed_threshold:    0.45, 0.50, 0.55, 0.60, 0.65, 0.70
abstain_threshold:  0.20, 0.25, 0.30, 0.35, 0.40
```

只运行满足 `abstain_threshold < typed_threshold` 的组合。

### 每组必须记录

- Exact typed recall；
- Exact protective recall；
- Overlap typed recall；
- Overlap protective recall；
- Typed precision；
- Protective precision；
- Abstention rate；
- 分标签指标；
- 平均与 P95 推理时间。

### 选择原则

不要选择 protective recall 最高但 abstention 极高的组合。建议：

1. 先保证 typed precision 和 over-redaction 可接受；
2. 在约束下提高 exact typed recall；
3. 检查 PERSON、ADDRESS 是否有明显短板；
4. 比较 protective recall 的增益和 abstention 成本；
5. 人工阅读开发集错误案例；
6. 写下最终阈值选择理由。

### 输出

```text
artifacts/threshold_tuning/threshold_sweep.csv
artifacts/threshold_tuning/per_label_thresholds.csv
artifacts/threshold_tuning/decision.md
configs/final_experiment.json
```

### 冻结点

当 `final_experiment.json` 确认后，冻结：

- label mapping；
- Presidio rules；
- typed threshold；
- abstention threshold；
- overlap resolution；
- model revision；
- metrics implementation。

之后才能开始 3,000 条正式实验。

## 11 阶段五 三系统冻结评测

### 目标

在 3,000 条 frozen evaluation records 上公平比较 Presidio-only、GLiNER-only 和 Hybrid。

### 批量实验接口

实现 `scripts/run_experiment.py`，预期用法：

```powershell
python scripts/run_experiment.py --dataset data/ai4privacy_split/frozen_evaluation_3000.json --system presidio --config configs/final_experiment.json --output results/runs/presidio_frozen

python scripts/run_experiment.py --dataset data/ai4privacy_split/frozen_evaluation_3000.json --system gliner --config configs/final_experiment.json --output results/runs/gliner_frozen

python scripts/run_experiment.py --dataset data/ai4privacy_split/frozen_evaluation_3000.json --system hybrid --config configs/final_experiment.json --output results/runs/hybrid_frozen
```

### 运行协议

1. 先用 10 条记录做 smoke test，只验证程序能否运行；不得用结果调参。
2. 保存完整 config 副本。
3. 保存逐条 prediction，避免为复算指标而重复推理。
4. 记录异常和失败记录，不可静默跳过。
5. 记录处理数量、gold spans 数、predicted spans 数和耗时。
6. 三套系统全部完成后再汇总表格。
7. 无论是否达到 80%，不再修改系统。

### 每次运行目录

```text
results/runs/<timestamp>_<system>/
├── config.json
├── predictions.jsonl
├── metrics.json
├── errors.jsonl
├── runtime.json
└── run.log
```

### 每条 prediction 至少包含

```json
{
  "record_id": "...",
  "gold_spans": [],
  "predicted_spans": [],
  "system": "hybrid",
  "runtime_ms": 0,
  "warnings": []
}
```

如许可不允许重新分发原始文本，GitHub 版本的 predictions 不应包含完整 `text`，可只保留 record ID、span 坐标和标签。

## 12 阶段六 30 条手写新加坡压力测试

### 老师要求的真实含义

“Hand-write 30 examples of real support text”是指手工设计 30 条**真实风格但完全虚构**的客服文本，不是使用真实客户聊天记录。

应覆盖：

- NRIC-shaped strings；
- Singlish；
- `Blk`、`Ave`、`St`、`#12-34` 等本地地址形式；
- 电话、email、人名和地址混合；
- 拼写错误、缺标点、客服缩写；
- 多个相邻 PII；
- 容易误报的数字负例。

### 当前状态

`data/singapore_stress.json` 已有 30 条草稿及 span 标注，但提交前必须由学生本人逐条阅读、修改和确认，以便诚实说明这是 hand-authored and manually reviewed stress set。

### 实验规则

- 在系统和阈值冻结后运行；
- 三套系统分别运行；
- 单独生成结果表；
- 不与 3,000 条 AI4Privacy 结果合并；
- 表现下降可作为 domain gap 发现，不是项目失败。

## 13 指标定义

### 13.1 Exact-span recall

预测 `start` 和 `end` 必须与 gold 完全一致。

### 13.2 Overlap recall

预测 span 与 gold span 只要存在字符交集，就算发现该 gold entity。

### 13.3 Typed recall

只计算明确类型的预测，不包含 `[POSSIBLE_PII]`。

### 13.4 Protective recall

明确类型和 `[POSSIBLE_PII]` 都算作遮盖成功，用于反映保守隐私保护能力。

### 13.5 Precision

反映预测 span 中有多少对应真实 PII，防止过度遮盖。

### 13.6 Abstention rate

```text
abstained predicted spans / all predicted spans
```

### 13.7 One-to-one matching

一个 gold span 最多匹配一个 prediction，一个 prediction 最多匹配一个 gold span。不得用多个重复预测反复计中同一个 gold span。

### 主结果表

| System | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Typed P | Protective P | Abstention |
|---|---:|---:|---:|---:|---:|---:|---:|
| Presidio-only | TBD | TBD | TBD | TBD | TBD | TBD | N/A or 0 |
| GLiNER-only | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Hybrid | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

还应增加 per-label 表和 AI4Privacy vs Singapore stress set 对照表。

## 14 错误分析设计

实现 `scripts/analyse_errors.py`，将错误分为：

1. 完全漏检；
2. 边界过短；
3. 边界过长；
4. 正确范围但类型错误；
5. 正确范围但被标为 `[POSSIBLE_PII]`；
6. 非 PII 被遮盖；
7. Presidio 与 GLiNER 冲突；
8. 一个实体被拆成多个预测；
9. 多个实体被错误合并。

### 分类型分析

至少报告 PERSON、ADDRESS、EMAIL、PHONE、GOVERNMENT_ID、FINANCIAL 及最终范围内其他类型。

### 代表案例

选择少量能够解释系统差异的案例：

- Presidio 成功、GLiNER 失败；
- GLiNER 成功、Presidio 失败；
- Hybrid 正确合并；
- exact miss 但 overlap hit；
- abstention 成功保护；
- over-redaction 损害文本可用性；
- 本地地址或 Singlish 导致 domain gap。

只使用合成或虚构案例。

## 15 实验日志设计

创建 `docs/experiment_log.md`。每次具有决策意义的实验使用以下模板：

```markdown
## EXP-XXX 实验标题

- Date:
- Objective:
- Dataset:
- System:
- Configuration:
- Code version:
- Expected outcome:
- Actual result:
- Interpretation:
- Decision:
- Next action:
```

### 必须记录的实验

- 数据标签盘点；
- span 质量审计；
- Presidio recognizer 测试；
- GLiNER 单条和批量 smoke test；
- 阈值 sweep；
- overlap resolver 决策；
- final config freeze；
- 三次 frozen system runs；
- 三次 Singapore stress runs；
- error analysis；
- runtime analysis。

不要只记录成功实验。失败、异常和规则取舍也是 business and technical trade-off analysis 的证据。

## 16 不超过 1,200 词的最终分析建议结构

最终英文正文需要同时覆盖 problem statement 与 business/technical trade-offs。建议约 1,050–1,150 词，留出编辑余量。

### 1 Problem and significance 约 120 词

- 用户 Tonya；
- 向公共 AI 助手粘贴客服文本的 PII 风险；
- 项目范围和非目标。

### 2 Proposed solution 约 150 词

- 本地 Presidio + GLiNER；
- review、reversible placeholders、abstention；
- 不声称类别创新，提及 PrivacyScrubber。

### 3 Business and technical trade-offs 约 300 词

- Local vs cloud：隐私、延迟、设备成本、模型维护；
- Rules vs NER：确定性与上下文能力；
- Build vs buy/reuse：自建 orchestration/UI/evaluation，复用 Presidio/GLiNER；
- No RAG/agent：没有检索或工具调用需求；
- `$0 per API call` 应准确写为“no external per-call API fee”，不能写成总成本为零。

### 4 Data and evaluation 约 220 词

- AI4Privacy synthetic dataset；
- 2,000 development / 3,000 frozen evaluation；
- 30 条独立 Singapore stress set；
- 三系统公平比较；
- exact/overlap、typed/protective、precision、abstention。

### 5 Results and interpretation 约 200 词

- 填入真实结果；
- Hybrid 是否优于 baseline；
- 80% 目标是否达到；
- abstention 带来的收益与代价；
- AI4Privacy 与本地 stress set 差异。

### 6 Risks limitations and responsible use 约 150 词

- silent failure；
- over-redaction；
- synthetic-to-real domain gap；
- English only；
- 不检测 trade secrets；
- 不做法律合规判断；
- 不替代 enterprise DLP；
- restore map 本身包含敏感信息。

### 报告写作纪律

- 不虚构结果；
- 不把 development set 称为 training set；
- 不称为 fine-tuning；
- 不只展示最有利的指标；
- 所有表格标明 `n`；
- 主测试和 stress test 分表；
- 明确区分 target 与 achieved result。

## 17 GitHub README 必须包含

1. 项目目标和截图；
2. 架构说明；
3. 为什么使用 Presidio + GLiNER；
4. 安装步骤；
5. 模型权重下载步骤；
6. 本地运行命令；
7. CLI 示例；
8. 三系统实验命令；
9. 数据来源和 license 注意事项；
10. 结果表；
11. 隐私和安全说明；
12. 已知限制；
13. 项目目录结构；
14. 测试命令。

README 不应承诺“生产级”“完全阻止泄漏”或“保证合规”。

## 18 录屏演示建议

建议时长 5–7 分钟，具体以课程要求为准。

### 演示结构

1. **问题与用户**：Tonya 即将把客服文本粘贴到公共 AI 助手；
2. **架构**：Presidio 处理结构化 PII，GLiNER 处理上下文 PII；
3. **现场 demo**：输入含姓名、地址、NRIC-shaped、电话和 email 的虚构消息；
4. **结果复核**：展示 typed span、`[POSSIBLE_PII]`、side-by-side text；
5. **恢复误报**：展示 reversible placeholder；
6. **复制 sanitised text**；
7. **实验结果**：展示三系统主表和 30 条 stress set；
8. **trade-offs 与限制**：强调本地运行、domain gap、不是 DLP；
9. **结论**：是否达到目标以及下一步改进。

### 演示数据

只使用虚构示例，不使用真实姓名、地址、NRIC、电话或客户工单。

### 录制前检查

- [ ] 断开不必要通知；
- [ ] 浏览器只打开本地页面；
- [ ] 模型提前加载；
- [ ] 演示输入提前核对；
- [ ] 结果表可读；
- [ ] GitHub repository 可访问；
- [ ] 声音和画面测试完成；
- [ ] 不在画面中显示 HF token、路径中的敏感信息或真实 PII。

## 19 自动测试要求

至少覆盖：

- Presidio 每种结构化 PII；
- 新加坡电话、NRIC-shaped、unit、postal code；
- GLiNER typed 和 abstained spans；
- Hybrid overlap resolution；
- reversible redaction round trip；
- exact matching；
- overlap matching；
- one-to-one matching；
- typed vs protective 指标；
- 空预测、空 gold、多预测同一 gold；
- dataset mapping；
- 30 条 stress set span validity；
- server API 基础流程。

提交前必须运行完整测试，并在 README 记录命令。

## 20 PyCharm Codex 的执行顺序

PyCharm Codex 应按照以下顺序执行，不要一次性重写整个项目：

### Phase A 环境和现状审计

- [ ] 检查 Git 状态和现有文件；
- [ ] 运行当前测试；
- [ ] 检查 Conda 环境、Python、GLiNER、Presidio；
- [ ] 验证数据文件和记录数；
- [ ] 计算数据文件 hash；
- [ ] 建立实验日志。

### Phase B 检测器完善

- [ ] 接通本地 GLiNER；
- [ ] 实现 PresidioDetector；
- [ ] 统一 labels 和 Span schema；
- [ ] 完善 overlap resolver；
- [ ] 增加测试。

### Phase C 数据与调参

- [ ] 数据审计；
- [ ] 标签映射；
- [ ] 开发集 threshold sweep；
- [ ] 人工错误阅读；
- [ ] 冻结 final config。

### Phase D 正式实验

- [ ] 三系统 smoke test；
- [ ] 三系统 frozen runs；
- [ ] 三系统 stress runs；
- [ ] 汇总指标；
- [ ] 错误分析；
- [ ] 生成图表和表格。

### Phase E 最终提交

- [ ] 完善 GitHub README；
- [ ] 清理 secrets、缓存和模型文件；
- [ ] 完成 ≤1,200 词英文分析；
- [ ] 编写视频脚本；
- [ ] 录屏并检查；
- [ ] 核对 LMS 提交项目。

## 21 最终完成定义

只有满足以下条件，项目才可视为完成：

- [ ] GLiNER 本地加载并可离线推理；
- [ ] Presidio 实际参与 Presidio-only 和 Hybrid；
- [ ] AI4Privacy 标签映射完整；
- [ ] 阈值只使用开发集确定；
- [ ] 配置在冻结评测前锁定；
- [ ] 三系统完成 3,000 条评测；
- [ ] 30 条 stress set 独立报告；
- [ ] exact/overlap 与 typed/protective 同时报告；
- [ ] precision 和 abstention 可见；
- [ ] 完成 per-label 和 error analysis；
- [ ] GitHub 仓库可由他人按 README 运行；
- [ ] 完成不超过 1,200 词的分析；
- [ ] 完成视频 presentation/demo；
- [ ] 所有结论与真实实验结果一致。

## 22 给 PyCharm Codex 的首条任务指令

可将以下内容直接发给 PyCharm Codex：

```text
请完整阅读仓库根目录的 SAFEPaste_PROJECT_EXECUTION_PLAN_ZH.md 和 README.md，然后检查现有源码、测试、数据文件与 Git 状态。不要立即运行冻结评测集，也不要重写整个项目。

先完成 Phase A：
1. 给出现状审计；
2. 验证 development_2000.json、frozen_evaluation_3000.json 和 singapore_stress.json 的记录数与 span 基本合法性；
3. 为数据文件生成 SHA-256 manifest；
4. 创建 docs/experiment_log.md；
5. 运行现有测试并报告结果；
6. 列出进入 Phase B 前的具体风险。

在我确认 Phase A 后，再开始接通本地 GLiNER 和实现 PresidioDetector。务必保护冻结集，不得用 frozen_evaluation_3000.json 调参。
```

