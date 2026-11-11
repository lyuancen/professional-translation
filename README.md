# professional-translation

供 Codex 使用的中英专业翻译 Skill。适用于商用车与汽车工程、国际商务和贸易、合同法律文件、公司治理及上市公司材料。默认中译英，也可英译中或审校既有译文。无需独立 API Key、数据库或后台服务；检索脚本只依赖 Python 3 标准库。

## 项目文件

```text
professional-translation/
├── SKILL.md                     Codex 的翻译和复核规则
├── glossary/English 0928.docx   唯一人工维护的共享术语主文件
├── scripts/glossary.py          DOCX 解析、哈希检查、临时索引和检索
├── scripts/check_share.py       提交前检查暂存文件名单
├── references/source-guidance.md 需要外部核查时的来源选择
├── agents/openai.yaml           Skill 显示信息
├── README.md
└── .gitignore                   仅允许上述共享文件被普通 git add 暂存
```

Word 中的项目标题、原始段落、括号注释和词条位置会一同出现在检索结果中。脚本提供**候选段落**，不自动断言斜杠两侧是同义词，也不自动决定译法。遇到粘连等复杂段落，必须查看 Word 原文和上下文。

## 安装与更新

GitHub 仓库地址：<https://github.com/lyuancen/professional-translation>。整个仓库即一个 Skill，Word 会随 Skill 一起下载。需要 Python 3。Private 仓库的同事须先获得访问权限，并在本机完成 GitHub 登录或 SSH 配置。

**最简单的 Codex 安装方式：**在 Codex 中发送以下消息。仓库根目录就是 Skill 目录；`$skill-installer` 需要指定根路径 `.` 和名称 `professional-translation`。

> 使用 `$skill-installer` 从 `https://github.com/lyuancen/professional-translation` 安装仓库根目录的 Skill（路径 `.`，名称 `professional-translation`）。

安装器会把 Skill 复制到个人技能目录；若该目录已存在同名 Skill，安装器会停止并提示，不会覆盖。通过安装器获取的下载版未必保留 Git 元数据，后续更新可让 Codex 协助移除旧安装并重新安装。若计划长期直接编辑共享 Word 或通过 `git pull` 更新，推荐以下 Git 克隆方式。需先安装 Git。

**macOS（终端）：**

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/lyuancen/professional-translation.git ~/.agents/skills/professional-translation
python3 ~/.agents/skills/professional-translation/scripts/glossary.py status
```

**Windows（PowerShell）：**

```powershell
New-Item -ItemType Directory -Force "$HOME/.agents/skills" | Out-Null
git clone https://github.com/lyuancen/professional-translation.git "$HOME/.agents/skills/professional-translation"
py -3 "$HOME/.agents/skills/professional-translation/scripts/glossary.py" status
```

启动一个新的 Codex 会话后即可调用 `$professional-translation`。Codex 的技能目录与安装方式可参考 [OpenAI 的技能安装示例](https://developers.openai.com/api/reference/cli)；如所在组织使用不同的 Skill 目录，将**整个** `professional-translation` 文件夹放到该目录，保持其内部结构。

使用 Git 克隆方式安装后，更新时在该文件夹运行 `git pull --ff-only`（Windows/macOS 均适用），或让 Codex 帮你更新此本地仓库；下一次翻译会自动检查新版 Word 并重建索引。若自己本地 Word 有未提交修改，应先处理这些修改，避免 `git pull` 冲突。

## 日常使用

- **专业翻译：**“使用 `$professional-translation`，将以下中文技术规格译成英文：……” 默认只输出可直接使用的译文；有重大歧义时会简要说明。
- **专业审校：**“使用 `$professional-translation` 的 Review 模式。原文：…… 现有译文：……” 输出问题及完整修订译文；准确的部分会保留。
- **术语核查：**“使用 `$professional-translation` 的 Terminology Check 模式，比较‘型式批准’与‘型式认证’在这份合同中的译法。” 此模式可附 Word 原记录和必要的权威来源链接。

对 DOCX 等文件，直接交给 Codex 并说明输出位置。生成文件应保存在用户指定目录或仓库外；本仓库只用于 Skill 和术语主文件。外部网页检索仅使用必要的非敏感术语；Codex 处理任务材料时仍可能涉及其运行环境或远程模型服务，应按所在组织的数据要求使用。

## 词库版本与本地更新

术语主文件是本仓库中的 `glossary/English 0928.docx`。本项目创建时从现有 Word **复制一次**；以后请直接编辑仓库里的这份 Word，避免维护两份。旧位置的原文件不会自动同步到仓库。

保存 Word 后，无需编辑 Skill 或手动更新索引。下次调用 Skill 会计算 DOCX 的 SHA-256：内容变化则重新解析，未变化则复用外部临时索引。新增、修改、删除都会随之生效。查看当前使用的版本：

```bash
python3 scripts/glossary.py status
```

Windows 用 `py -3` 代替 `python3`。输出中的 `sha256` 是**当前 Word 的内容版本**，`index_refreshed` 表示本次是否重建。也可用 `python3 scripts/glossary.py search --query '整备质量' --query '预付款'` 检索；`show --id 727 --neighbors 2` 查看相邻段落。索引位于系统临时目录，不上传到 GitHub，也不是另一份人工维护的词库。临时目录清空后会自动重建。

如果 Word 缺失、无法读取或索引写入失败，脚本明确报错并返回非零状态，**不会**静默使用旧索引。检查仓库中是否有 `glossary/English 0928.docx`、Word 是否已保存且不是损坏文件、系统临时目录是否可写；必要时重新 `git pull` 或从仓库恢复主文件。不要用旧缓存替代缺失的主文件。

## 发布新版到 GitHub（仅由维护者手动进行）

本地保存 Word 只更新本机内容和下次使用的索引，**不会**发布给同事。决定发布时，先亲自审阅 Word 中是否有不宜共享的信息，并决定 Public 或 Private 仓库。然后在仓库目录执行：

```bash
git status --short
git add .
python3 scripts/check_share.py
git diff --cached --name-only
git commit -m "Update shared glossary"
git push
```

`check_share.py` 只核对暂存路径是否属于项目允许共享的文件；**不会**审查 Word 内部是否有敏感内容，也无法防止有人强制暂存文件。首次发布需由维护者设置 GitHub 远程地址。若选 Private，只有获授权的同事可以克隆和更新。使用 Git 克隆方式的同事 `git pull --ff-only` 后，在下次翻译时自动使用新的 Word 内容和索引。

## 数据边界

`.gitignore` 采用共享文件白名单。普通 `git add .` 不会纳入合同、董事会资料、译文、缓存、日志或个人配置；日常翻译材料也不会被脚本写进本仓库。仍请在提交前运行检查并亲自审阅 Word。脚本不发送网络请求，外部专业来源核查由 Codex 根据任务需要进行；无法联网时会区分已核查和未核查的表达。
