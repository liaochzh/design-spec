#!/usr/bin/env python3
"""设计规范一致性校验（八组断言）—— 防副本回流、锚指向不存在的版本、摘要漂移、闸门清单回流。

权威源
------
`design-spec/references/ui-design-philosophy.md`：§俗套校准表（`### Web` / `### App`）、§交付闸门、§维护说明 · 变更日志。

八组断言
--------
1. `cliche`  俗套表副本：扫描面内 markdown 表格，**表头三列同构** 且 **数据行 ≥3** 且
   **首列整格命中 Web 权威名 ≥2** ⇒ 违规。匹配只看表格首列整格，散文串不参与。
2. `anchors` 版本锚：只认 `- 版本：` 开头的行，行内取 `（配套 vX.Y.Z）` 或 `vX.Y.Z 配套`
   两种词序；**锚版本必须存在于变更日志**，否则违规。
   天花板：只拦「锚写了不存在的版本」；**拦不到「应 bump 未 bump」**（季审人工判定），
   也**不判**「载体自身版本号分叉 / 载体格式漂移」——那是 `versions` 的职责。
3. `summary` 摘要集合：含「消费哲学层」+「俗套校准表」的块（标题行 + 紧随内容行），
   按平台标记（`· App` / `· Web`）比对对应权威表：条目名集合与禁用集合须相等。
   `skills/app-design/SKILL.md` 必须存在摘要块（删除摘要 = 须同轮改本断言）。
4. `gates`    交付闸门副本：权威源 §交付闸门 ›「### Web 淘汰闸门」（11 项）与「### App 原型记录项」
   （5 条）是唯一出处。判据 A：**单行**命中 Web 条目名 ≥3 ⇒ 违规（单行斜杠/编号串的副本形态）；
   判据 B：**连续 ≥4 行**每行命中 ≥1 个条目名 ⇒ 违规（多行编号块的副本形态；空行或未命中行中断计数）。
   条目名归一化：去编号 → 去「（记录项…）」尾注 → 去括注 → App 取「：」前 → 去空白 → 小写，子串匹配。
   **fail-closed**：段缺失或条目数 ≠11/≠5 ⇒ 退出码 2，禁止空表放行。
5. `versions` 版本载体：同一文件内**已存在**的载体（frontmatter `version` / 首个 H1 的 `Vx.y.z` /
   `- 版本：x.y.z`）必须相等（`1.0` ≠ `1.0.0`）；存在 `- vX.Y.Z：` 历史条目时，当前版本必须留痕；
   权威源变更日志须逐行合格式且**严格递减**（相等/回升 ⇒ rc=1，格式不符 ⇒ rc=2）。
   载体**格式漂移**（缺冒号 / 4 段版本 / 疑似版本行无法解析 / frontmatter 的 version 无法解析）⇒ rc=1。
   天花板：只比已有载体，**不判**「该不该有版本号」。
6. `pointer` 指针存活：`REQUIRED_POINTERS` 四个消费方必须各含 ≥1 条正文行同时出现
   `交付闸门` 与 `见`/`消费`（标题行与 `- vX` 历史条目不算）。天花板：只判存活，不判文案是否最新。
   判据 B（**仅 info**）：`skills/**` 内反引号包裹的 `~/.config/opencode/...` 路径须在本机存在，
   不存在则报 info（不判红；排除 `<占位符>` 与含 `…` 的模板形态）。补「指针指向已删除文件」这一盲区
   （2026-10-28 曾有 `design-spec/design-spec/` 双前缀断链 3 天未被捕获）。
7. `standards` 标准基线：权威源 `## 无障碍基线（WCAG x.y AA）` 是唯一基线；扫描面内任何
   `WCAG x.y`（**排除准则号形态** `2.4.11` / `24×24px`）必须等于基线，否则 rc=1；
   基线解析失败或 `skills/accessibility/SKILL.md` 缺失 ⇒ rc=2。跳过 `- vX` 历史条目与变更日志表格行。
   判据 A：扫描面内 `（SC x.y.z）`（严格全角括号 + `SC ` 前缀）必须先在权威源 §无障碍基线 表登记，
   否则 rc=1；判据 B：登记了但 `skills/accessibility/platforms/*.md` 无落点 ⇒ 仅 info 行（不判红）。
   天花板：只比版本号与 SC 号登记/落点，**不判**条款分级、条目语义质量、平台映射是否到位。
8. `hygiene`  卫生与清单：判据 A 扫描根内不得存在原位备份（`*.bak` / `*.bak-*`，排除 `.backups/`
   等目录）否则 rc=1；判据 B 解析 `opencode.jsonc` › `commands.design-spec-review.template`，
   其中反引号路径须各自 glob 命中，且必须覆盖 `REQUIRED_POINTERS` 全部消费方 + `REQUIRED_STANDARDS`
   否则 rc=1；模板缺失或 jsonc 解析失败 ⇒ rc=2。
   天花板：只认 `.bak` 命名族（`.before-*` 属盲区）；不判复核是否真读了文件。

扫描面（白名单，防扫进 node_modules/fixtures）
---------------------------------------------
    skills/*/SKILL.md、skills/*/references/*.md、skills/*/checklists/*.md、
    skills/accessibility/platforms/*.md、references/*.md
排除：路径含 node_modules/fixtures/templates/.backups，或文件名含 .bak。
`hygiene` 例外：它按**扫描根**遍历（用于发现原位备份），只跳过 node_modules/fixtures/templates/.backups/.git。

退出码
------
    0 = 全绿 ｜ 1 = 断言失败（stdout 输出 `✗ [组] rel:line 原因`）｜ 2 = 用法/IO/权威源解析失败/必需文件缺失（stderr，不静默通过）

用法
----
    python3 check-design-spec.py                       # 八组全跑
    python3 check-design-spec.py --only anchors --quiet
    python3 check-design-spec.py --root /tmp/copy       # 沙箱扫描（负例验证用）
    DESIGN_SPEC_ROOT=~/.config/opencode python3 ...     # 覆盖宿主根（等价于 --root）
    python3 check-design-spec.py --selftest            # 判据正负例自检
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

# 本脚本现居 <宿主>/design-spec/scripts/：取脚本**出现路径**（不解析软链）的 3 级父目录 = 宿主配置根
# （此前脚本在 <宿主>/scripts/，实现为 parent.parent）。从仓库内直接运行（~/Projects/design-spec/scripts）
# 时把 _HOST 判成 ~/Projects，故用「该目录下有没有 skills/」兜底回落 ~/.config/opencode。
# 换宿主或沙箱扫描用 DESIGN_SPEC_ROOT / --root 覆盖。
_SCRIPT = Path(__file__).absolute()
_HOST = _SCRIPT.parents[2] if len(_SCRIPT.parents) > 2 else _SCRIPT.parent
ROOT = Path(os.environ.get("DESIGN_SPEC_ROOT")
            or (_HOST if (_HOST / "skills").is_dir() else Path.home() / ".config" / "opencode"))
HEADER = ["俗套", "特征", "何时可用"]
EXCLUDE_PARTS = ("node_modules", "fixtures", "templates", ".backups")
HYGIENE_SKIP_DIRS = {"node_modules", "fixtures", "templates", ".backups", ".git", "__pycache__"}
SEP_CELL = re.compile(r"^:?-{3,}:?$")
ANCHOR_PAREN = re.compile(r"（配套\s*v(\d+\.\d+\.\d+)）")
ANCHOR_SUFFIX = re.compile(r"v(\d+\.\d+\.\d+)\s*配套")
ANCHOR_FROZEN = re.compile(r"不承诺.{0,6}同步")
REQUIRED_SUMMARY_FILES = ("skills/app-design/SKILL.md",)
REQUIRED_SUMMARY = REQUIRED_SUMMARY_FILES
GROUPS = ("cliche", "anchors", "summary", "gates", "versions", "pointer", "standards", "hygiene")
REQUIRED_VERSION_FILES = ("skills/frontend-design/SKILL.md", "skills/app-design/SKILL.md", "skills/accessibility/SKILL.md")
FROZEN_ALLOWED = ("design-spec/references/ui-design-anti-patterns.md",)
REQUIRED_STANDARDS = ("skills/accessibility/SKILL.md",)
BASELINE_HEAD = re.compile(r"^## 无障碍基线（WCAG (\d+\.\d+) AA）")
WCAG_REF = re.compile(r"WCAG\s*(\d+\.\d+)(?!\.\d)")
HISTORY_ITEM = re.compile(r"^- v\d")
VERSION_ROW = re.compile(r"^\|\s*\d+\.\d+\.\d+\s*\|")
SC_TAG = re.compile(r"（SC (\d+\.\d+\.\d+)）")
SC_ROW = re.compile(r"^\|\s*(\d+\.\d+\.\d+)\s*\|\s*(?:\*\*)?A{1,3}(?:[^|]*)\|")
STRAY_BACKUP = re.compile(r"\.bak($|-)|\.bak-")
SEASON_PATH = re.compile(r"`(~/\.config/opencode/[^`]+)`")
REQUIRED_POINTERS = {
    "skills/frontend-design/SKILL.md": "Web",
    "skills/clean-code/SKILL.md": "Web",
    "skills/app-design/SKILL.md": "App",
    "skills/product-prototype-generation/SKILL.md": "App",
}
VERSION_TOKEN = r"\d+(?:\.\d+){1,2}"
FM_VERSION = re.compile(r"^\s*version:\s*[\"']?([0-9][0-9.]*)[\"']?\s*$")
H1_VERSION = re.compile(r"\b[Vv](" + VERSION_TOKEN + r")(?![.\d-])")
LINE_VERSION = re.compile(r"^- 版本[：:]\s*v?(" + VERSION_TOKEN + r")(?![.\d-])")
BULLET_VERSION = re.compile(r"^- v(" + VERSION_TOKEN + r")(?![.\d-])[：:]")
LINE_TRUNCATED = re.compile(r"^- 版本[：:]\s*v?\d+(?:\.\d+){3,}")
LOG_ROW = re.compile(r"^\d+\.\d+\.\d+$")
ORPHAN_LOG_ROW = re.compile(r"^\s*\d+\.\d+\.\d+\s*\|")
CHANGELOG_HEADING = "### 变更日志"

# 时效表述守卫：平台事实行若含下列措辞，须同行带核读日期（防把旧摘要/将来时当现状）
STALE_PATTERNS = (
    ("what's-new", re.compile(r"what['’]?s[-\s]new", re.I)),
    ("future releases", re.compile(r"future releases", re.I)),
    ("预计发布", re.compile(r"预计.{0,12}(发布|转\s*stable|稳定|上线)")),
    ("beta", re.compile(r"(?<![A-Za-z])beta(?![a-z])(?!\s*/)", re.I)),
)
STALE_STAMP = re.compile(r"20\d\d-\d{2}|20\d\d\s?H[12]|截至")
# 日期后被「转 stable / 发布 / 上线 / 落地」接走 ⇒ 属将来时目标日期，不算核读日期
TARGET_TAIL = re.compile(r"^\s*[）)]?\s*[，,、]?\s*(?:转\s*(?:stable|正式|GA)|发布|上线|稳定|落地)")
STAMP_LEAD = re.compile(r"(?:截至|核读)\s*$")
GATE_SECTION = "交付闸门"
GATE_WEB_SUB = "### Web 淘汰闸门"
GATE_APP_SUB = "### App 原型记录项"
GATE_WEB_COUNT, GATE_APP_COUNT = 11, 5
NUM_ITEM = re.compile(r"(?:^|(?<=\s))\d+\.\s")
RECORD_TAIL = re.compile(r"（记录项[^）]*）")
PAREN = re.compile(r"（[^）]*）")


# ---------- 通用解析 ----------

def read_lines(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()


def split_row(line):
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.strip() for c in body.split("|")]


def is_separator(cells):
    return bool(cells) and all(SEP_CELL.match(c) for c in cells)


def iter_tables(lines):
    """产出 (表头行号 1-based, header cells, [(行号, cells)])"""
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append((i + 1, split_row(lines[i])))
                i += 1
            if len(block) >= 3:
                header_line, header = block[0]
                yield header_line, header, [(n, c) for n, c in block[1:] if not is_separator(c)]
        else:
            i += 1


def section_table(lines, section, subsection):
    """取 `## section` 段内 `### subsection` 的表格，返回 (header, data rows)。"""
    in_sec = in_sub = False
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if s == f"## {section}":
            in_sec = True
            continue
        if not in_sec:
            continue
        if s.startswith("## "):
            break
        if s == f"### {subsection}":
            in_sub = True
            continue
        if in_sub:
            if s.startswith("### "):
                break
            for header_line, header, data in iter_tables(lines[idx:]):
                return header, data
    return None, []


def changelog_versions(lines):
    """按文件顺序（新→旧）返回版本号列表。"""
    for header_line, header, data in iter_tables(lines):
        if header[:1] == ["版本"]:
            return [c[0] for _, c in data if c and re.match(r"^\d+\.\d+\.\d+$", c[0])]
    return []


# ---------- 断言 1：俗套表副本 ----------

def web_names(lines):
    _, data = section_table(lines, "俗套校准表", "Web")
    return {c[0] for _, c in data if c}


def scan_lines_cliche(names, lines):
    hits = []
    for header_line, header, data in iter_tables(lines):
        if header != HEADER or len(data) < 3:
            continue
        matched = [c[0] for _, c in data if c and c[0] in names]
        if len(matched) >= 2:
            hits.append((header_line, matched))
    return hits


# ---------- 断言 2：版本锚 ----------

def anchor_value(line):
    """纯解析：`- 版本：` 行里的配套锚（不看待冻结）。"""
    if not re.match(r"^-\s*版本[：:]", line.lstrip()):
        return None
    m = ANCHOR_PAREN.search(line) or ANCHOR_SUFFIX.search(line)
    return m.group(1) if m else None


def extract_anchor(line):
    """对外语义：冻结行使锚退出滞后判定（返回 None）。"""
    a = anchor_value(line)
    if a and ANCHOR_FROZEN.search(line):
        return None
    return a


def scan_lines_anchors(versions, lines):
    """返回 [(行号, 锚版本)] 中锚不存在于 versions 的项。"""
    bad = []
    for i, ln in enumerate(lines, 1):
        anchor = extract_anchor(ln)
        if anchor and anchor not in versions:
            bad.append((i, anchor))
    return bad


def has_anchor(lines):
    return any(extract_anchor(ln) for ln in lines)


# ---------- 断言 3：摘要集合 ----------

def summary_blocks(lines):
    """返回 [(起始行号, 块文本)]；块 = 含两关键词的行 + 紧随一行。"""
    blocks = []
    for i, ln in enumerate(lines):
        if "消费哲学层" in ln and "俗套校准表" in ln:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            blocks.append((i + 1, ln + "\n" + nxt))
    return blocks


def parse_summary(text):
    """摘要 → (names set, disabled set, platform or None)"""
    platform = "App" if "· App" in text else ("Web" if "· Web" in text else None)
    body = text.split("\n", 1)[1] if "\n" in text else ""
    names, disabled = set(), set()
    for item in body.split("·"):
        raw = item.strip()
        if not raw:
            continue
        name = re.split(r"[（。]", raw, maxsplit=1)[0].strip()
        if not name:
            continue
        names.add(name)
        if "**禁用**" in raw:
            disabled.add(name)
    return names, disabled, platform


def authority_sets(lines, platform):
    _, data = section_table(lines, "俗套校准表", platform)
    names, disabled = set(), set()
    for _, cells in data:
        if not cells:
            continue
        names.add(cells[0])
        if len(cells) > 2 and cells[2].startswith("**禁用**"):
            disabled.add(cells[0])
    return names, disabled


# ---------- 断言 4：交付闸门副本 ----------

def _gate_normalize(raw):
    """条目名归一化：去记录项尾注 → 去括注 → 取「：」前 → 去空白 → 小写。"""
    s = RECORD_TAIL.sub("", raw)
    s = PAREN.sub("", s)
    s = s.split("：")[0]
    return re.sub(r"\s+", "", s).lower()


def gate_keywords(lines):
    """解析 §交付闸门 ›「### Web 淘汰闸门」/「### App 原型记录项」的条目名；数量不符抛 ValueError（fail-closed）。"""
    web, app = [], []
    in_sec = False
    bucket = None
    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            in_sec = GATE_SECTION in s
            bucket = None
            continue
        if not in_sec:
            continue
        if s.startswith("### "):
            if s.startswith(GATE_WEB_SUB):
                bucket = web
            elif s.startswith(GATE_APP_SUB):
                bucket = app
            else:
                bucket = None
            continue
        if bucket is None or not s or s.startswith(">"):
            continue
        for raw in NUM_ITEM.split(s):
            name = _gate_normalize(raw)
            if name:
                bucket.append(name)
    if len(web) != GATE_WEB_COUNT or len(app) != GATE_APP_COUNT:
        raise ValueError(
            f"权威源解析失败：§{GATE_SECTION} 条目数异常"
            f"（Web {len(web)}≠{GATE_WEB_COUNT}、App {len(app)}≠{GATE_APP_COUNT}）"
        )
    return web, app


