"""Render AIR_BLAST v1.1 GIFs and timing data with the runtime Qt renderer.

Run with an output directory argument. Pillow is needed for GIF export only.
"""
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from animation import ANCHOR, SpriteAnimation, VISIBLE_HEIGHT
from avatar import Action


def render(animation, time, background, direction=1):
    area = QRectF(0, 0, 960, 200)
    ground = QPointF(180 if direction > 0 else 780, 175)
    height = 120
    scale = height / VISIBLE_HEIGHT
    image = QImage(960, 200, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(background))
    animation.advance(Action.AIR_BLAST, 0)
    animation.elapsed = time
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.save()
    painter.translate(ground)
    painter.scale(direction, 1)
    rect = animation.render_rect
    target = QRectF((rect.x() - ANCHOR[0]) * scale, (rect.y() - ANCHOR[1]) * scale,
                    rect.width() * scale, rect.height() * scale)
    painter.drawPixmap(target, animation.pixmap, QRectF(animation.pixmap.rect()))
    painter.restore()
    scene = animation.blast_effects.scene(time, area, ground, height, direction, animation.index)
    animation.blast_effects.paint(painter, scene)
    painter.end()
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    result = Image.frombytes("RGBA", (rgba.width(), rgba.height()), bytes(rgba.constBits())).convert("RGB")
    return result, scene


def main():
    app = QApplication.instance() or QApplication([])
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    animation = SpriteAnimation()
    if animation.warnings or animation.blast_effects is None:
        raise ValueError(animation.warnings)
    trace = []
    for label, color in (("dark", "#20252d"), ("white", "#ffffff")):
        frames = []
        for milliseconds in range(0, 2040, 40):
            time = min(2.0, milliseconds / 1000)
            image, scene = render(animation, time, color)
            frames.append(image)
            if label == "dark":
                trace.append({"time_ms": milliseconds, "character_frame": animation.index + 1,
                              "palm": [scene.palm.x(), scene.palm.y()],
                              "forward_extent": scene.front.width(), "front_active": not scene.front.isEmpty()})
        frames[0].save(output / f"air_blast_v11_{label}.gif", save_all=True, append_images=frames[1:],
                       duration=40, loop=0, disposal=2)
        render(animation, .760, color)[0].save(output / f"air_blast_v11_{label}_launch.png")
    render(animation, .760, "#ffffff", -1)[0].save(output / "air_blast_v11_left_launch.png")
    (output / "timing_trace.json").write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    print(output.resolve())


if __name__ == "__main__":
    main()
