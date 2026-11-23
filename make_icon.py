#!/usr/bin/env python3
# 재고관리 앱 아이콘 생성 — 파란 라운드 배경 + 흰 클립보드/체크
from PIL import Image, ImageDraw

S = 4  # supersample
BLUE_TOP = (58, 124, 244)
BLUE_BOT = (28, 78, 190)
WHITE = (255, 255, 255, 255)


def rounded(draw, box, radius, fill=None, outline=None, width=0):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make(size, pad_ratio=0.0, bg_radius_ratio=0.22, full_bleed=True):
    W = size * S
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 배경 그라데이션
    grad = Image.new("RGBA", (1, W))
    gd = ImageDraw.Draw(grad)
    for y in range(W):
        t = y / (W - 1)
        c = tuple(int(BLUE_TOP[i] + (BLUE_BOT[i] - BLUE_TOP[i]) * t) for i in range(3)) + (255,)
        gd.point((0, y), fill=c)
    grad = grad.resize((W, W))

    if full_bleed:
        mask = Image.new("L", (W, W), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, W - 1, W - 1), radius=int(W * bg_radius_ratio), fill=255)
        img.paste(grad, (0, 0), mask)
    else:
        # iOS 홈 아이콘은 OS가 라운드를 씌우므로 꽉 찬 사각 배경
        img.paste(grad, (0, 0))

    d = ImageDraw.Draw(img)

    # 콘텐츠를 안전 영역(80%) 안에 배치
    m = int(W * (0.12 + pad_ratio))
    w = W - 2 * m

    def X(p):
        return m + int(p * w)

    # 클립보드 판 (테두리)
    stroke = int(w * 0.075)
    board_top = X(0.10)
    board_bot = X(0.94)
    rounded(d, (X(0.05), board_top, X(0.95), board_bot), radius=int(w * 0.12),
            outline=WHITE, width=stroke)

    # 상단 클립
    clip_w = int(w * 0.26)
    clip_h = int(w * 0.13)
    cx = X(0.5)
    clip_top = X(0.015)
    rounded(d, (cx - clip_w // 2, clip_top, cx + clip_w // 2, clip_top + clip_h),
            radius=int(clip_h * 0.42), fill=WHITE)

    # 체크 표시
    pts = [(X(0.27), X(0.56)), (X(0.44), X(0.72)), (X(0.75), X(0.38))]
    d.line(pts, fill=WHITE, width=int(w * 0.105), joint="curve")
    # 둥근 끝마감
    r = int(w * 0.0525)
    for p in (pts[0], pts[-1]):
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=WHITE)

    return img.resize((size, size), Image.LANCZOS)


def save(img, path):
    img.save(path, optimize=True)
    print(path, img.size)


save(make(512), "icon-512.png")
save(make(192), "icon-192.png")
save(make(180, full_bleed=False), "icon-180.png")
save(make(32), "icon-32.png")
# maskable: 안전 영역 80% 안쪽으로 더 축소
save(make(512, pad_ratio=0.06), "icon-512-maskable.png")
