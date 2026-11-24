"""
전체 파이프라인 일괄 실행기 (라벨링이 끝난 뒤의 단계를 순서대로 자동 실행)

  check(3) → split(4) → train(5) → validate(6, val) → final(6, test) → test(7) → export(9)

사람이 해야 하는 1~2단계(수집 정리, 라벨링)는 포함하지 않습니다.
각 단계가 실패하면 즉시 멈춥니다. 검증 FAIL(종료코드 2)은 경고만 하고 계속 진행합니다.

사용 예:
  python run_pipeline.py                                # 3~9단계 전체
  python run_pipeline.py --from train --to validate     # 일부만
  python run_pipeline.py --demo                         # 가상 데이터로 전체 흐름 체험 (5분 내외)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S = ROOT / "scripts"

STEPS = [
    ("check",    "3단계 라벨 점검",        [S / "03_check_labels.py", "--strict"]),
    ("split",    "4단계 데이터셋 분할",    [S / "04_split_dataset.py"]),
    ("train",    "5단계 학습",             [S / "05_train.py"]),
    ("validate", "6단계 검증 (val)",       [S / "06_validate.py", "--split", "val"]),
    ("final",    "6단계 최종 시험 (test)", [S / "06_validate.py", "--split", "test"]),
    ("test",     "7단계 운영조건 테스트",  [S / "07_test.py"]),
    ("export",   "9단계 배포 변환",        [S / "09_export.py"]),
]
KEYS = [k for k, _, _ in STEPS]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ROOT / "config.yaml"))
    ap.add_argument("--from", dest="start", default="check", choices=KEYS)
    ap.add_argument("--to", dest="end", default="export", choices=KEYS)
    ap.add_argument("--demo", action="store_true", help="가상 데이터셋 생성 후 config.demo.yaml 로 실행")
    args = ap.parse_args()

    if args.demo:
        args.config = str(ROOT / "config.demo.yaml")
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_demo_dataset.py"),
                        "--config", args.config], check=True)

    steps = STEPS[KEYS.index(args.start): KEYS.index(args.end) + 1]
    timeline = []
    for key, title, cmd in steps:
        print(f"\n▶▶▶ {title}  ({key})")
        t0 = time.time()
        rc = subprocess.run([sys.executable, *map(str, cmd), "--config", args.config]).returncode
        dt = time.time() - t0
        status = "OK" if rc == 0 else ("FAIL(기준 미달)" if rc == 2 else f"ERROR(rc={rc})")
        timeline.append((title, status, dt))
        if rc not in (0, 2):
            break

    print("\n" + "=" * 64 + "\n  파이프라인 요약\n" + "=" * 64)
    for title, status, dt in timeline:
        mark = "✅" if status == "OK" else ("⚠️ " if status.startswith("FAIL") else "❌")
        print(f"  {mark} {title:<24} {status:<16} {dt:7.1f}s")
    if any(s.startswith("ERROR") for _, s, _ in timeline):
        sys.exit(1)


if __name__ == "__main__":
    main()
