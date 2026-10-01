> **核心原则：** 2,000 条 development set 可以用于标签映射、规则修改和阈值选择；3,000 条 frozen evaluation set 一旦开始正式评测，就不能再用于调参。30 条 Singapore-style stress set 必须单独报告，不与主测试集合并。
> 

<aside>
📌

**当前项目状态**

- 项目目录：`C:\Users\DELL\Desktop\safepaste`
- 已生成：`development_2000.json`、`frozen_evaluation_3000.json`、`singapore_stress.json`
- 固定随机种子：`6201`
- `gliner`、`presidio-analyzer`、`datasets`、`torch` 已安装
- 目前真正可运行的是 Regex baseline；GLiNER 权重和 Presidio 实际调用仍需接通
</aside>

# 一 整体实施顺序

1. 下载并验证本地 GLiNER 权重。
2. 让 Presidio 成为 Regex-only 系统的正式检测引擎。
3. 将 AI4Privacy 原始标签映射为 SafePaste 的统一标签。
4. 只在 2,000 条开发集上选择 Regex 规则和 GLiNER 阈值。
5. 冻结配置后，在 3,000 条评测集上一次性运行三套系统。
6. 生成总体指标、分类别指标、30 条压力测试结果和错误分析。

建议保存一份冻结配置，例如 `configs/final_experiment.json`，包含模型名称、模型版本、阈值、标签映射版本、Regex 版本、数据 seed 和 Git commit。

---

# 二 下载并接通本地 GLiNER 模型

## 目标

让 GLiNER-only 和 Hybrid 系统能在本机识别人名、地址等上下文 PII；正式推理过程中不向云端发送用户文本。

## 推荐模型

使用针对 PII 微调的 `urchade/gliner_multi_pii-v1`。模型文件约 1.16 GB。模型页面：https://huggingface.co/urchade/gliner_multi_pii-v1

## 操作步骤

- [ ]  激活项目 Conda 环境。
- [ ]  将模型权重下载到项目的 `models` 目录。
- [ ]  设置 `SAFEPASTE_GLINER_MODEL` 环境变量。
- [ ]  运行单条文本检测。
- [ ]  断网后再次检测，确认模型和 tokenizer 都能从本地加载。

```powershell
conda activate safepaste
cd C:\Users\DELL\Desktop\safepaste

python -c "from huggingface_hub import snapshot_download; print(snapshot_download(repo_id='urchade/gliner_multi_pii-v1', local_dir=r'C:\Users\DELL\Desktop\safepaste\models\gliner_multi_pii-v1'))"

$env:SAFEPASTE_GLINER_MODEL = "C:\Users\DELL\Desktop\safepaste\models\gliner_multi_pii-v1"
$env:PYTHONPATH = "src"

python -c "from safepaste.gliner_detector import GLiNERDetector; d=GLiNERDetector(); print(d.available); print(d.detect('Customer Mei Tan stays at Blk 123 Ang Mo Kio Ave 3.'))"
```

## 代码要求

在 `gliner_detector.py` 中：

- 模型只在第一次调用时加载，避免每条记录重复加载。
- 模型路径必须是本地目录。
- 正式实验中使用 `local_files_only=True`。
- 记录模型名称、模型文件版本或 Hugging Face revision。
- 输出统一的 `start`、`end`、`label`、`score`、`source` 和 `abstained`。

## 验收标准

- [ ]  `available` 输出 `True`。
- [ ]  能识别示例中的 `Mei Tan` 和地址候选。
- [ ]  断网后仍可运行。
- [ ]  Hybrid 结果中的 `engines_used` 同时出现 `presidio` 和 `gliner`。
- [ ]  网页没有“GLiNER unavailable”提示。

## 常见问题

- 第一次加载慢是正常的，模型初始化不应计入逐条推理延迟。
- 如果本地目录有权重但 tokenizer 仍联网，先在线完整加载一次，再启用 `local_files_only=True` 验证。
- `.env.py` 不会被当前代码自动读取。当前终端应使用 PowerShell 的 `$env:SAFEPASTE_GLINER_MODEL=...`。

---

# 三 正式接入 Presidio

