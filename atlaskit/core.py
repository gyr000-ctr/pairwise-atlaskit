"""atlaskit 核心 API（初始未实现）。"""


class Packer:
    def __init__(self, page_w, page_h, allow_rotate=False):
        """构造打包器"""
        raise NotImplementedError

    def add(self, rid, size):
        """加入矩形，返回 (x,y,w,h,page)"""
        raise NotImplementedError

    def rollback(self):
        """撤销最后一次加入"""
        raise NotImplementedError

    def next_page(self):
        """翻页"""
        raise NotImplementedError

    def rects(self):
        """当前矩形"""
        raise NotImplementedError

    def stats(self):
        """返回 {'count','pages','fill'}"""
        raise NotImplementedError

    def uv(self, rid):
        """该矩形 UV"""
        raise NotImplementedError
