"""
[2단계-보조] Pascal VOC(XML) → YOLO(txt) 변환

LabelImg 를 PascalVOC 모드로 사용했거나, 외부에서 XML 라벨을 받은 경우 사용합니다.
(LabelImg 를 YOLO 모드로 썼거나 Label Studio / Roboflow 에서 'YOLO' 로 export 했다면 필요 없음)

입력 : --xml-dir 폴더의 *.xml  (픽셀 좌표 xmin/ymin/xmax/ymax + 이미지 크기)
출력 : data/labeled/labels/<xml이름>.txt  (YOLO 정규화 좌표)

처리 흐름 (main)
  1) 옵션 · 설정 로드
  2) XML 파일마다: 이미지 크기 읽기 → object 마다 클래스 이름 확인 → 좌표 변환
  3) YOLO txt 저장, config 에 없는 클래스는 개수만 세서 경고

VOC XML 구조 (참고)
  <annotation>
    <size><width>640</width><height>480</height></size>
    <object>
      <name>car</name>
      <bndbox><xmin>10</xmin><ymin>20</ymin><xmax>110</xmax><ymax>220</ymax></bndbox>
    </object>
  </annotation>

사용 예:
  python scripts/02c_convert_voc_to_yolo.py --xml-dir data/labeled/xml
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from common import add_config_arg, banner, labeled_dirs, load_config, write_yolo_labels, xyxy_to_yolo


def main():
    """VOC XML 라벨을 읽어 YOLO txt 라벨로 변환·저장한다."""
    # ── 1) 옵션 · 설정 로드 ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--xml-dir", required=True, help="VOC XML 폴더")
    args = ap.parse_args()

    cfg = load_config(args.config)
    names = [n.lower() for n in cfg["classes"]]     # 클래스 이름은 대소문자 무시하고 비교
    _, labels_dir = labeled_dirs(cfg)               # 출력은 labels/ 폴더만 필요
    banner("2단계-보조", "VOC XML → YOLO txt 변환")

    # ── 2) XML 파일별 변환 ──
    unknown, converted = Counter(), 0               # unknown: config 에 없는 클래스 이름별 개수
    for xml in sorted(Path(args.xml_dir).rglob("*.xml")):
        root = ET.parse(xml).getroot()
        # findtext("size/width", "0"): 태그가 없으면 "0" → float 경유로 "640.0" 같은 값도 허용
        w = int(float(root.findtext("size/width", "0")))
        h = int(float(root.findtext("size/height", "0")))
        if not w or not h:                          # 크기를 모르면 정규화(0~1) 계산이 불가능
            print(f"  [SKIP] 크기 정보 없음: {xml.name}")
            continue
        boxes = []
        for obj in root.iter("object"):             # 이미지 안의 모든 객체
            name = (obj.findtext("name") or "").strip().lower()
            if name not in names:
                unknown[name] += 1
                continue
            bb = obj.find("bndbox")
            x1, y1, x2, y2 = (float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))
            # 픽셀 꼭짓점 좌표 → YOLO (cls, xc, yc, w, h) 정규화 좌표 (클래스 ID = config 순서)
            boxes.append(xyxy_to_yolo(names.index(name), x1, y1, x2, y2, w, h))
        # ── 3) 저장 ── (XML 파일 이름 = 이미지 이름이라고 가정)
        write_yolo_labels(labels_dir / f"{xml.stem}.txt", boxes)
        converted += 1

    print(f"  변환: {converted} 개 → {labels_dir}")
    if unknown:
        print(f"  [WARN] config 에 없는 클래스(무시됨): {dict(unknown)}")


if __name__ == "__main__":
    main()