## 目标

让 Regex-only 系统真正通过 Presidio 的 recognizer registry 运行，而不是只使用项目自写的 RegexDetector，从而与 milestone 中“reusing Presidio”的表述一致。

## 推荐设计

建立 `PresidioDetector`：

- 使用 Presidio 内建 recognizers 处理 email、phone、credit card、IP 等类型。
- 添加自定义 `PatternRecognizer` 处理 Singapore NRIC、unit number 和 local postal code。
- 将 Presidio 的实体名称转换为 SafePaste 统一标签。
- 保留 recognizer name 和 score，便于错误分析。

## 新加坡规则建议

- `SG_NRIC`：先检测 shaped identifier；是否进行 checksum 验证必须在报告中说明。
- `UNIT_NUMBER`：例如 `#12-34`。
- `POSTAL_CODE`：六位数字必须结合 `Singapore` 或地址上下文，避免把普通订单号当邮编。
- 电话号码应覆盖 `+65 9123 4567`、`91234567`、`9123-4567`。

## 实现步骤

- [ ]  新建 `src/safepaste/presidio_detector.py`。
- [ ]  创建 Presidio registry。
- [ ]  加载需要的内建 recognizers。
- [ ]  注册新加坡自定义 recognizers。
- [ ]  将 Presidio result 转换成项目的 `Span`。
- [ ]  Pipeline 的 Regex-only 模式改为调用 `PresidioDetector`。
- [ ]  保留现有 RegexDetector 作为故障排查或对照实现，不要同时重复计分。
- [ ]  为每类结构化 PII 增加单元测试。

## 验收标准

- [ ]  Regex-only 输出的 `source` 是 `presidio`。
- [ ]  Email、电话、NRIC-shaped、邮编和 unit number 测试通过。
- [ ]  普通八位订单号不会被轻易判为电话号码。
- [ ]  相同字符范围不会因为多个 recognizer 重复输出而重复计分。
- [ ]  README 准确说明复用了 Presidio，而不是声称自研完整 PII 引擎。

Presidio 自定义 recognizer 文档：https://github.com/data-privacy-stack/presidio/blob/main/docs/analyzer/adding_recognizers.md

---

# 四 建立 AI4Privacy 标签映射

## 目标

把 AI4Privacy 的细粒度标签转换成三个系统都能输出、也能公平评测的 SafePaste 标签空间。

## 第一步 盘点标签

只读取 2,000 条开发集，统计：

- 原始标签名称；
- 每个标签的 span 数量；
- 每个标签的样本文本；
- 是否属于当前项目范围。

建议生成：

- `artifacts/development_label_counts.csv`
- `configs/label_mapping.json`
- `artifacts/unmapped_labels.csv`

## 映射原则

| SafePaste 标签 | 可能合并的原始类型 | 主要检测方式 |
| --- | --- | --- |
| PERSON | name、first name、last name、customer name | GLiNER |
| ADDRESS | street address、building、city、postal address | GLiNER + Presidio 局部规则 |
| EMAIL | email | Presidio |
| PHONE | phone、mobile number | Presidio |
| GOVERNMENT_ID | national ID、passport、SSN 等 | Presidio；新加坡样本单列 SG_NRIC |
| FINANCIAL | credit card、bank account、IBAN | Presidio |

最终映射必须由数据中实际出现的标签决定，不能仅凭上述示例直接假设。

## 边界检查

- [ ]  确认数据采用半开区间 `[start, end)`。
- [ ]  验证 `text[start:end]` 是否等于标注值。
- [ ]  记录坏 span、空 span、越界 span 和重复 span。
- [ ]  明确是否将城市、国家、组织名称视为 PII。
- [ ]  不在范围内的标签应记为 `EXCLUDED`，不可静默丢弃。

## 验收标准

- [ ]  开发集每个原始标签都有明确映射或明确排除理由。
- [ ]  未映射标签数量为 0。
- [ ]  映射规则存入版本化 JSON。
- [ ]  三个系统输出同一个标签空间。
- [ ]  报告中列出范围内和范围外的类型。

---

# 五 在 2,000 条开发集上调阈值

## 目标

