"""Phase 1 라인 추종 실행 스크립트."""

from pathlib import Path
import sys

# 스크립트가 어디서 실행되든 프로젝트 루트(=raspbot 패키지 위치)를 import path에 포함
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspbot.runtime.phase1_baseline import main


if __name__ == "__main__":
    main()
