"""User-authorized pixel-only cleanup; preserve source and opaque RGB."""
import hashlib
import json
from pathlib import Path

from PySide6.QtGui import QImage


def bounds(image, threshold=0):
    alpha = bytes(image.convertToFormat(QImage.Format.Format_RGBA8888).constBits())[3::4]
    xs, ys = [], []
    for y in range(image.height()):
        row = alpha[y * image.width():(y + 1) * image.width()]
        values = [x for x, a in enumerate(row) if a > threshold]
        if values:
            xs.extend((values[0], values[-1]))
            ys.append(y)
    if not ys:
        raise ValueError("Empty character")
    return [min(xs), min(ys), max(xs) + 1, max(ys) + 1]


def sole_center(image, floor):
    xs = []
    for y in range(max(0, floor - 9), floor + 1):
        xs.extend(x for x in range(image.width()) if image.pixelColor(x, y).alpha() >= 80)
    return (min(xs) + max(xs)) / 2


def main():
    root = Path(__file__).resolve().parents[1] / 'assets/characters/aang'
    source = root / 'source/look_around/original_sheet.png'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    image = QImage(str(source)).convertToFormat(QImage.Format.Format_RGBA8888)
    if (image.width(), image.height()) != (1448, 1086):
        raise ValueError('Expected supplied 1448x1086 sheet')
    reference = QImage(str(root / 'frames_v04/side_idle/side_idle_01.png'))
    ref_foot = sole_center(reference, 735)
    output = root / 'frames_look_around'
    output.mkdir(parents=True, exist_ok=True)
    records, cleaned, anchors = [], [], []
    height = None
    for index in range(4):
        cell = image.copy(index * 362, 0, 362, 1086)
        data = bytearray(bytes(cell.constBits()))
        removed = 0
        for offset in range(0, len(data), 4):
            if data[offset + 3] < 80:
                removed += data[offset + 3] > 0
                data[offset:offset + 4] = b'\0\0\0\0'
        frame = QImage(bytes(data), 362, 1086, 362 * 4, QImage.Format.Format_RGBA8888).copy()
        box = bounds(frame)
        if height is None:
            height = box[3] - box[1]
        foot = sole_center(frame, box[3] - 1)
        # Register to the existing standing sprite's sole center; common scale.
        anchor_x = foot - (ref_foot - 256) * height / 680
        anchors.append([anchor_x, box[3] - 1])
        path = output / f'look_around_{index + 1:02}.png'
        if not frame.save(str(path)):
            raise OSError(path)
        assert QImage(str(path)).size() == frame.size()
        original = bytes(cell.constBits())
        retained = all(original[i:i + 4] == bytes(data[i:i + 4])
                       for i in range(0, len(data), 4) if original[i + 3] >= 80)
        assert retained
        records.append({'frame':path.name, 'source_cell':[index * 362, 0, 362, 1086],
                        'removed_low_alpha_pixels':removed, 'retained_rgba_unchanged':retained,
                        'bbox':box, 'anchor':anchors[-1], 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        cleaned.append(frame)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    spec = {'version':1, 'clips':{'look_around':{'directory':'frames_look_around', 'prefix':'look_around',
            'canvas':[362,1086], 'anchor':anchors[0], 'anchors':anchors, 'standing_height':height,
            'durations_ms':[320,500,500,320]}}}
    (root / 'extra_clips.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')
    report = {'source_sha256':source_hash, 'source_unchanged':True, 'alpha_cutoff':80,
              'resized_or_redrawn':False, 'shared_standing_height':height, 'reference_sole_center':ref_foot,
              'frames':records, 'limit':'Low-alpha edge removal is heuristic; no new poses or body redesign.'}
    audit = root / 'audit/look_around'
    audit.mkdir(parents=True, exist_ok=True)
    (audit / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
