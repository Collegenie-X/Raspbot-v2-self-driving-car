# LabelImg 가이드

![LabelImg](/readme/images/labelimg.png)

## Label Studio - 최신 데이터 어노테이션 도구

LabelImg는 Tzutalin이 만들고 수많은 기여자들이 도운 인기 있는 이미지 어노테이션 도구였으나, 현재는 더 이상 활발하게 개발되지 않으며 Label Studio 커뮤니티의 일부가 되었습니다. 

이미지, 텍스트, 하이퍼텍스트, 오디오, 비디오 및 시계열 데이터를 위한 가장 유연한 오픈 소스 데이터 레이블링 도구인 [Label Studio](https://github.com/heartexlabs/label-studio)를 확인하세요. 

- [Label Studio 설치](https://labelstud.io/guide/install.html)
- [Slack 커뮤니티 가입](https://label-studio.slack.com/)

![Label Studio Screenshot](/readme/images/label-studio-1-6-player-screenshot.png)

---

## LabelImg 소개

![PyPI version](https://img.shields.io/pypi/v/labelimg.svg)
![Build Status](https://img.shields.io/github/workflow/status/tzutalin/labelImg/Package?style=for-the-badge)

**다국어 지원:**
- ![English](https://img.shields.io/badge/lang-en-blue.svg) [English](https://github.com/tzutalin/labelImg)
- ![中文](https://img.shields.io/badge/lang-zh-green.svg) [中文](https://github.com/tzutalin/labelImg/blob/master/readme/README.zh.rst)
- ![日本語](https://img.shields.io/badge/lang-jp-green.svg) [日本語](https://github.com/tzutalin/labelImg/blob/master/readme/README.jp.rst)

### 주요 특징

LabelImg는 그래픽 이미지 어노테이션 도구입니다.

- **개발 언어:** Python
- **GUI 프레임워크:** Qt
- **지원 포맷:** 
  - PASCAL VOC XML 형식 ([ImageNet](http://www.image-net.org/)에서 사용)
  - YOLO 형식
  - CreateML 형식

### 스크린샷

![Demo 1](https://raw.githubusercontent.com/tzutalin/labelImg/master/demo/demo3.jpg)

![Demo 2](https://raw.githubusercontent.com/tzutalin/labelImg/master/demo/demo.jpg)

### 데모 영상

[데모 영상 보기](https://youtu.be/p0nR2YsCY_U)

---

## 설치 방법

### 1. PyPI에서 설치 (Python 3.0 이상)

가장 간단한 설치 방법입니다. Ubuntu, Fedora 등 최신 Linux 배포판에서 사용 가능합니다.

```bash
pip3 install labelImg
labelImg
labelImg [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

### 2. 소스에서 빌드

#### 시스템 요구사항

- **최소:** Python 2.6 + PyQt 4.8
- **권장:** Python 3 이상 + PyQt5

---

#### Ubuntu Linux

**Python 3 + Qt5 설치:**

```bash
sudo apt-get install pyqt5-dev-tools
sudo pip3 install -r requirements/requirements-linux-python3.txt
make qt5py3
python3 labelImg.py
python3 labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

---

#### macOS

**Python 3 + Qt5 설치:**

```bash
# Homebrew로 Qt 설치
brew install qt  # qt-5.x.x 설치
brew install libxml2

# 또는 pip 사용
pip3 install pyqt5 lxml

# 빌드 및 실행
make qt5py3
python3 labelImg.py
python3 labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

**Python 3 Virtualenv 사용 (권장):**

Virtualenv를 사용하면 Qt/Python 버전 충돌을 피할 수 있습니다.

```bash
brew install python3
pip3 install pipenv
pipenv run pip install pyqt5==5.15.2 lxml
pipenv run make qt5py3
pipenv run python3 labelImg.py

# [선택사항] .app 파일 생성
rm -rf build dist
pipenv run python setup.py py2app -A
mv "dist/labelImg.app" /Applications
```

**참고:** 마지막 명령어는 새로운 SVG 아이콘이 포함된 .app 파일을 /Applications 폴더에 생성합니다.  
스크립트 사용: `build-tools/build-for-macos.sh`

---

#### Windows

**필수 프로그램 설치:**
1. [Python](https://www.python.org/downloads/windows/)
2. [PyQt5](https://www.riverbankcomputing.com/software/pyqt/download5)
3. [lxml](http://lxml.de/installation.html)

**설치 및 실행:**

```bash
# LabelImg 디렉토리로 이동 후
pyrcc4 -o libs/resources.py resources.qrc
# PyQt5의 경우:
pyrcc5 -o libs/resources.py resources.qrc

# 실행
python labelImg.py
python labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

**EXE 파일로 패키징:**

```bash
pip install pyinstaller
pyinstaller --hidden-import=pyqt5 --hidden-import=lxml -F -n "labelImg" -c labelImg.py -p ./libs -p ./
```

---

#### Windows + Anaconda

1. [Anaconda](https://www.anaconda.com/download/#download) 다운로드 및 설치 (Python 3+)
2. Anaconda Prompt를 열고 LabelImg 디렉토리로 이동

```bash
conda install pyqt=5
conda install -c anaconda lxml
pyrcc5 -o libs/resources.py resources.qrc
python labelImg.py
python labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

---

### 3. Docker 사용

```bash
docker run -it \
  --user $(id -u) \
  -e DISPLAY=unix$DISPLAY \
  --workdir=$(pwd) \
  --volume="/home/$USER:/home/$USER" \
  --volume="/etc/group:/etc/group:ro" \
  --volume="/etc/passwd:/etc/passwd:ro" \
  --volume="/etc/shadow:/etc/shadow:ro" \
  --volume="/etc/sudoers.d:/etc/sudoers.d:ro" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  tzutalin/py2qt4

make qt4py2;./labelImg.py
```

모든 의존성이 설치된 이미지를 pull 할 수 있습니다.  
[Docker 데모 영상](https://youtu.be/nw1GexJzbCI)

---

## 사용 방법

### PascalVOC 형식 사용 단계

1. 위의 설명대로 빌드 및 실행
2. Menu/File에서 'Change default saved annotation folder' 클릭
3. 'Open Dir' 클릭
4. 'Create RectBox' 클릭
5. 마우스 왼쪽 버튼을 클릭하고 드래그하여 영역 선택
6. 마우스 오른쪽 버튼으로 박스를 복사하거나 이동 가능

어노테이션은 지정한 폴더에 저장됩니다.

아래의 단축키를 사용하면 작업 속도를 높일 수 있습니다.

---

### YOLO 형식 사용 단계

1. `data/predefined_classes.txt` 파일에 학습에 사용할 클래스 목록 정의

2. 위의 설명대로 빌드 및 실행

3. 툴바의 "Save" 버튼 아래에 있는 "PascalVOC" 버튼을 클릭하여 YOLO 형식으로 전환

4. Open/OpenDIR을 사용하여 단일 또는 여러 이미지 처리. 이미지 작업이 끝나면 저장 클릭

YOLO 형식의 txt 파일이 이미지와 같은 폴더에 같은 이름으로 저장됩니다. "classes.txt" 파일도 해당 폴더에 저장되며, 이 파일은 YOLO 레이블이 참조하는 클래스 이름 목록을 정의합니다.

**주의사항:**

- 이미지 목록을 처리하는 중에는 레이블 목록을 변경하지 마세요. 이미지를 저장하면 classes.txt도 업데이트되지만, 이전 어노테이션은 업데이트되지 않습니다.

- YOLO 형식으로 저장할 때는 "default class" 기능을 사용하지 마세요. 참조되지 않습니다.

- YOLO 형식으로 저장할 때 "difficult" 플래그는 무시됩니다.

---

### 사전 정의된 클래스 생성

[data/predefined_classes.txt](https://github.com/tzutalin/labelImg/blob/master/data/predefined_classes.txt) 파일을 편집하여 사전 정의된 클래스를 로드할 수 있습니다.

---

### 어노테이션 시각화

1. 기존 레이블 파일을 이미지와 같은 폴더에 복사합니다. 레이블 파일명은 이미지 파일명과 같아야 합니다.

2. File을 클릭하고 'Open Dir'을 선택한 후 이미지 폴더를 엽니다.

3. File List에서 이미지를 선택하면 해당 이미지의 모든 객체에 대한 바운딩 박스와 레이블이 표시됩니다.

**(View에서 Display Labels 모드를 선택하여 레이블 표시/숨김 가능)**

---

## 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl + u` | 디렉토리의 모든 이미지 로드 |
| `Ctrl + r` | 기본 어노테이션 저장 폴더 변경 |
| `Ctrl + s` | 저장 |
| `Ctrl + d` | 현재 레이블과 박스 복사 |
| `Ctrl + Shift + d` | 현재 이미지 삭제 |
| `Space` | 현재 이미지를 검증됨으로 표시 |
| `w` | 사각형 박스 생성 |
| `d` | 다음 이미지 |
| `a` | 이전 이미지 |
| `del` | 선택한 박스 삭제 |
| `Ctrl + +` | 확대 |
| `Ctrl + -` | 축소 |
| `↑ → ↓ ←` | 선택한 박스를 화살표 방향으로 이동 |

---

### 이미지 검증 (Verify Image)

Space 키를 누르면 이미지를 검증됨으로 표시할 수 있으며, 녹색 배경이 나타납니다.  
이는 데이터셋을 자동으로 생성할 때 사용되며, 사용자는 모든 사진을 확인하고 어노테이션 대신 플래그를 지정할 수 있습니다.

---

### Difficult 플래그

difficult 필드가 1로 설정되면 객체가 "어려움"으로 어노테이션되었음을 나타냅니다. 예를 들어, 명확하게 보이지만 상당한 맥락 없이는 인식하기 어려운 객체입니다.  
딥 뉴럴 네트워크 구현에 따라 학습 중에 difficult 객체를 포함하거나 제외할 수 있습니다.

---

## 설정 초기화

클래스 로딩에 문제가 있는 경우 다음 중 하나를 수행하세요:

1. LabelImg 상단 메뉴에서 Menu/File/Reset All 클릭
2. 홈 디렉토리에서 `.labelImgSettings.pkl` 파일 제거
   - Linux/Mac: `rm ~/.labelImgSettings.pkl`

---

## 기여 방법

Pull Request를 보내주세요.

---

## 라이선스

[MIT License](https://github.com/tzutalin/labelImg/blob/master/LICENSE)

**인용:**  
Tzutalin. LabelImg. Git code (2015). https://github.com/tzutalin/labelImg

---

## 관련 도구 및 추가 리소스

1. [Label Studio](https://github.com/heartexlabs/label-studio) - 이미지, 텍스트, 오디오, 비디오 및 시계열 데이터를 머신러닝과 AI를 위해 레이블링

2. [ImageNet Utils](https://github.com/tzutalin/ImageNet_Utils) - 이미지 다운로드, 머신러닝을 위한 레이블 텍스트 생성 등

3. [Docker로 LabelImg 실행](https://hub.docker.com/r/tzutalin/py2qt4)

4. [PASCAL VOC TFRecord 파일 생성](https://github.com/tensorflow/models/blob/4f32535fe7040bb1e429ad0e3c948a492a89482d/research/object_detection/g3doc/preparing_inputs.md#generating-the-pascal-voc-tfrecord-files)

5. [앱 아이콘 출처](https://www.elegantthemes.com/) - Icon by Nick Roach (GPL)

6. [VSCode에서 Python 개발 환경 설정](https://tzutalin.blogspot.com/2019/04/set-up-visual-studio-code-for-python-in.html)

7. [iHub 플랫폼의 프로젝트 링크](https://code.ihub.org.cn/projects/260/repository/labelImg)

8. [어노테이션 파일을 CSV 또는 Google Cloud AutoML 형식으로 변환](https://github.com/tzutalin/labelImg/tree/master/tools)

---

## 인기도 추이

![Stargazers over time](https://starchart.cc/tzutalin/labelImg.svg)
