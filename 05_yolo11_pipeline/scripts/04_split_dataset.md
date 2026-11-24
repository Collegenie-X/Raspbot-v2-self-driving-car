(venv) kimjongphil@kimjongphilui-Mac-Studio scripts % python 04_split_dataset.py --config config.demo.yaml                

================================================================
  [4단계] 데이터셋 분할 (train / val / test) + data.yaml
================================================================
  분할 방식: 클래스 층화 | 미라벨 제외: 0 장
  클래스            train     val    test
  0:car             60      14       8
  1:green           56      13       8
  2:oo              71      17      12
  3:red             63      18      13
  4:xx              60      21       8
  이미지 수           169      47      24

  data.yaml: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/dataset/data.yaml
  다음 단계 → python scripts/05_train.py

  