def _flat(text):
    return re.sub(r"\s+", "", text).lower()


def scan_lines_gates(web, app, lines):
    """返回 [(起始行号, 形态说明)]。判据 A：单行命中 Web ≥3；判据 B：连续 ≥4 行各命中 ≥1。"""
    kws = list(web) + list(app)
    hits = []
    run_start, run_len = 0, 0
    for i, ln in enumerate(lines, 1):
        flat = _flat(ln)
        n_web = sum(1 for k in web if k in flat)
        if n_web >= 3:
            hits.append((i, f"单行命中 Web 闸门 {n_web}/{len(web)} 项"))
        if any(k in flat for k in kws):
            if run_len == 0:
                run_start = i
            run_len += 1
            if run_len == 4:
                hits.append((run_start, "连续 ≥4 行逐行命中闸门条目（多行块副本）"))
        else:
            run_len = 0
    return hits


# ---------- 共享构件（versions / pointer / summary 缺文件判定） ----------

def require_present(root, authority, rels, group):
    """必需文件必须存在于扫描面（用 candidate_files，不用 scanned —— 避免被「排除权威源」掩盖）。"""
    ap = authority.resolve()
    for rel in rels:
        if (root / rel).resolve() == ap:
            raise ValueError(f"[{group}] REQUIRED_* 不得包含权威源自身：{rel}")
    present = {str(p.relative_to(root)) for p in candidate_files(root)}
    missing = [r for r in rels if r not in present]
    if missing:
        raise ValueError(f"[{group}] 必需文件缺失：{missing}")