使用 development set 选择 GLiNER typed threshold 和 abstention threshold，并完成 Regex/Presidio 规则开发；不能查看 frozen set 的结果来反向修改配置。

## 三段式决策

假设 GLiNER score 为 `s`：

- `s >= typed_threshold`：输出明确标签，如 `PERSON`。
- `abstain_threshold <= s < typed_threshold`：遮盖为 `POSSIBLE_PII`。
- `s < abstain_threshold`：不输出。

## 推荐搜索范围

- `typed_threshold`：0.45、0.50、0.55、0.60、0.65、0.70。
- `abstain_threshold`：0.20、0.25、0.30、0.35、0.40。
- 必须满足 `abstain_threshold < typed_threshold`。

## 每组阈值记录

- exact typed recall；
- exact protective recall；
- overlap typed recall；
- overlap protective recall；
- typed precision；
- protective precision；
- abstention rate；
- 分类型 recall；
- 推理时间。

## 选择规则

不要简单选择 protective recall 最高的组合，否则大量 `POSSIBLE_PII` 会人为提高结果。建议按以下顺序决策：

1. 首先满足可接受的 typed precision，控制过度遮盖。
2. 在此约束下提高 exact typed recall。
3. 检查 protective recall 的增益是否值得对应的 abstention rate。
4. 检查 PERSON 和 ADDRESS 是否存在明显短板。
5. 人工阅读一小批 false positive 和 false negative。

## 必须保存

- [ ]  每组阈值的完整结果 CSV。
- [ ]  最终选择的阈值。
- [ ]  选择理由。
- [ ]  调参日期和代码版本。
- [ ]  最终冻结配置 `configs/final_experiment.json`。

## 验收标准

- [ ]  阈值选择完全基于 2,000 条开发集。
- [ ]  能解释为什么选该阈值，而不仅是“数字最高”。
- [ ]  `POSSIBLE_PII` 的比例可见。
- [ ]  冻结配置后，不再修改 Regex、标签映射或阈值。

---

# 六 在 3,000 条冻结集上运行三系统实验

## 目标

在完全相同的数据、标签映射和评测程序上比较：

1. Presidio-only，也就是报告中的 Regex-only baseline；
2. GLiNER-only；
3. Hybrid：Presidio + GLiNER。

## 实验公平性

三套系统必须共用：

- 相同 3,000 条记录；
- 相同 label mapping；
- 相同 span normalization；
- 相同评测脚本；
- 相同 one-to-one matching；
- 相同机器和运行记录方式。

GLiNER-only 不得包含 Presidio 结果；Presidio-only 不得包含 GLiNER 结果。Hybrid 使用冻结的 overlap resolution 策略。

## 建议命令

项目需要增加批量实验脚本，例如：

```powershell
python scripts/run_experiment.py --dataset data/ai4privacy_split/frozen_evaluation_3000.json --system presidio --config configs/final_experiment.json --output results/presidio_frozen.json

python scripts/run_experiment.py --dataset data/ai4privacy_split/frozen_evaluation_3000.json --system gliner --config configs/final_experiment.json --output results/gliner_frozen.json

python scripts/run_experiment.py --dataset data/ai4privacy_split/frozen_evaluation_3000.json --system hybrid --config configs/final_experiment.json --output results/hybrid_frozen.json
```

## 运行要求

- [ ]  先做 10 条 smoke test，只检查程序是否能运行，不据此调参。
- [ ]  正式运行时保存 stdout、异常、耗时和配置。
- [ ]  预测结果要落盘，以便复算指标而无需重复模型推理。
- [ ]  给每个预测保存 detector source。
- [ ]  不因结果未达到 80% 而修改 frozen set 或回到开发集继续“追分”。
- [ ]  三系统完成后，再对 30 条 stress set 分别运行并单独成表。

## 验收标准

- [ ]  三套系统都完成 3,000 条记录。
- [ ]  每套系统的处理记录数和 gold span 数一致。
- [ ]  结果可由保存的 predictions 重新计算。
- [ ]  报告明确说明 80% 是目标；实际未达到时如实解释。
- [ ]  Stress set 结果没有与 AI4Privacy 结果合并。

