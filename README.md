# design-spec

跨端 UI 设计规范的**唯一权威源**（哲学层）：设计立场、原则、两遍工作法、平台硬规则、俗套校准表、交付闸门、无障碍基线，以及配套的反面案例库与一致性校验器。

> 消费方（`frontend-design` / `app-design` / `clean-code` / `product-prototype-generation` / `accessibility`）只写**指针**，不复述条款；副本会被校验器判红。

## 内容

```
references/ui-design-philosophy.md    # 哲学层本体（条款 + 变更日志 + 维护说明）
references/ui-design-anti-patterns.md # 反面案例库（8 例 + 锚语义）
scripts/check-design-spec.py          # 一致性校验器（八组断言，含 selftest）
```

## 挂载（目录级软链）

```bash
git clone https://github.com/liaochzh/design-spec.git ~/Projects/design-spec
ln -s ~/Projects/design-spec ~/.config/opencode/design-spec
```

挂载后的规范路径：

- 哲学层：`~/.config/opencode/design-spec/references/ui-design-philosophy.md`
- 反面案例：`~/.config/opencode/design-spec/references/ui-design-anti-patterns.md`
- 校验器：`~/.config/opencode/design-spec/scripts/check-design-spec.py`

换宿主时只换这一条软链，仓库内容不动。

## 一致性校验

```bash
python3 ~/.config/opencode/design-spec/scripts/check-design-spec.py            # 八组全跑
python3 ~/.config/opencode/design-spec/scripts/check-design-spec.py --quiet    # 只出失败项
python3 ~/.config/opencode/design-spec/scripts/check-design-spec.py --selftest # 断言自身自测
python3 ~/.config/opencode/design-spec/scripts/check-design-spec.py --only pointer
```

八组断言：`cliche`（俗套表副本）/ `anchors`（版本锚）/ `summary`（摘要集合）/ `gates`（交付闸门副本）/ `versions`（版本载体）/ `pointer`（消费方指针存活）/ `standards`（WCAG 基线）/ `hygiene`（原位备份与季审清单）。

退出码：`0` 全绿｜`1` 断言失败｜`2` 用法/IO/权威源解析失败（不静默通过）。

扫描根默认取「脚本所在路径的上三级」= `~/.config/opencode`；沙箱或换宿主用 `--root` / `DESIGN_SPEC_ROOT` 覆盖。

## 消费方契约

| 消费方 | 义务 | 机械守护 |
|---|---|---|
| `frontend-design`(Web) / `app-design`(App) | 各留 ≥1 条「见哲学层 §交付闸门」指针；版本行带「（配套 vX.Y.Z）」锚 | `pointer` / `anchors` / `versions` |
| `clean-code`(Web) / `product-prototype-generation`(App) | 指针存活 | `pointer` |
| `accessibility` | 以 §无障碍基线 为唯一标准口径，逐平台登记落点 | `standards` |

**改本仓库后必须跑校验器**；`rc=1` 即说明某处出现了副本或锚指向不存在的版本。季审用 `/design-spec-review` 命令。

## 文档口径

`docs/plan`、`docs/review`、`docs/test`、`docs/baton` 是本项目的本地工作文档（方案、审查、验收入档、接力棒），按 `.gitignore` **不发布**。