def changelog_rows(lines):
    """返回 [(行号, 首格原值)]，不做格式过滤（格式漂移由调用方判 rc=2）。"""
    for header_line, header, data in iter_tables(lines):
        if header[:1] == ["版本"]:
            return [(n, c[0]) for n, c in data if c]
    return []


CHANGELOG_COLS = 5


def scan_changelog_structure(lines):
    """变更日志数据行结构：须 5 个单元格、行内不得出现第二个版本号（防两行合并成一行）。"""
    out = []
    for _, header, data in iter_tables(lines):
        if header[:1] != ["版本"]:
            continue
        for line_no, cells in data:
            if len(cells) != CHANGELOG_COLS:
                out.append((line_no, f"变更日志行应有 {CHANGELOG_COLS} 个单元格，实为 {len(cells)}（疑似两行合并或漏列）"))
            for idx, cell in enumerate(cells[1:], start=2):
                if LOG_ROW.match(cell):
                    out.append((line_no, f"第 {idx} 格是版本号 {cell}（疑似两行合并成一行）"))
        break
    return out


def scan_changelog_orphans(lines):
    """变更日志区内行首缺 `|` 的版本行（已脱离表格，changelog_rows 解析不到）。"""
    start = next((i for i, line in enumerate(lines) if line.strip().startswith(CHANGELOG_HEADING)), None)
    if start is None:
        raise ValueError(f"[versions] 未找到 `{CHANGELOG_HEADING}` 标题，日志行守卫无法生效（fail-closed）")
    out = []
    in_fence = False
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^#{1,6}\s", line):
            break
        if ORPHAN_LOG_ROW.match(line):
            out.append((i + 1, "版本行缺行首竖线（已脱离表格，日志不可解析）"))
    return out


def is_read_stamp(line, stamp):
    """日期能否当核读日期：显式「截至/核读」优先；若后接将来时动词则属目标日期，不算。"""
    if STAMP_LEAD.search(line[:stamp.start()]):
        return True
    return not TARGET_TAIL.search(line[stamp.end():])


def scan_stale_claims(lines):
    """返回 [(行号, 命中词)]：时效表述缺核读日期。跳过变更日志区、围栏、标题与历史条目行。"""
    out = []
    in_changelog = False
    in_fence = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.strip().startswith(CHANGELOG_HEADING):
            in_changelog = True
            continue
        if in_changelog:
            if re.match(r"^#{1,6}\s", line):
                in_changelog = False
            else:
                continue
        if re.match(r"^#{1,6}\s", line) or HISTORY_ITEM.match(line.strip()):
            continue
        for word, pat in STALE_PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            # 落在命中跨度内的日期、以及后接将来时动词的目标日期，都不算核读日期
            stamps = [s for s in STALE_STAMP.finditer(line)
                      if not (m.start() <= s.start() and s.end() <= m.end())
                      and is_read_stamp(line, s)]
            if not stamps:
                out.append((i, word))
            break
    return out


def version_tuple(text):
    return tuple(int(x) for x in text.split("."))


# ---------- 断言 5：版本载体一致性 ----------

def version_carriers(lines):
    """返回 (carriers, drift)。carriers: {'fm','h1','line','bullet'} → [版本串]；drift: [(行号, 原因)]。"""
    carriers = {"fm": [], "h1": [], "line": [], "bullet": []}
    drift = []

    fm_end = None
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm_end = i
                break
    if fm_end is not None:
        for i in range(1, fm_end):
            raw = lines[i]
            if re.match(r"^\s*version:", raw):
                m = FM_VERSION.match(raw)
                if m:
                    carriers["fm"].append(m.group(1))
                else:
                    drift.append((i + 1, "frontmatter 的 version 键无法解析"))

    in_fence = False
    for i, raw in enumerate(lines):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if raw.startswith("# "):
            m = H1_VERSION.search(raw)
            if m:
                carriers["h1"].append(m.group(1))
            elif re.search(r"[Vv]\d", raw):
                drift.append((i + 1, "首个 H1 含版本形态但无法解析"))
            break

    for i, raw in enumerate(lines, 1):
        text = raw.rstrip()
        if LINE_TRUNCATED.match(text):
            drift.append((i, "版本 token 段数 > 3"))
            continue
        if text.startswith("- 版本"):
            m = LINE_VERSION.match(text)
            if m:
                carriers["line"].append(m.group(1))
            else:
                drift.append((i, "「- 版本」行无法解析"))
            continue
        m = BULLET_VERSION.match(text)
        if m:
            carriers["bullet"].append(m.group(1))
    return carriers, drift