---

# 七 输出完整指标和错误分析

## 主结果表

每个系统至少报告：

- Exact typed recall；
- Exact protective recall；
- Overlap typed recall；
- Overlap protective recall；
- Typed precision；
- Protective precision；
- Abstention rate；
- 样本数和 gold span 数。

| System | Exact typed R | Exact protective R | Overlap typed R | Overlap protective R | Typed P | Abstention |
| --- | --- | --- | --- | --- | --- | --- |
| Presidio-only | TBD | TBD | TBD | TBD | TBD | 0 或不适用 |
| GLiNER-only | TBD | TBD | TBD | TBD | TBD | TBD |
| Hybrid | TBD | TBD | TBD | TBD | TBD | TBD |

## 为什么同时报告 exact 和 overlap

Exact-span 把边界多一个或少一个字符算作失败，适合衡量 span 质量；overlap 只要覆盖到 gold PII 就算发现，适合衡量“敏感信息是否至少被拦截”。两者必须并列，不能用 overlap 替代 exact。

## 为什么同时报告 typed 和 protective

Typed 指标只统计明确类型的预测；protective 指标包括 `POSSIBLE_PII`。如果只展示 protective recall，系统可以通过大量 abstention 获得虚高 recall，因此必须同时展示 abstention rate。

## 错误分类

每个系统分别统计：

- 完全漏检；
- 边界偏左或偏右；
- 标签错误；
- 正确范围但被标为 `POSSIBLE_PII`；
- 普通文本被误遮盖；
- Presidio 与 GLiNER 的重叠冲突；
- 多个相邻 PII 被合并；
- 一个完整 PII 被拆成多个预测。

## 分类型分析

至少单独报告：

- PERSON；
- ADDRESS；
- EMAIL；
- PHONE；
- GOVERNMENT_ID；
- FINANCIAL；
- 其他最终纳入范围的类型。

## 案例分析

选择少量代表案例：

- Presidio 成功、GLiNER 失败；
- GLiNER 成功、Presidio 失败；
- Hybrid 正确合并；
- exact 失败但 overlap 成功；
- `POSSIBLE_PII` 成功保护；
- over-redaction 影响文本可用性。

案例只能来自合成数据或 30 条虚构压力测试，不展示真实客户 PII。

## 最终交付文件

- [ ]  `results/main_results.csv`
- [ ]  `results/per_label_results.csv`
- [ ]  `results/singapore_stress_results.csv`
- [ ]  `results/error_categories.csv`
- [ ]  `results/representative_errors.json`
- [ ]  `results/runtime_summary.json`
- [ ]  一张三系统主结果表；
- [ ]  一张 typed 与 protective 差异表；
- [ ]  一段对 80% 目标是否实现的诚实结论。

---

# 八 最终完成定义

当且仅当以下条件全部满足，才能称为完成 milestone 承诺的项目：

- [ ]  GLiNER 模型本地加载并能离线推理。
- [ ]  Presidio 实际参与 Regex-only 和 Hybrid。
- [ ]  AI4Privacy 标签映射完整且有版本记录。
- [ ]  阈值只使用 2,000 条开发集选择。
- [ ]  3,000 条冻结集完成三系统比较。
- [ ]  30 条本地化压力测试独立报告。
- [ ]  Exact/overlap 和 typed/protective 同时报告。
- [ ]  Precision 与 abstention rate 可见。
- [ ]  有分类型结果和人工错误分析。
- [ ]  报告明确说明限制：synthetic data、English only、不处理 trade secrets、不替代 enterprise DLP。

# 九 推荐执行清单

- [ ]  先完成本地 GLiNER 下载和单条验证。
- [ ]  编写并测试 PresidioDetector。
- [ ]  编写标签盘点和映射脚本。
- [ ]  编写 development threshold sweep。
- [ ]  人工确认最终配置并冻结。
- [ ]  编写可恢复的批量实验脚本。
- [ ]  运行三套 frozen experiments。
- [ ]  运行独立 stress set。
- [ ]  自动生成表格和错误样本。
- [ ]  根据真实结果撰写最终报告，不预先假定达到 80%。