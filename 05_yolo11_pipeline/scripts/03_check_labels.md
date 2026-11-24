venv) kimjongphil@kimjongphilui-Mac-Studio scripts % python 03_check_labels.py --config config.demo.yaml

================================================================
  [3단계] 라벨 품질 점검
================================================================
  전체 이미지 240 | 라벨 완료 240 | 미라벨 0 | 배경(빈 라벨) 20 | 이미지 없는 라벨 0

  클래스        박스수  이미지수  평균크기   분포
  0:car            82       70     3.7%   █████
  1:green          77       67     1.8%   █████
  2:oo            100       88     1.9%   ██████
  3:red            94       85     1.8%   ██████
  4:xx             89       72     1.9%   ██████

  ERROR 0 건 | WARN 0 건

  리포트: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/reports/label_check.md
  미리보기: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/reports/label_preview  ← 박스 위치가 맞는지 눈으로 확인하세요
  다음 단계 → python scripts/04_split_dataset.py
(venv) kimjongphil@kimjongphilui-Mac-Studio scripts % 