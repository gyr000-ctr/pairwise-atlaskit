# pairwise-atlaskit

## 题面（可直接粘贴）

图集打包器加多页后出现重叠与空间浪费：放不下时没有回滚、重复 ID 静默覆盖、翻页后 UV 仍按第一页算、12 个矩形只用了不到一半面积。atlaskit/core.py 是核心，tests/test_core.py 15 个红。要修的是：放不下必须回滚且不改变页面；重复 ID、负尺寸、超页尺寸抛 ValueError；多页 UV 用对应页尺寸；同一批矩形填充率不低于 70%；结果确定可复现；支持 90 度旋转。

## 运行方式

```bash
python -m pytest tests -q
```

初始结果应为 `15 failed`（全部因 `NotImplementedError` 失败，无 collection error）。

## 字段

- 所属领域：游戏、图形与多媒体
- 子方向：图形渲染
- 任务类型：Bugfix
- 语言/框架：Python 3, pytest
- 环境可复现等级：无外部依赖