def scan_file_versions(rel, lines):
    """返回 [(行号或 0, 原因)]。"""
    carriers, drift = version_carriers(lines)
    fails = [(n, f"载体格式漂移：{why}") for n, why in drift]
    vals = carriers["fm"] + carriers["h1"] + carriers["line"]
    if len(set(vals)) > 1:
        fails.append((0, "载体不一致：fm={} h1={} line={}".format(
            ",".join(carriers["fm"]) or "-", ",".join(carriers["h1"]) or "-", ",".join(carriers["line"]) or "-")))
    if len(set(carriers["line"])) > 1:
        fails.append((0, f"多处「- 版本：」值不一致：{carriers['line']}"))
    if carriers["line"] and carriers["bullet"] and carriers["line"][-1] not in carriers["bullet"]:
        fails.append((0, f"当前版本 {carriers['line'][-1]} 无历史条目（- vX.Y.Z：）留痕"))
    return fails


# ---------- 断言 6：指针存活 ----------

def pointer_line(lines):
    """返回首个「正文行同时含 交付闸门 与 见/消费」的行号；0 = 未命中。"""
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or s.startswith("#") or re.match(r"^- v?\d", s):
            continue
        if "交付闸门" in s and ("见" in s or "消费" in s):
            return i
    return 0


CONFIG_PATH_REF = re.compile(r"`(~/\.config/opencode/[^`]*)`")


def pointer_path_refs(lines):
    """抽取行内反引号包裹的 `~/.config/opencode/...` 路径；跳过占位符与模板形态。

    跳过：含尖括号（如 `skills/<name>`）、含省略号（`…` / `...`）。
    """
    out = []
    for i, raw in enumerate(lines, 1):
        for p in CONFIG_PATH_REF.findall(raw):
            if any(ch in p for ch in "<>") or "…" in p or "..." in p:
                continue
            out.append((i, p))
    return out


def missing_pointer_paths(lines, home):
    """返回 [(行号, 路径)]：`~/.config/opencode/...` 路径在 `home` 下不存在（仅信息项）。"""
    return [(n, p) for n, p in pointer_path_refs(lines)
            if not Path(p.replace("~", str(home))).exists()]


# ---------- 断言 7：标准基线（WCAG） ----------

def standards_baseline(lines):
    """从权威源 §无障碍基线 标题解析基线版本；解析失败抛 ValueError（fail-closed）。"""
    for raw in lines:
        m = BASELINE_HEAD.match(raw.strip())
        if m:
            return m.group(1)
    raise ValueError("[standards] 权威源解析失败：未找到 `## 无障碍基线（WCAG x.y AA）` 标题")


def is_version_table_row(line):
    return bool(VERSION_ROW.match(line.strip()))


def scan_lines_standards(baseline, lines):
    """返回 [(行号, 命中值)]：写出的 WCAG x.y ≠ 基线。跳过历史条目与变更日志表格行。"""
    bad = []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or HISTORY_ITEM.match(s) or is_version_table_row(s):
            continue
        for m in WCAG_REF.finditer(s):
            if m.group(1) != baseline:
                bad.append((i, m.group(1)))
    return bad


# ---------- 断言 7 扩展：SC 登记 / 平台落点 ----------

def _baseline_slice(lines):
    """§无障碍基线 区间：`BASELINE_HEAD` 命中行之后 → 首个 `^## `（不含两端）。

    这是「变更日志数据行（`| 2.3.8 | 2026-10-25 |` 与基线行同形）不被误收」的**唯一真实防线**
    （日志在文末 §维护说明 内，不在本区间）。`baseline_scs` 与 `scan_baseline_levels` 共用，
    避免区间口径两处漂移。
    """
    out = []
    started = False
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not started:
            if BASELINE_HEAD.match(s):
                started = True
            continue
        if s.startswith("## "):
            break
        out.append((i, s))
    return out


# 等级列：宽松行形态（不含等级前缀绑定，坏等级也要能报出来）+ 等级令牌锚定（`AB` 不算 A）
LEVEL_ROW = re.compile(r"^\|\s*(\d+\.\d+\.\d+)\s*\|\s*([^|]*)\|")
LEVEL_TOKEN = re.compile(r"^(A|AA|AAA)(?![A-Za-z0-9])")
LEVEL_RANK = {"A": 1, "AA": 2, "AAA": 3}
CHANGELOG_DATE_CELL = re.compile(r"^20\d\d-")


def scan_baseline_levels(lines):
    """返回 [(行号, 说明)]：等级列取值非法，或等级分组倒退（A → AA → AAA 须非递减）。

    已知盲区（刻意不做）：**组首行**降级（如把 AA 组首位改成 A）不会造成倒退，放行；
    机械只防「写坏 / 非组边界降级 / 错位摆放」，不判「该号官方等级本应是什么」（那属季审）。
    """
    bad = []
    seq = []
    for line_no, s in _baseline_slice(lines):
        m = LEVEL_ROW.match(s)
        if not m:
            continue
        cell = m.group(2).strip()
        if CHANGELOG_DATE_CELL.match(cell):
            # 兜底：日期形态属变更日志行（区间实现若被放宽，这里仍不会误报）
            continue
        token = cell.replace("**", "").strip()
        lm = LEVEL_TOKEN.match(token)
        if not lm:
            bad.append((line_no, f"等级列「{cell}」不合法（仅 A / AA / AAA）"))
            continue
        rest = token[lm.end():].strip()
        if rest and not (rest.startswith("（") and rest.endswith("）")):
            bad.append((line_no, f"等级列「{cell}」不合法（等级后只允许括注，如 `AAA（本仓升为强制）`）"))
            continue
        seq.append((line_no, lm.group(1)))
    for (prev_no, prev), (cur_no, cur) in zip(seq, seq[1:]):
        if LEVEL_RANK[cur] < LEVEL_RANK[prev]:
            order = ",".join(lv for _, lv in seq)
            bad.append((cur_no, "等级分组倒退（序列 "
                               f"{order}；第 {prev_no} 行 {prev} → 第 {cur_no} 行 {cur}，"
                               "表内须按 A → AA → AAA 排列）"))
    return bad


def baseline_scs(lines):
    """权威源 §无障碍基线 表首列 SC 号集合。

    区间由 `_baseline_slice` 硬定义；行形态绑定「首列 x.y.z + 次列等级（A/AA/AAA）」，
    因此变更日志数据行（`| 2.3.8 | 2026-10-25 |`）永远不会被当成登记号。
    空集抛 ValueError（fail-closed）。
    """
    registered = set()
    for _, s in _baseline_slice(lines):
        m = SC_ROW.match(s)
        if m:
            registered.add(m.group(1))
    if not registered:
        raise ValueError("[standards] 权威源 §无障碍基线 表解析失败：未取到任何 SC 号")
    return registered


def scan_lines_sc(registered, lines):
    """返回 [(行号, SC 号)]：写了未登记条款。跳过历史条目与版本表行（历史行不改写）。"""
    bad = []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or HISTORY_ITEM.match(s) or is_version_table_row(s):
            continue
        for m in SC_TAG.finditer(s):
            if m.group(1) not in registered:
                bad.append((i, m.group(1)))
    return bad


def platform_scs_by_file(root):
    """{平台文件 rel: 已打号的 SC 集合}。逐文件是刻意的：并集会掩盖「某平台漏打号」。"""
    by_file = {}
    for p in sorted((root / "skills" / "accessibility" / "platforms").glob("*.md")):
        by_file[str(p.relative_to(root))] = {
            m.group(1) for m in SC_TAG.finditer(p.read_text(encoding="utf-8"))
        }
    return by_file


