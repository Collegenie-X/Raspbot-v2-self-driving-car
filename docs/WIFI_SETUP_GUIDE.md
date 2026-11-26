# 라즈베리 파이 와이파이 설정 가이드 (AP 모드 해제 및 외부 공유기 연결)

## 0. 가장 쉬운 방법: `wifi_setup.sh` (메뉴에서 번호만 고르기)

> **`sudo wpa_cli -i wlan0 reconfigure` 가 `FAIL` 이 나오나요?**
> Raspberry Pi OS **Bookworm** 부터는 Wi‑Fi 를 **NetworkManager** 가 관리하므로
> `/etc/wpa_supplicant/wpa_supplicant.conf` 를 고쳐도 반영되지 않습니다.
> 아래 스크립트를 쓰면 SSID 를 쉽게 추가할 수 있습니다.

### ① 스크립트를 라즈베리 파이로 복사 (내 PC/Mac 에서 실행 — **반드시 먼저!**)

```bash
scp tools/wifi_setup.sh pi@pi.local:~/
```

> `pi.local` 이 안 되면 Pi 의 IP 로 바꿔서 입력 (예: `pi@192.168.1.11`).
> 복사 전에 ②를 실행하면 `No such file or directory` 가 나옵니다.

### ② 라즈베리 파이에 접속해서 실행

```bash
ssh pi@pi.local
```

```bash
sudo bash ~/wifi_setup.sh
```

> 프롬프트가 `pi@pi:~ $` 인지 확인하세요. Mac 프롬프트에서 실행하면 Mac 비밀번호를 묻고 동작하지 않습니다.

```
==========  Raspbot Wi-Fi 간편 설정  ==========
 장치       : wlan0
 상태       : 100 (connected)
 연결 프로필: edu22
 IP 주소    : 192.168.1.11/24
✔ 인터넷 연결 정상
 1) 주변 Wi-Fi 검색해서 추가   ← 처음이면 이것
 2) 저장된 Wi-Fi 목록 보기
 3) 저장된 Wi-Fi 로 지금 전환
 4) 우선순위 바꾸기
 5) 저장된 Wi-Fi 삭제
 6) 예전 wpa_supplicant.conf 내용 가져오기
 7) 핫스팟(AP) 자동 시작 켜기/끄기
 q) 종료
```

**1번** → 주변 Wi‑Fi 목록에서 번호 선택 → 비밀번호 입력(2번) → 우선순위 입력(Enter 면 10) → 끝.

- **SSH 로 접속 중이어도 안전합니다.** 기본은 "저장만" 하고 지금 연결은 끊지 않습니다.
  재부팅하면 우선순위가 높은 Wi‑Fi 부터 자동 연결됩니다.
- 지금 바로 전환하면 SSH 가 끊어집니다. 새 네트워크에서 `ssh pi@<호스트이름>.local` 로 다시 접속하세요.
- 숨김 SSID 는 목록에서 `h` 를 눌러 직접 입력합니다.
- 이미 `wpa_supplicant.conf` 에 `network={...}` 를 적어 두었다면 **6번** 으로 한 번에 옮길 수 있습니다
  (`disabled=1` → 자동연결 꺼짐, `priority=` → 우선순위 로 그대로 변환).

### 한 줄 명령으로 쓰기 (수업 중 일괄 설정용)

```bash
sudo bash ~/wifi_setup.sh add "edu" "12345678" 20
```

```bash
sudo bash ~/wifi_setup.sh list
```

| 예전 `wpa_supplicant.conf` | 지금 (NetworkManager) |
| :--- | :--- |
| `network={ ssid=... psk=... }` 추가 | `wifi_setup.sh add "SSID" "비밀번호"` |
| `disabled=1` | `sudo nmcli connection modify 이름 connection.autoconnect no` (아예 지우려면 메뉴 5) |
| `priority=5` | 우선순위 (숫자 클수록 먼저) |
| `wpa_cli -i wlan0 reconfigure` | 필요 없음 (저장 즉시 반영, 전환은 메뉴 3) |

---

## 1. 설정 흐름도 (Flowchart)

```mermaid
flowchart TD
    Start[시작: 인터넷 연결 안됨] --> CheckMode{현재 모드 확인}
    CheckMode -- AP 모드 (공유기 역할) --> DeleteAP[기존 AP 설정 삭제]
    CheckMode -- Client 모드 --> ScanWifi[외부 공유기 검색]
    
    DeleteAP --> Reboot[재부팅]
    Reboot --> ScanWifi
    
    ScanWifi --> Method{연결 방법 선택}
    
    Method -- 방법 A: GUI --> ClickIcon[와이파이 아이콘 클릭]
    ClickIcon --> SelectSSID[SSID 선택 및 비번 입력]
    SelectSSID --> Connected[연결 완료]
    
    Method -- 방법 B: 터미널 --> Command[nmcli 명령어 입력]
    Command --> Connected
    
    Method -- 방법 C: 설정파일 --> OS{OS 버전 확인}
    OS -- 최신 (Bookworm 등) --> EditNM[NetworkManager 파일 생성]
    OS -- 구버전 (Buster 등) --> EditWPA[wpa_supplicant 수정]
    
    EditNM --> Reload[설정 로드 및 연결]
    EditWPA --> Reboot2[재부팅]
    
    Reload --> Connected
    Reboot2 --> Connected
```

