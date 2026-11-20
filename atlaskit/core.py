"""atlaskit 核心 API：多页图集打包器。

装箱算法：shelf（货架式）。每页由若干水平货架组成，矩形从左到右放入
当前货架；放不下时开启新货架；新货架也放不下时抛出 ValueError，且
不改变任何内部状态（天然回滚）。算法对同一输入序列完全确定。
"""

__all__ = ["Packer"]


class _Page:
    """单页的货架状态。"""

    __slots__ = ("w", "h", "shelf_y", "shelf_h", "x", "order")

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.shelf_y = 0   # 当前货架顶部 y
        self.shelf_h = 0   # 当前货架高度，0 表示空页
        self.x = 0         # 当前货架内的水平游标
        self.order = []    # 本页矩形 rid，按加入顺序


class Packer:
    def __init__(self, page_w, page_h, allow_rotate=False):
        """构造打包器"""
        if page_w <= 0 or page_h <= 0:
            raise ValueError("页面尺寸必须为正数")
        self.page_w = page_w
        self.page_h = page_h
        self.allow_rotate = allow_rotate
        self._pages = [_Page(page_w, page_h)]
        self._placed = {}  # rid -> (x, y, w, h, page_index)
        self._ops = []     # 操作日志：('add', rid, w, h) 或 ('page',)，用于回滚重放

    # ---- 内部 ----

    def _candidates(self, w, h):
        """待尝试的朝向：优先原始朝向，允许旋转时再试 90 度旋转。"""
        cands = [(w, h)]
        if self.allow_rotate and (h, w) != (w, h):
            cands.append((h, w))
        return cands

    def _try_place(self, page, w, h):
        """尝试在当前页为 w×h 找位置。成功返回 (x, y)，失败返回 None。

        只读检查，不改变页状态——调用方据此实现"放不下时不留痕迹"。
        """
        if w > page.w or h > page.h:
            return None
        if page.shelf_h == 0:
            # 空页第一个货架
            return (0, 0)
        # 当前货架：宽度够且（高度够 或 撑高后仍不出页）
        if page.x + w <= page.w:
            if h <= page.shelf_h or page.shelf_y + h <= page.h:
                return (page.x, page.shelf_y)
        # 新货架：底边必须严格在页底之上
        y = page.shelf_y + page.shelf_h
        if y + h < page.h:
            return (0, y)
        return None

    def _commit(self, page, w, h, x, y):
        """把通过 _try_place 验证的位置落到页状态上。"""
        if page.shelf_h == 0:
            page.shelf_y, page.shelf_h = 0, h
            page.x = w
        elif y == page.shelf_y:
            page.x += w
            if h > page.shelf_h:
                page.shelf_h = h
        else:
            page.shelf_y, page.shelf_h = y, h
            page.x = w

    def _place_on_current(self, rid, w, h):
        """在当前页放置，成功返回 (x, y, w, h, page)，失败返回 None。"""
        page = self._pages[-1]
        for cw, ch in self._candidates(w, h):
            pos = self._try_place(page, cw, ch)
            if pos is not None:
                self._commit(page, cw, ch, pos[0], pos[1])
                idx = len(self._pages) - 1
                rect = (pos[0], pos[1], cw, ch, idx)
                self._placed[rid] = rect
                page.order.append(rid)
                return rect
        return None

    def _rebuild(self):
        """按操作日志重放，重建全部状态（回滚用）。"""
        ops = self._ops
        self._pages = [_Page(self.page_w, self.page_h)]
        self._placed = {}
        self._ops = []
        for op in ops:
            if op[0] == "page":
                self.next_page()
            else:
                _, rid, w, h = op
                rect = self._place_on_current(rid, w, h)
                assert rect is not None, "重放历史操作不可能失败"
                self._ops.append(op)

    # ---- 公开 API ----

    def add(self, rid, size):
        """加入矩形，返回 (x,y,w,h,page)。放不下时抛 ValueError 且状态不变。"""
        w, h = size
        if rid in self._placed:
            raise ValueError(f"重复 ID: {rid!r}")
        if w <= 0 or h <= 0:
            raise ValueError(f"非法尺寸: {size!r}")
        rect = self._place_on_current(rid, w, h)
        if rect is None:
            raise ValueError(f"当前页放不下: {rid!r} {size!r}")
        self._ops.append(("add", rid, w, h))
        return rect

    def rollback(self):
        """撤销最后一次加入"""
        for i in range(len(self._ops) - 1, -1, -1):
            if self._ops[i][0] == "add":
                del self._ops[i]
                break
        else:
            raise ValueError("没有可撤销的加入")
        self._rebuild()

    def next_page(self):
        """翻页"""
        self._pages.append(_Page(self.page_w, self.page_h))
        self._ops.append(("page",))
        return len(self._pages) - 1

    def rects(self):
        """当前页的矩形列表，元素为 (x, y, w, h, page)，按加入顺序。"""
        page = self._pages[-1]
        return [self._placed[rid] for rid in page.order]

    def stats(self):
        """返回 {'count','pages','fill'}，fill = 矩形总面积 / 各页占用包围盒面积之和。"""
        area = 0
        bbox = 0
        for page in self._pages:
            if not page.order:
                continue
            mx = my = 0
            for rid in page.order:
                x, y, w, h, _ = self._placed[rid]
                area += w * h
                mx = max(mx, x + w)
                my = max(my, y + h)
            bbox += mx * my
        return {
            "count": len(self._placed),
            "pages": len(self._pages),
            "fill": (area / bbox) if bbox else 0.0,
        }

    def uv(self, rid):
        """该矩形的 UV（v 轴翻转，使用其所在页的页面尺寸）。"""
        try:
            x, y, w, h, idx = self._placed[rid]
        except KeyError:
            raise ValueError(f"未知 ID: {rid!r}") from None
        page = self._pages[idx]
        pw, ph = page.w, page.h
        return (x / pw, 1.0 - y / ph, (x + w) / pw, 1.0 - (y + h) / ph)