def coverage_gaps(registered, by_file):
    """[(平台文件 rel, 缺失的 SC)]，逐平台（info，不判红）。

    空落点面（platforms 目录缺失 / 无 .md）抛 ValueError：否则「缺一平台」会退化成
    「整个落点面消失且不吭声」的 fail-open。
    """
    if not by_file:
        raise ValueError("[standards] 平台落点面为空：skills/accessibility/platforms/*.md 缺失或无内容")
    gaps = []
    for rel, found in by_file.items():
        for sc in registered - found:
            gaps.append((rel, sc))
    return sorted(gaps, key=lambda x: (x[0], version_tuple(x[1])))


# ---------- 断言 8：卫生与清单 ----------

def stray_backups(root):
    """扫描根内的原位备份（目录级剪枝，只认 `.bak` 命名族）。"""
    bad = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in HYGIENE_SKIP_DIRS)
        for name in sorted(filenames):
            if STRAY_BACKUP.search(name):
                bad.append(str(Path(dirpath, name).relative_to(root)))
    return bad


def load_jsonc(path):
    """严格解析 → 失败则去行注释兜底（与 scripts/perm_model.py:load_config 同策略）。"""
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(re.sub(r"^\s*//.*$", "", raw, flags=re.M))


def season_paths(root):
    """抽取 `/design-spec-review` 模板里的 `~/...` 路径；模板缺失/解析失败抛 ValueError（rc=2）。"""
    cfg_path = root / "opencode.jsonc"
    if not cfg_path.is_file():
        raise ValueError("[hygiene] 缺少 opencode.jsonc（季审清单 owner）")
    try:
        cfg = load_jsonc(cfg_path)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"[hygiene] opencode.jsonc 解析失败：{e}")
    tpl = ((cfg.get("commands") or {}).get("design-spec-review") or {}).get("template")
    if not isinstance(tpl, str):
        raise ValueError("[hygiene] opencode.jsonc 缺少 commands.design-spec-review.template")
    paths = SEASON_PATH.findall(tpl)
    if not paths:
        raise ValueError("[hygiene] 季审模板内未找到任何 `~/.config/opencode/...` 路径")
    return paths


def season_missing_files(paths):
    """模板中列出的路径必须 glob 命中 ≥1 个文件。"""
    return [p for p in paths if not glob.glob(os.path.expanduser(p))]


def season_missing_consumers(paths):
    """模板必须覆盖全部消费方（指针 4 个 + standards 必需文件）。"""
    need = list(REQUIRED_POINTERS) + list(REQUIRED_STANDARDS)
    return [rel for rel in need if not any(rel in p for p in paths)]


# ---------- 扫描面 ----------

def candidate_files(root):
    seen = set()
    paths = []
    for pat in ("*/SKILL.md", "*/references/*.md", "*/checklists/*.md", "accessibility/platforms/*.md"):
        paths += sorted((root / "skills").glob(pat))
    paths += sorted((root / "references").glob("*.md"))
    for p in paths:
        if any(part in EXCLUDE_PARTS for part in p.parts) or ".bak" in p.name:
            continue
        if p not in seen:
            seen.add(p)
            yield p


def scanned(root, authority):
    """扫描面去掉权威源自身（否则断言 1 会把自己的表判为副本）。"""
    ap = authority.resolve()
    for p in candidate_files(root):
        if p.resolve() != ap:
            yield p


# ---------- 执行 ----------

def run(root, authority, only, quiet):
    lines = read_lines(authority)
    failures = []

    if "cliche" in only:
        names = web_names(lines)
        if not names:
            print("✗ 权威源解析失败：§俗套校准表 › ### Web 无数据行", file=sys.stderr)
            return 2
        for p in scanned(root, authority):
            for line, matched in scan_lines_cliche(names, read_lines(p)):
                failures.append(f"✗ [cliche] {p.relative_to(root)}:{line} 俗套表副本（命中 {len(matched)}/{len(names)}：{'、'.join(matched)}）")

    if "anchors" in only:
        versions = changelog_versions(lines)
        if not versions:
            print("✗ 权威源解析失败：变更日志无版本行", file=sys.stderr)
            return 2
        vset = set(versions)
        for rel in REQUIRED_VERSION_FILES:
            rl = read_lines(root / rel)
            if has_anchor(rl):
                continue
            if any(anchor_value(ln) and ANCHOR_FROZEN.search(ln) for ln in rl):
                failures.append(f"✗ [anchors] {rel} 锚被「不承诺同步」冻结作废（REQUIRED_VERSION_FILES 不允许冻结）")
            else:
                failures.append(f"✗ [anchors] {rel} 缺少「（配套 vX.Y.Z）」锚（删除锚须同轮改本断言）")
        for p in scanned(root, authority):
            rel = p.relative_to(root)
            plines = read_lines(p)
            for i, ln in enumerate(plines, 1):
                a = anchor_value(ln)
                if a and a not in vset:
                    failures.append(f"✗ [anchors] {rel}:{i} 版本锚 v{a} 不存在于变更日志")
                if a and ANCHOR_FROZEN.search(ln) and str(rel) not in FROZEN_ALLOWED:
                    failures.append(f"✗ [anchors] {rel}:{i} 未在 FROZEN_ALLOWED 白名单内却声明「不承诺同步」")
        if not quiet:
            first = versions[0]
            for p in scanned(root, authority):
                for i, ln in enumerate(read_lines(p), 1):
                    a = extract_anchor(ln)
                    if a and a in versions:
                        behind = versions.index(a)
                        if behind:
                            print(f"· [{p.relative_to(root)}:{i}] 锚 v{a} 落后首行 v{first} {behind} 个日志位（信息项，不判红）")

    if "summary" in only:
        require_present(root, authority, REQUIRED_SUMMARY_FILES, "summary")
        for p in scanned(root, authority):
            rel = str(p.relative_to(root))
            plines = read_lines(p)
            blocks = summary_blocks(plines)
            if rel in REQUIRED_SUMMARY and not blocks:
                failures.append(f"✗ [summary] {rel} 缺少约定摘要块（删除摘要须同轮改本断言）")
            for line, text in blocks:
                names, disabled, platform = parse_summary(text)
                if platform is None:
                    continue
                a_names, a_disabled = authority_sets(lines, platform)
                if not a_names:
                    print(f"✗ 权威源解析失败：### {platform} 无数据行", file=sys.stderr)
                    return 2
                if names != a_names:
                    failures.append(f"✗ [summary] {rel}:{line} {platform} 摘要名集合不符：多 {sorted(names - a_names)} 缺 {sorted(a_names - names)}")
                if disabled != a_disabled:
                    failures.append(f"✗ [summary] {rel}:{line} {platform} 摘要禁用集合不符：多 {sorted(disabled - a_disabled)} 缺 {sorted(a_disabled - disabled)}")

    if "gates" in only:
        web, app = gate_keywords(lines)
        for p in scanned(root, authority):
            for line, detail in scan_lines_gates(web, app, read_lines(p)):
                failures.append(f"✗ [gates] {p.relative_to(root)}:{line} 交付闸门副本（{detail}）")

    if "versions" in only:
        rows = changelog_rows(lines)
        if not rows:
            raise ValueError("[versions] 权威源变更日志缺失或为空")
        for line_no, raw in rows:
            if not LOG_ROW.match(raw):
                raise ValueError(f"[versions] 数据行格式不符：变更日志 line {line_no} {raw!r}")
        for (a_line, a_raw), (b_line, b_raw) in zip(rows, rows[1:]):
            if not version_tuple(a_raw) > version_tuple(b_raw):
                failures.append(f"✗ [versions] design-spec/references/ui-design-philosophy.md 变更日志未严格递减：{a_raw} 之后是 {b_raw}")
        for line_no, why in scan_changelog_structure(lines) + scan_changelog_orphans(lines):
            failures.append(f"✗ [versions] {authority.relative_to(root)}:{line_no} {why}")
        require_present(root, authority, REQUIRED_VERSION_FILES, "versions")
        for p in scanned(root, authority):
            rel = p.relative_to(root)
            plines = read_lines(p)
            for line_no, why in scan_file_versions(str(rel), plines):
                where = f"{rel}:{line_no}" if line_no else str(rel)
                failures.append(f"✗ [versions] {where} {why}")
            for line_no, word in scan_stale_claims(plines):
                failures.append(f"✗ [versions] {rel}:{line_no} 时效表述「{word}」缺核读日期（补 `20xx-xx` / `20xx H1|H2` / `截至 …`）")

    if "pointer" in only:
        require_present(root, authority, tuple(REQUIRED_POINTERS), "pointer")
        for p in scanned(root, authority):
            rel = str(p.relative_to(root))
            if rel in REQUIRED_POINTERS and not pointer_line(read_lines(p)):
                failures.append(f"✗ [pointer] {rel} 缺少指向哲学层 §交付闸门 的指针行（消费侧：{REQUIRED_POINTERS[rel]}）")
        if not quiet:
            home = Path.home()
            for p in scanned(root, authority):
                rel = str(p.relative_to(root))
                if not rel.startswith("skills/"):
                    continue
                for line_no, ref in missing_pointer_paths(read_lines(p), home):
                    print(f"· [pointer] {rel}:{line_no} 路径不存在：{ref}（信息项，不判红）")

    if "standards" in only:
        baseline = standards_baseline(lines)
        registered = baseline_scs(lines)
        require_present(root, authority, REQUIRED_STANDARDS, "standards")
        for p in scanned(root, authority):
            rel = p.relative_to(root)
            for line_no, found in scan_lines_standards(baseline, read_lines(p)):
                failures.append(f"✗ [standards] {rel}:{line_no} 写出的 WCAG {found} ≠ 基线 {baseline}")
            for line_no, sc in scan_lines_sc(registered, read_lines(p)):
                failures.append(f"✗ [standards] {rel}:{line_no} 未登记条款 SC {sc}（先在哲学层 §无障碍基线 登记）")
        for line_no, why in scan_baseline_levels(lines):
            failures.append(f"✗ [standards] {authority.relative_to(root)}:{line_no} {why}")
        if not quiet:
            for rel, sc in coverage_gaps(registered, platform_scs_by_file(root)):
                print(f"· [standards] {rel} 缺 SC {sc} 落点（信息项；该平台确不适用请在台账 T 项声明）")

    if "hygiene" in only:
        if not root.is_dir():
            raise ValueError(f"[hygiene] 扫描根不存在：{root}")
        for rel in stray_backups(root):
            failures.append(f"✗ [hygiene] {rel} 原位备份（请移到 .backups/）")
        tpl_paths = season_paths(root)
        for missing in season_missing_files(tpl_paths):
            failures.append(f"✗ [hygiene] 季审清单路径不存在：{missing}")
        for rel in season_missing_consumers(tpl_paths):
            failures.append(f"✗ [hygiene] 季审清单未覆盖消费方：{rel}")

    if failures:
        for f in failures:
            print(f)
        print(f"⇒ {len(failures)} 项失败")
        return 1
    if not quiet:
        print(f"✓ 全绿（{','.join(only)}；扫描 {sum(1 for _ in scanned(root, authority))} 个文件）")
    return 0