---

## 2. 연결 방법 비교표

| 구분 | 방법 A: GUI 사용 (권장) | 방법 B: 터미널 (nmcli) | 방법 C: 설정 파일 (NetworkManager) | 방법 D: 구버전 (wpa_supplicant) |
| :--- | :--- | :--- | :--- | :--- |
| **난이도** | ⭐ (매우 쉬움) | ⭐⭐ (보통) | ⭐⭐⭐ (어려움) | ⭐⭐⭐ (어려움) |
| **추천 상황** | 모니터/마우스 연결 시 | 터미널/SSH 작업 시 | 대량 배포 / 자동화 필요 시 | 구형 OS 사용 시 |
| **특징** | 윈도우처럼 클릭으로 해결 | 한 줄 명령어로 깔끔함 | 파일로 설정 관리 가능 | 최신 OS에서 오동작 가능성 있음 |
| **비고** | 가장 직관적임 | 오타 주의 필요 | 권한(600) 설정 필수 | 레거시 방식 |

---

## 3. 단계별 상세 설정 가이드

### 1단계: 기존 핫스팟(AP) 설정 삭제하기

현재 라즈베리 파이가 공유기 역할(AP 모드)을 하고 있어 외부 와이파이를 잡지 못하는 상태입니다. 먼저 이 설정을 지워야 합니다.

> **⚠️ 주의:** 원격 접속 중이라면 설정 삭제 시 연결이 끊깁니다. 반드시 모니터/키보드를 연결하거나 유선 랜을 사용하세요.

1. **터미널 실행 및 명령어 입력**
   ```bash
   sudo rm /etc/NetworkManager/system-connections/Raspbot-9be2c8c5-d64b-42bf-9fbc-1decea417f7c.nmconnection
   ```
   *(팁: `sudo rm /etc/NetworkManager/system-connections/Raspbot*` 로 간략하게 입력 가능)*

2. **재부팅**
   ```bash
   sudo reboot
   ```

---

### 2단계: 외부 공유기 검색 및 연결

재부팅 후 AP 모드가 꺼지면 일반 와이파이 연결이 가능해집니다.

#### 방법 A: 바탕화면 UI에서 연결 (가장 쉬움)
1. 바탕화면 우측 상단 **와이파이 아이콘** 클릭
2. 연결하려는 **외부 와이파이 이름(SSID)** 선택
3. **비밀번호** 입력 후 연결 확인

#### 방법 B: 터미널 명령어로 연결 (nmcli)
UI 사용이 불가능한 경우 터미널에서 진행합니다.

1. **와이파이 목록 검색**
   ```bash
   nmcli device wifi list
   ```

2. **와이파이 연결 시도**
   ```bash
   sudo nmcli device wifi connect "와이파이이름" password "비밀번호"
   ```

---

### 3단계: 설정 파일을 통한 고급 설정 (필요시)

터미널 명령어가 잘 안 되거나, 설정 파일로 관리하고 싶은 경우 사용합니다.

#### 추천: NetworkManager 설정 파일 직접 생성 (최신 OS)

1. **파일 생성**
   ```bash
   sudo nano /etc/NetworkManager/system-connections/MyWifi.nmconnection
   ```

2. **내용 작성**
   ```ini
   [connection]
   id=MyWifi
   type=wifi
   interface-name=wlan0

   [wifi]
   mode=infrastructure
   ssid=연결할_와이파이_이름

   [wifi-security]
   key-mgmt=wpa-psk
   psk=와이파이_비밀번호

   [ipv4]
   method=auto
   
   [ipv6]
   method=auto
   ```

3. **권한 설정 및 적용 (필수)**
   ```bash
   sudo chmod 600 /etc/NetworkManager/system-connections/MyWifi.nmconnection
   sudo nmcli connection reload
   sudo nmcli connection up MyWifi
   ```

## 요약

1. **AP 모드 끄기**: 기존 설정 파일(`Raspbot...nmconnection`) 삭제 후 재부팅
2. **연결하기**: 바탕화면 아이콘 클릭 또는 `nmcli` 명령어 사용
3. **확인하기**: 인터넷 브라우저를 열어 접속 확인