def selftest():
    ok = True

    def case(label, got, expect):
        nonlocal ok
        good = bool(got) == expect
        ok = ok and good
        print(f"{'✓' if good else '✗'} {label}")

    lines = read_lines(ROOT / "design-spec" / "references" / "ui-design-philosophy.md")
    names = web_names(lines)
    sample = sorted(names)[:3]
    mk = lambda rows: ["| 俗套 | 特征 | 何时可用 |", "|---|---|---|"] + rows

    case("副本：10 行同构 → 报", scan_lines_cliche(names, mk([f"| {n} | x | y |" for n in names])), True)
    case("副本：3 行无交集 → 不报", scan_lines_cliche(names, mk(["| Material3 紫 | a | b |", "| 系统蓝白 | a | b |", "| 默认 Scaffold | a | b |"])), False)
    case("副本：散文串 → 不报", scan_lines_cliche(names, [f"- 闸门：{'/'.join(sample)} 均为淘汰项"]), False)
    case("副本：表头不同构 → 不报", scan_lines_cliche(names, ["| 名称 | 特征 | 用法 |", "|---|---|---|"] + [f"| {n} | x | y |" for n in names]), False)
    case("副本：仅 2 行 → 不报", scan_lines_cliche(names, mk([f"| {n} | x | y |" for n in sample[:2]])), False)

    vers = {"2.3.3"}
    case("锚：括号词序命中不存在版本 → 报", scan_lines_anchors(vers, ["- 版本：1.0.0（2026-10-25），与 `x.md` v9.9.9 配套"]), True)
    case("锚：后缀词序且存在 → 不报", scan_lines_anchors(vers, ["- 版本：1.2.0（2026-10-25），哲学层共享 `x.md`（配套 v2.3.3）"]), False)
    case("锚：幻影行（含版本但非「- 版本：」）→ 不报", scan_lines_anchors(vers, ["- v2.1.2：新增 2 条 Web 俗套，与哲学层 2.2.2 对齐"]), False)

    a_names, a_disabled = authority_sets(lines, "App")
    case("摘要：名称全等 + 禁用全等 → 不报",
         parse_summary("### App 俗套表（消费哲学层「俗套校准表 · App」）\n" +
                       " · ".join(f"{n}（**禁用**）" if n in a_disabled else n for n in sorted(a_names))) [0] == a_names, True)
    case("摘要：跨条吸入禁用 → 检出",
         parse_summary("### App 俗套表 · App\n" + " · ".join(f"{n}（**禁用**）" for n in sorted(a_names)))[1] == a_disabled, False)
    case("摘要：平台标记缺失 → platform None", parse_summary("### x（消费哲学层「俗套校准表」）\nn/a")[2], False)

    web_kw, app_kw = gate_keywords(lines)
    case("闸门：权威源解析 = 11 + 5", len(web_kw) == 11 and len(app_kw) == 5, True)
    case("闸门：单行斜杠串 11 项副本 → 报", scan_lines_gates(web_kw, app_kw, ["- 闸门：" + "/".join(web_kw)]), True)
    case("闸门：单行只提 2 项（指针） → 不报",
         scan_lines_gates(web_kw, app_kw, ["- 见 §交付闸门（" + "、".join(web_kw[:2]) + "）"]), False)
    block = [f"{i}. {n}" for i, n in enumerate(app_kw, 1)]
    case("闸门：连续 5 行逐行命中 → 报", scan_lines_gates(web_kw, app_kw, block), True)
    case("闸门：连续 3 行 → 不报", scan_lines_gates(web_kw, app_kw, block[:3]), False)
    case("闸门：3 行 + 空行 + 3 行 → 不报",
         scan_lines_gates(web_kw, app_kw, block[:3] + [""] + block[2:]), False)

    def raises_value(fn):
        try:
            fn()
        except ValueError:
            return True
        return False

    def mk_gate(web_names, app_names):
        return (["## 交付闸门（AI 产物）与交付质检", "",
                 "### Web 淘汰闸门（11 项，无 Brief 依据时命中即淘汰）",
                 " ".join(f"{i}. {n}" for i, n in enumerate(web_names, 1)), "",
                 "### App 原型记录项（5 条，非硬禁令，交付时自检回填）"]
                + [f"{i}. {n}：正文（记录项：不淘汰，仅回填）" for i, n in enumerate(app_names, 1)])

    case("闸门：Web 条目数 10 → fail-closed（rc=2 通道）",
         raises_value(lambda: gate_keywords(mk_gate(web_kw[:10], app_kw))), True)
    case("闸门：App 条目数 4 → fail-closed（rc=2 通道）",
         raises_value(lambda: gate_keywords(mk_gate(web_kw, app_kw[:4]))), True)
    case("闸门：段缺失 → fail-closed（rc=2 通道）",
         raises_value(lambda: gate_keywords(["## 别的章节", "正文"])), True)
    case("闸门：结构正确的伪权威源 → 解析通过",
         raises_value(lambda: gate_keywords(mk_gate(web_kw, app_kw))), False)

    def mk_skill(fm=None, h1=None, line=None, bullets=(), fence=False):
        out = []
        if fm is not None:
            out += ["---", "name: x", f"  version: {fm}", "---", ""]
        if h1:
            out.append(h1)
        if fence:
            out += ["```", fence, "```"]
        if line:
            out.append(line)
        out += [f"- v{b}：历史" for b in bullets]
        return out

    case("载体：fm/H1/版本行 三者一致 → 不报",
         scan_file_versions("x", mk_skill('"2.1.4"', "# X V2.1.4", "- 版本：2.1.4（2026-10-25）", ["2.1.4"])), False)
    case("载体：H1 与 fm 不一致 → 报",
         scan_file_versions("x", mk_skill('"2.1.4"', "# X V9.9.9", "- 版本：2.1.4")), True)
    case("载体：双载体两段式同值 → 不报",
         scan_file_versions("x", mk_skill('"1.0"', None, "- 版本：1.0（2026-09-11）")), False)
    case("载体：真·单载体 → 不报",
         scan_file_versions("x", mk_skill(None, "# Agent Evolution v2.0")), False)
    case("载体：缺冒号 → 漂移", scan_file_versions("x", mk_skill(None, None, "- 版本 2.1.4")), True)
    case("载体：4 段版本 → 漂移", scan_file_versions("x", mk_skill(None, None, "- 版本：1.2.3.4")), True)
    case("载体：仅代码围栏内 # … v0.1 → 不误捕",
         scan_file_versions("x", mk_skill(None, None, None, fence="# [名称] 文档 v0.1")), False)
    case("载体：有历史条目但当前版本未留痕 → 报",
         scan_file_versions("x", mk_skill('"2.1.4"', "# X V2.1.4", "- 版本：2.1.4", ["2.1.3"])), True)
    case("载体：无历史条目 → 跳过",
         scan_file_versions("x", mk_skill(None, None, "- 版本：1.1.0（2026-10-25）")), False)
    case("日志：2.3.10 与 2.3.9 序正确", version_tuple("2.3.10") > version_tuple("2.3.9"), True)
    case("日志：相等不算递减", version_tuple("2.3.6") > version_tuple("2.3.6"), False)
    _rows = changelog_rows(lines)
    case("日志：权威源现网严格递减",
         all(version_tuple(a) > version_tuple(b) for (_, a), (_, b) in zip(_rows, _rows[1:])), True)
    _mk_log = lambda data: ["| 版本 | 日期 | 变更章节 | 变更理由 | 兼容性 |", "|---|---|---|---|---|"] + data
    case("日志结构：5 列正常 → 不报",
         scan_changelog_structure(_mk_log(["| 2.3.9 | 2026-10-26 | §x | y | 兼容 |"])), False)
    case("日志结构：两行合并成一行 → 报",
         bool(scan_changelog_structure(_mk_log(
             ["| 2.3.9 | 2026-10-26 | §x | y | | 2.3.8 | 2026-10-25 | §x | z | 兼容 |"]))), True)
    case("日志结构：缺列（4 格）→ 报",
         scan_changelog_structure(_mk_log(["| 2.3.9 | 2026-10-26 | §x | 兼容 |"])), True)
    case("日志结构：5 格但第 4 格裸版本号 → 报",
         scan_changelog_structure(_mk_log(["| 2.3.9 | 2026-10-26 | §x | 2.3.8 | 兼容 |"])), True)
    case("日志结构：行首缺 `|` 的版本行 → 报",
         scan_changelog_orphans(["### 变更日志",
                                 "| 2.3.9 | 2026-10-26 | §x | y | 兼容 |",
                                 "2.3.8 | 2026-10-25 | §x | y | 兼容 |"]), True)
    case("日志结构：正常表格行不误判为孤儿",
         scan_changelog_orphans(["### 变更日志",
                                 "| 2.3.9 | 2026-10-26 | §x | y | 兼容 |"]), False)
    case("日志结构：围栏内与下一章节后不误判",
         scan_changelog_orphans(["### 变更日志", "```", "2.3.8 | x", "```", "## 下一节", "2.3.7 | x"]), False)
    case("日志结构：缺标题 → rc=2 通道",
         raises_value(lambda: scan_changelog_orphans(["# 别的章节"])), True)
    case("时效：future releases 无日期 → 报",
         scan_stale_claims(["- Material 组件原生 style 参数官方称 future releases"]), True)
    case("时效：同句带日期 → 不报",
         scan_stale_claims(["- 官方称 future releases（截至 2026-10-26）"]), False)
    case("时效：变更日志历史行 → 不报",
         scan_stale_claims(["### 变更日志", "| 2.3.5 | 2026-10-25 | x | 据 what's-new 摘要 | y |"]), False)
    case("时效：channel 枚举 beta/next → 不报",
         scan_stale_claims(["**全部由 channel（latest/dev/beta/next/prod）决定**"]), False)
    case("时效：无撇号 whats-new → 报",
         scan_stale_claims(["- 据 whats-new 摘要"]), True)
    case("时效：预测期自带日期不算核读日期 → 报",
         scan_stale_claims(["- x 预计 2026 H2 转 stable"]), True)
    case("时效：另有独立日期 → 不报",
         scan_stale_claims(["- x 预计发布（截至 2026-10-26）"]), False)
    case("时效：beta 后的目标日期不算核读 → 报",
         scan_stale_claims(["- x 处于 beta，2026 H2 转 stable"]), True)
    case("时效：beta 后带截至日期 → 不报",
         scan_stale_claims(["- x 处于 beta（截至 2026-10-26）"]), False)
    case("时效：目标日期 + 独立核读日期 → 不报",
         scan_stale_claims(["- x 处于 beta，2026 H2 转 stable（截至 2026-10-26）"]), False)
    case("时效：目标日期识别（后接发布）→ 不算核读",
         is_read_stamp("- x 2026-10 发布", STALE_STAMP.search("- x 2026-10 发布")), False)
    case("时效：历史条目行 → 不报",
         scan_stale_claims(["- v1.2.3：官方称 future releases"]), False)
    case("时效：代码围栏内 → 不报",
         scan_stale_claims(["```", "- 据 future releases", "```"]), False)
    case("时效：betamax 不误报",
         scan_stale_claims(["- betamax 是别的库"]), False)
    case("锚：冻结文件仍须有真实锚（A×D）",
         has_anchor(["- 版本：1.1.0（2026-10-25），与 x v2.3.0 配套（不承诺逐版同步）"]), False)
    case("锚：显式不承诺同步 → 不参与判定",
         extract_anchor("- 版本：1.1.0（2026-10-25），与 x v2.3.0 配套（不承诺逐版同步）"), False)
    case("锚：正常配套 → 仍解析",
         extract_anchor("- 版本：2.1.5（2026-10-26），…（配套 v2.4.1）"), True)
    case("锚：缺配套 → 判定为无锚",
         has_anchor(["- 版本：2.1.5（2026-10-26），哲学层抽到 design-spec/references/ui-design-philosophy.md"]), False)
    case("锚：有配套 → 判定为有锚",
         has_anchor(["- 版本：2.1.6（2026-10-26），…（配套 v2.4.2）"]), True)
    case("必需文件：权威源自身不得进 REQUIRED_*",
         raises_value(lambda: require_present(ROOT, ROOT / "design-spec" / "references" / "ui-design-philosophy.md",
                                              ("design-spec/references/ui-design-philosophy.md",), "x")), True)
    case("必需文件：缺失 → rc=2 通道",
         raises_value(lambda: require_present(ROOT, ROOT / "design-spec" / "references" / "ui-design-philosophy.md",
                                              ("skills/nope/SKILL.md",), "x")), True)

    case("指针：正文行命中 → 存活", pointer_line(["- [ ] 闸门：见哲学层 §交付闸门（11 项）"]), True)
    case("指针：仅标题行命中 → 报", pointer_line(["## 原型验收条款（消费哲学层 §交付闸门）"]), False)
    case("指针：仅历史 bullet 命中 → 报", pointer_line(["- v1.2.2：条款并入 §交付闸门（见哲学层）"]), False)

    real_home = Path.home()
    case("指针路径：本机存在的路径 → 不报",
         missing_pointer_paths(["- 读 `~/.config/opencode/design-spec/references/ui-design-philosophy.md`"], real_home),
         False)
    case("指针路径：不存在的路径 → 报",
         missing_pointer_paths(["- 读 `~/.config/opencode/design-spec/design-spec/references/ui-design-philosophy.md`"], real_home),
         True)
    case("指针路径：尖括号占位符 → 不报",
         missing_pointer_paths(["见 `~/.config/opencode/skills/<name>/SKILL.md`"], Path("/nonexistent-root")),
         False)
    case("指针路径：省略号模板 → 不报",
         missing_pointer_paths(["见 `~/.config/opencode/skills/…`"], Path("/nonexistent-root")),
         False)

    case("基线：权威源解析出 2.2 且为字符串", standards_baseline(lines) == "2.2", True)
    case("基线：2.1 与基线 2.2 冲突 → 报", scan_lines_standards("2.2", ["- 标准：WCAG 2.1 AA"]), True)
    case("基线：准则号 2.4.11 → 不判", scan_lines_standards("2.2", ["见 WCAG 2.4.11 焦点不被遮挡"]), False)
    case("基线：24×24px → 不判", scan_lines_standards("2.2", ["WCAG 24×24px 最小目标"]), False)
    case("基线：准则号 4.1.3 → 不判", scan_lines_standards("2.2", ["WCAG 4.1.3 状态消息"]), False)
    case("基线：历史条目 - v1.0：WCAG 2.1 → 跳过",
         scan_lines_standards("2.2", ["- v1.0：以 WCAG 2.1 AA 为基准"]), False)
    case("基线：变更日志表格行 → 跳过",
         scan_lines_standards("2.2", ["| 1.0.0 | 2026-01-01 | 基线 WCAG 2.1 | x | 兼容 |"]), False)
    case("基线：标题缺失 → rc=2 通道", raises_value(lambda: standards_baseline(["## 无障碍基线"])), True)

    scs = baseline_scs(lines)
    # 改 §无障碍基线 行数须同轮改本常量与用例名（见 docs/plan/design-spec-sync-todo.md #12）
    case("SC：登记集合 17 条且不含变更日志号", len(scs) == 17 and "2.3.8" not in scs, True)
    case("SC：4.1.3 已登记不报", bool(scan_lines_sc(scs, ["- [ ] x（SC 4.1.3）"])), False)
    case("SC：已登记号不报", bool(scan_lines_sc(scs, ["- [ ] x（SC 2.4.11）"])), False)
    case("SC：未登记号 → 报", bool(scan_lines_sc(scs, ["- [ ] x（SC 9.9.9）"])), True)
    case("SC：半角括号不命中", bool(scan_lines_sc(scs, ["- [ ] x (SC 9.9.9)"])), False)
    case("SC：历史条目内 → 跳过", bool(scan_lines_sc(scs, ["- v1.0：x（SC 9.9.9）"])), False)
    case("SC：基线表无 SC 号 → rc=2 通道",
         raises_value(lambda: baseline_scs(["## 无障碍基线（WCAG 2.2 AA）", "| 编号 | 等级 |", "|---|---|", "", "## 下一节"])), True)

    # ---- 等级列（仅 A / AA / AAA + A → AA → AAA 非递减）----
    lv_head = ["## 无障碍基线（WCAG 2.2 AA）", "| 编号 | 等级 | 要求 | 踩坑场景 |", "|---|---|---|---|"]
    case("等级：A → AA → AAA 单调 → 不报",
         scan_baseline_levels(lv_head + ["| 3.2.6 | A | a | b |", "| 2.4.11 | AA | a | b |",
                                         "| 2.3.3 | **AAA（本仓升为强制）** | a | b |", "", "## 下一节"]), False)
    case("等级：AA 组末位写 A → 报倒退",
         any("倒退" in why for _, why in scan_baseline_levels(
             lv_head + ["| 3.3.8 | AA | a | b |", "| 4.1.3 | A | a | b |"])), True)
    case("等级：组首写 A → 不报（已知盲区，固化防误修）",
         scan_baseline_levels(lv_head + ["| 2.4.11 | A | a | b |", "| 3.3.8 | AA | a | b |"]), False)
    case("等级：AB → 报不合法",
         any("不合法" in why for _, why in scan_baseline_levels(lv_head + ["| 4.1.3 | AB | a | b |"])), True)
    case("等级：区间内变更日志行形态 → 不报（日期兜底）",
         scan_baseline_levels(lv_head + ["| 2.3.8 | 2026-10-25 | §x | y | 兼容 |"]), False)

    # ---- 落点：逐平台（并集掩盖的漏打号）----
    case("落点：逐平台点名缺失项",
         coverage_gaps({"4.1.3"}, {"skills/accessibility/platforms/web.md": {"4.1.3"},
                                   "skills/accessibility/platforms/ios.md": set()})
         == [("skills/accessibility/platforms/ios.md", "4.1.3")], True)
    case("落点：落点面为空 → fail-closed", raises_value(lambda: coverage_gaps({"4.1.3"}, {})), True)

    case("卫生：x.md.bak-1 命中", bool(STRAY_BACKUP.search("x.md.bak-1")), True)
    case("卫生：x.md.bak 命中", bool(STRAY_BACKUP.search("x.md.bak")), True)
    case("卫生：x.md 不命中", bool(STRAY_BACKUP.search("x.md")), False)
    _tpl = "见 `~/.config/opencode/skills/a/SKILL.md` 与 `~/.config/opencode/references/x.md`"
    case("清单：抽取模板路径",
         SEASON_PATH.findall(_tpl) == ["~/.config/opencode/skills/a/SKILL.md",
                                       "~/.config/opencode/references/x.md"], True)
    case("清单：缺 accessibility → 报",
         bool(season_missing_consumers(["~/.config/opencode/skills/frontend-design/SKILL.md"])), True)
    case("清单：全覆盖 → 不报",
         bool(season_missing_consumers([f"~/.config/opencode/{rel}" for rel in
                                        list(REQUIRED_POINTERS) + list(REQUIRED_STANDARDS)])), False)
    case("清单：路径不存在 → 报", bool(season_missing_files(["~/__nope__/x.md"])), True)

    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="设计规范一致性校验")
    ap.add_argument("--root", default=str(ROOT), help="扫描根（缺省=配置根）")
    ap.add_argument("--authority", help="覆盖权威源路径")
    ap.add_argument("--only", default="all", help="cliche|anchors|summary|gates|versions|pointer|standards|hygiene|all（逗号分隔）")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    authority = Path(args.authority) if args.authority else root / "design-spec" / "references" / "ui-design-philosophy.md"
    only = GROUPS if args.only == "all" else tuple(x.strip() for x in args.only.split(",") if x.strip())
    unknown = [g for g in only if g not in GROUPS]
    if unknown:
        print(f"✗ 未知断言组：{unknown}（可选 {GROUPS}）", file=sys.stderr)
        return 2
    if not authority.is_file():
        print(f"✗ 权威源不存在：{authority}", file=sys.stderr)
        return 2
    try:
        return selftest() if args.selftest else run(root, authority, only, args.quiet)
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"✗ IO 错误：{e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
