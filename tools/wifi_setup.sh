#!/usr/bin/env bash
# =====================================================================
#  Raspbot Wi-Fi 간편 설정 도구
#  - 대상: Raspberry Pi OS Bookworm 이상 (NetworkManager 사용)
#  - Bookworm 부터는 /etc/wpa_supplicant/wpa_supplicant.conf 를 읽지 않으므로
#    `wpa_cli -i wlan0 reconfigure` 가 FAIL 이 납니다. 이 스크립트를 쓰세요.
#
#  사용법
#    sudo bash wifi_setup.sh                 # 메뉴 화면 (가장 쉬움)
#    sudo bash wifi_setup.sh add "SSID" "비밀번호" [우선순위]
#    sudo bash wifi_setup.sh add "SSID"      # 비밀번호 없는(개방형) Wi-Fi
#    sudo bash wifi_setup.sh list            # 저장된 Wi-Fi 목록
#    sudo bash wifi_setup.sh status          # 현재 연결 상태
#    sudo bash wifi_setup.sh connect "이름"   # 저장된 Wi-Fi 로 지금 전환
#    sudo bash wifi_setup.sh delete "이름"    # 저장된 Wi-Fi 삭제
#    sudo bash wifi_setup.sh import          # 예전 wpa_supplicant.conf 내용 가져오기
#
#  환경변수: WIFI_IFACE(기본 wlan0), WIFI_COUNTRY(기본 KR)
# =====================================================================
set -u

IFACE="${WIFI_IFACE:-wlan0}"
COUNTRY="${WIFI_COUNTRY:-KR}"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant.conf"
LOG_FILE="/var/log/wifi_setup_last.log"
DEFAULT_PRIO=10

RED=$'\e[31m'; GRN=$'\e[32m'; YEL=$'\e[33m'; CYN=$'\e[36m'; BOLD=$'\e[1m'; RST=$'\e[0m'
info() { echo "${CYN}▶${RST} $*"; }
ok()   { echo "${GRN}✔${RST} $*"; }
warn() { echo "${YEL}⚠${RST} $*"; }
err()  { echo "${RED}✘${RST} $*" >&2; }
line() { echo "------------------------------------------------------------"; }

# ---------------------------------------------------------------------
# root 권한으로 다시 실행
# ---------------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
  exec sudo env WIFI_IFACE="$IFACE" WIFI_COUNTRY="$COUNTRY" bash "$0" "$@"
fi

ask_yn() {  # ask_yn "질문" [기본값 y|n]
  local q="$1" def="${2:-n}" a hint="[y/N]"
  [ "$def" = "y" ] && hint="[Y/n]"
  read -r -p "$q $hint " a
  a="${a:-$def}"
  [[ "$a" =~ ^[Yy] ]]
}

# ---------------------------------------------------------------------
# 사전 점검
# ---------------------------------------------------------------------
check_env() {
  if ! command -v nmcli >/dev/null 2>&1 || ! systemctl is-active --quiet NetworkManager; then
    err "NetworkManager 가 동작하지 않습니다."
    echo "   - Bookworm 이전(Buster/Bullseye) OS 라면 예전 방식(wpa_supplicant.conf)을 사용하세요."
    echo "   - Bookworm 인데 꺼져 있다면:  sudo systemctl enable --now NetworkManager"
    exit 1
  fi

  if ! nmcli -t -f DEVICE device status | grep -Fxq "$IFACE"; then
    err "무선 장치 '$IFACE' 를 찾을 수 없습니다. (nmcli device status 로 확인)"
    exit 1
  fi

  # Wi-Fi 국가 코드가 없으면 무선이 막혀(rfkill) 있는 경우가 많음
  if command -v raspi-config >/dev/null 2>&1; then
    local cur
    cur="$(raspi-config nonint get_wifi_country 2>/dev/null || true)"
    if [ -z "$cur" ]; then
      info "Wi-Fi 국가 코드가 비어 있어 '$COUNTRY' 로 설정합니다."
      raspi-config nonint do_wifi_country "$COUNTRY" >/dev/null 2>&1 || warn "국가 코드 설정 실패 (계속 진행)"
    fi
  fi
  if command -v rfkill >/dev/null 2>&1 && rfkill list wifi 2>/dev/null | grep -q "Soft blocked: yes"; then
    info "Wi-Fi 가 꺼져(rfkill) 있어 켭니다."
    rfkill unblock wifi
  fi
  nmcli radio wifi on >/dev/null 2>&1 || true
}

# 지금 누군가 Wi-Fi(wlan0) 를 통해 SSH 로 들어와 있는가? (전환하면 끊김)
ssh_over_wifi() {
  local ips
  ips="$(ip -o addr show dev "$IFACE" 2>/dev/null | awk '{split($4, a, "/"); print a[1]}')"
  [ -n "$ips" ] || return 1
  ss -tnH state established '( sport = :22 )' 2>/dev/null \
    | awk '{print $3}' | sed -E 's/^\[?//; s/\]?:[0-9]+$//; s/^::ffff://' \
    | grep -Fxq -f <(echo "$ips")
}

# ---------------------------------------------------------------------
# 저장된 Wi-Fi 프로필 조회
# ---------------------------------------------------------------------
wifi_profiles() {  # 한 줄에 하나씩 프로필 이름 출력
  nmcli -t -e no -f TYPE,NAME connection show | while IFS=: read -r type name; do
    [ "$type" = "802-11-wireless" ] && echo "$name"
  done
}

prop() { nmcli -g "$2" connection show "$1" 2>/dev/null; }

find_profile_by_ssid() {
  local n names=()
  mapfile -t names < <(wifi_profiles)
  for n in "${names[@]}"; do
    [ "$(prop "$n" 802-11-wireless.mode)" = "ap" ] && continue
    [ "$(prop "$n" 802-11-wireless.ssid)" = "$1" ] && { echo "$n"; return 0; }
  done
  return 1
}

PROFILES=()
list_saved() {
  PROFILES=()
  local n i=0 ssid mode ac prio active tag
  mapfile -t PROFILES < <(wifi_profiles)
  if [ ${#PROFILES[@]} -eq 0 ]; then
    warn "저장된 Wi-Fi 가 없습니다."
    return 1
  fi
  printf "${BOLD} %-3s %-22s %-22s %-6s %-8s %s${RST}\n" "번호" "프로필 이름" "SSID" "우선" "자동연결" "상태"
  for n in "${PROFILES[@]}"; do
    i=$((i + 1))
    ssid="$(prop "$n" 802-11-wireless.ssid)"
    mode="$(prop "$n" 802-11-wireless.mode)"
    ac="$(prop "$n" connection.autoconnect)"
    prio="$(prop "$n" connection.autoconnect-priority)"
    active="$(prop "$n" GENERAL.STATE)"
    tag=""
    [ "$mode" = "ap" ] && tag="${YEL}[핫스팟]${RST} "
    [ "$active" = "activated" ] && tag="${tag}${GRN}● 연결됨${RST}"
    [ "$ac" = "yes" ] && ac="켜짐" || ac="꺼짐"
    printf " %-3s %-22s %-22s %-6s %-8s %s\n" "$i)" "$n" "$ssid" "$prio" "$ac" "$tag"
  done
}

pick_profile() {  # 번호를 입력받아 PICKED 에 이름 저장
  PICKED=""
  list_saved || return 1
  local k
  read -r -p "번호 선택 (취소: Enter): " k
  [[ "$k" =~ ^[0-9]+$ ]] && [ "$k" -ge 1 ] && [ "$k" -le ${#PROFILES[@]} ] || return 1
  PICKED="${PROFILES[$((k - 1))]}"
}

# ---------------------------------------------------------------------
# 상태
# ---------------------------------------------------------------------
show_status() {
  line
  local state conn ip4
  state="$(nmcli -g GENERAL.STATE device show "$IFACE" 2>/dev/null)"
  conn="$(nmcli -g GENERAL.CONNECTION device show "$IFACE" 2>/dev/null)"
  ip4="$(nmcli -g IP4.ADDRESS device show "$IFACE" 2>/dev/null | head -1)"
  echo " 장치       : $IFACE"
  echo " 상태       : ${state:-알 수 없음}"
  echo " 연결 프로필: ${conn:-(없음)}"
  echo " IP 주소    : ${ip4:-(없음)}"
  if ping -c1 -W2 8.8.8.8 >/dev/null 2>&1; then
    ok "인터넷 연결 정상"
  else
    warn "인터넷에 연결되어 있지 않습니다."
  fi
  line
}

# ---------------------------------------------------------------------
# 프로필 저장 (있으면 수정, 없으면 새로 만듦) — 현재 연결은 끊지 않음
#   save_profile SSID PASS PRIO HIDDEN(yes|no) KEYMGMT(wpa-psk|sae|none) [AUTOCONNECT yes|no]
# ---------------------------------------------------------------------
SAVED_NAME=""
save_profile() {
  local ssid="$1" pass="$2" prio="$3" hidden="$4" km="$5" auto="${6:-yes}" name

  if [ "$km" != "none" ]; then
    local len=${#pass}
    if ! { [ "$len" -ge 8 ] && [ "$len" -le 63 ]; } && ! [[ "$pass" =~ ^[0-9A-Fa-f]{64}$ ]]; then
      err "비밀번호는 8~63자여야 합니다. (입력: ${len}자)"
      return 1
    fi
  fi

  if name="$(find_profile_by_ssid "$ssid")"; then
    info "기존 프로필 '$name' 을(를) 새 정보로 수정합니다."
  else
    name="$ssid"
    if nmcli connection show "$name" >/dev/null 2>&1; then name="${ssid}-wifi"; fi
    nmcli connection add type wifi ifname "$IFACE" con-name "$name" ssid "$ssid" >/dev/null \
      || { err "프로필 생성 실패"; return 1; }
  fi

  nmcli connection modify "$name" \
    802-11-wireless.ssid "$ssid" \
    802-11-wireless.mode infrastructure \
    802-11-wireless.hidden "$hidden" \
    connection.interface-name "$IFACE" \
    connection.autoconnect "$auto" \
    connection.autoconnect-priority "$prio" \
    ipv4.method auto || { err "프로필 수정 실패"; return 1; }

  if [ "$km" = "none" ]; then
    nmcli connection modify "$name" remove 802-11-wireless-security >/dev/null 2>&1 || true
  else
    nmcli connection modify "$name" wifi-sec.key-mgmt "$km" wifi-sec.psk "$pass" \
      || { err "보안 설정 실패"; return 1; }
  fi

  SAVED_NAME="$name"
  ok "저장 완료: '$name' (SSID: $ssid, 우선순위: $prio, 자동연결: $auto)"
}

# ---------------------------------------------------------------------
# 지금 연결 전환
# ---------------------------------------------------------------------
connect_now() {
  local name="$1"
  if ssh_over_wifi; then
    warn "지금 Wi-Fi 로 SSH 접속 중입니다. 전환하면 이 SSH 창은 끊어집니다."
    echo "   - 다시 접속:  ssh pi@$(hostname).local   (또는 공유기에서 새 IP 확인)"
    echo "   - 연결에 실패하면 저장된 다른 Wi-Fi 로 자동으로 다시 붙습니다."
    ask_yn "그래도 지금 전환할까요?" n || { info "전환하지 않았습니다. 재부팅하면 우선순위대로 연결됩니다."; return 0; }
    info "백그라운드에서 '$name' 으로 전환합니다... (결과: $LOG_FILE)"
    nohup nmcli --wait 40 connection up "$name" ifname "$IFACE" >"$LOG_FILE" 2>&1 &
    sleep 1
    return 0
  fi

  info "'$name' 에 연결 중... (최대 40초)"
  if nmcli --wait 40 connection up "$name" ifname "$IFACE"; then
    ok "연결 성공"
    show_status
  else
    err "연결 실패 — 비밀번호, SSID, 공유기 거리(신호)를 확인하세요."
  fi
}

# ---------------------------------------------------------------------
# 메뉴 1: 주변 Wi-Fi 검색해서 추가
# ---------------------------------------------------------------------
read_password() {  # PASS 변수에 저장 (두 번 입력 확인)
  local p1 p2
  while true; do
    read -r -s -p "비밀번호: " p1; echo
    read -r -s -p "비밀번호 확인: " p2; echo
    if [ "$p1" = "$p2" ]; then PASS="$p1"; return 0; fi
    warn "두 비밀번호가 다릅니다. 다시 입력하세요."
  done
}

add_interactive() {
  local rows=() ssids=() secs=() sigs=() r sig rest sec ssid i k
  while true; do
    info "주변 Wi-Fi 검색 중..."
    nmcli device wifi rescan ifname "$IFACE" >/dev/null 2>&1 || true
    sleep 2
    mapfile -t rows < <(nmcli -t -e no -f SIGNAL,SECURITY,SSID device wifi list ifname "$IFACE" 2>/dev/null | sort -t: -k1,1nr)
    ssids=(); secs=(); sigs=()
    declare -A seen=()
    for r in "${rows[@]}"; do
      sig="${r%%:*}"; rest="${r#*:}"; sec="${rest%%:*}"; ssid="${rest#*:}"
      [ -z "$ssid" ] || [ "$ssid" = "--" ] && continue
      [ -n "${seen[$ssid]:-}" ] && continue
      seen[$ssid]=1
      ssids+=("$ssid"); secs+=("$sec"); sigs+=("$sig")
    done
    unset seen

    line
    if [ ${#ssids[@]} -eq 0 ]; then
      warn "검색된 Wi-Fi 가 없습니다."
    else
      printf "${BOLD} %-4s %-30s %-6s %s${RST}\n" "번호" "SSID" "신호" "보안"
      for i in "${!ssids[@]}"; do
        printf " %-4s %-30s %-6s %s\n" "$((i + 1)))" "${ssids[$i]}" "${sigs[$i]}%" "${secs[$i]:-없음}"
      done
    fi
    line
    echo " h) 목록에 없는(숨김) SSID 직접 입력    r) 다시 검색    q) 취소"
    read -r -p "선택: " k
    case "$k" in
      q|Q|"") return 0 ;;
      r|R) continue ;;
      h|H)
        read -r -p "SSID (대소문자 정확히): " ssid
        [ -z "$ssid" ] && continue
        sec="?"; HIDDEN=yes
        break ;;
      *)
        if [[ "$k" =~ ^[0-9]+$ ]] && [ "$k" -ge 1 ] && [ "$k" -le ${#ssids[@]} ]; then
          ssid="${ssids[$((k - 1))]}"; sec="${secs[$((k - 1))]}"; HIDDEN=no
          break
        fi
        warn "잘못된 입력입니다." ;;
    esac
  done

  local km="wpa-psk"
  PASS=""
  if [ "$sec" = "" ] || [ "$sec" = "--" ]; then
    km="none"; info "'$ssid' 은(는) 비밀번호가 없는 Wi-Fi 입니다."
  elif [ "$sec" = "?" ]; then
    ask_yn "비밀번호가 있는 Wi-Fi 인가요?" y && read_password || km="none"
  else
    [[ "$sec" == *WPA3* && "$sec" != *WPA2* ]] && km="sae"
    read_password
  fi

  local prio
  read -r -p "우선순위 (숫자가 클수록 먼저 연결, 기본 $DEFAULT_PRIO): " prio
  [[ "$prio" =~ ^-?[0-9]+$ ]] || prio=$DEFAULT_PRIO

  save_profile "$ssid" "$PASS" "$prio" "$HIDDEN" "$km" || return 1
  PASS=""
  if ask_yn "지금 바로 '$ssid' 로 연결할까요?" n; then
    connect_now "$SAVED_NAME"
  else
    info "저장만 했습니다. 다음 부팅(또는 현재 Wi-Fi 끊김) 때 자동으로 연결됩니다."
  fi
}

# ---------------------------------------------------------------------
# 메뉴: 예전 wpa_supplicant.conf 의 network={...} 가져오기
# ---------------------------------------------------------------------
import_wpa_conf() {
  local file="${1:-$WPA_CONF}"
  if [ ! -f "$file" ]; then
    warn "$file 파일이 없습니다."
    return 1
  fi
  local US=$'\x1f' entries=() e ssid psk dis pri km hid auto kmode
  mapfile -t entries < <(awk -v US="$US" '
    /^[[:space:]]*network[[:space:]]*=[[:space:]]*\{/ { inb=1; ssid=psk=pri=km=""; dis=0; hid=0; next }
    inb && /^[[:space:]]*\}/ {
      inb=0
      if (ssid != "") print ssid US psk US dis US pri US km US hid
      next
    }
    inb {
      l=$0; sub(/^[[:space:]]+/, "", l); sub(/[[:space:]]+$/, "", l)
      if (l ~ /^#/ || index(l, "=") == 0) next
      k=substr(l, 1, index(l, "=") - 1); v=substr(l, index(l, "=") + 1)
      if (v ~ /^".*"$/) v=substr(v, 2, length(v) - 2)
      if (k=="ssid") ssid=v; else if (k=="psk") psk=v; else if (k=="disabled") dis=v
      else if (k=="priority") pri=v; else if (k=="key_mgmt") km=v; else if (k=="scan_ssid") hid=v
    }' "$file")

  if [ ${#entries[@]} -eq 0 ]; then
    warn "$file 에서 network={...} 항목을 찾지 못했습니다."
    return 1
  fi

  info "$file 에서 ${#entries[@]}개 네트워크를 찾았습니다:"
  for e in "${entries[@]}"; do
    IFS="$US" read -r ssid psk dis pri km hid <<<"$e"
    [ "$dis" = "1" ] && auto="꺼짐(disabled=1)" || auto="켜짐"
    printf "   - %-24s 자동연결: %s\n" "$ssid" "$auto"
  done
  ask_yn "NetworkManager 프로필로 가져올까요? (현재 연결은 끊기지 않습니다)" y || return 0

  for e in "${entries[@]}"; do
    IFS="$US" read -r ssid psk dis pri km hid <<<"$e"
    [ "$dis" = "1" ] && auto=no || auto=yes
    [[ "$pri" =~ ^-?[0-9]+$ ]] || pri=$DEFAULT_PRIO
    [ "$hid" = "1" ] && hid=yes || hid=no
    case "$km" in
      NONE) kmode=none ;;
      SAE)  kmode=sae ;;
      *)    kmode=wpa-psk; [ -z "$psk" ] && kmode=none ;;
    esac
    save_profile "$ssid" "$psk" "$pri" "$hid" "$kmode" "$auto" || warn "'$ssid' 가져오기 실패"
  done
  echo
  list_saved
}

# ---------------------------------------------------------------------
# 메뉴: 핫스팟(AP) 자동 시작 켜기/끄기
# ---------------------------------------------------------------------
toggle_hotspot() {
  local n found=0 ac names=()
  mapfile -t names < <(wifi_profiles)
  for n in "${names[@]}"; do
    [ "$(prop "$n" 802-11-wireless.mode)" = "ap" ] || continue
    found=1
    ac="$(prop "$n" connection.autoconnect)"
    if [ "$ac" = "yes" ]; then
      if ask_yn "핫스팟 '$n' 이(가) 부팅 시 자동으로 켜집니다. 자동 시작을 끌까요?" y; then
        nmcli connection modify "$n" connection.autoconnect no && ok "'$n' 자동 시작 끔 (다음 부팅부터 적용)"
        local others
        others="$(wifi_profiles | while IFS= read -r x; do
          [ "$(prop "$x" 802-11-wireless.mode)" != "ap" ] && [ "$(prop "$x" connection.autoconnect)" = "yes" ] && echo "$x"
        done)"
        if [ -z "$others" ]; then
          warn "자동 연결되는 일반 Wi-Fi 가 하나도 없습니다! 재부팅 전에 메뉴 1 로 Wi-Fi 를 먼저 추가하세요."
        fi
      fi
    else
      if ask_yn "핫스팟 '$n' 자동 시작이 꺼져 있습니다. 다시 켤까요?" n; then
        nmcli connection modify "$n" connection.autoconnect yes && ok "'$n' 자동 시작 켬 (다음 부팅부터 적용)"
      fi
    fi
  done
  [ "$found" -eq 1 ] || info "핫스팟(AP) 프로필이 없습니다."
}

# ---------------------------------------------------------------------
# 메뉴: 우선순위 변경 / 삭제
# ---------------------------------------------------------------------
change_priority() {
  pick_profile || return 0
  local p
  read -r -p "'$PICKED' 의 새 우선순위 (숫자가 클수록 먼저): " p
  [[ "$p" =~ ^-?[0-9]+$ ]] || { warn "숫자를 입력하세요."; return 0; }
  nmcli connection modify "$PICKED" connection.autoconnect-priority "$p" connection.autoconnect yes \
    && ok "'$PICKED' 우선순위 = $p"
}

delete_profile() {
  local name="${1:-}"
  if [ -z "$name" ]; then pick_profile || return 0; name="$PICKED"; fi
  nmcli connection show "$name" >/dev/null 2>&1 || { err "'$name' 프로필이 없습니다."; return 1; }
  if [ "$(prop "$name" GENERAL.STATE)" = "activated" ] && ssh_over_wifi; then
    warn "'$name' 은(는) 지금 SSH 가 사용 중인 연결입니다. 삭제하면 접속이 끊깁니다."
  fi
  ask_yn "'$name' 을(를) 삭제할까요?" n || return 0
  nmcli connection delete "$name" >/dev/null && ok "'$name' 삭제 완료"
}

# ---------------------------------------------------------------------
# 메인 메뉴
# ---------------------------------------------------------------------
menu() {
  while true; do
    echo
    echo "${BOLD}==========  Raspbot Wi-Fi 간편 설정  ==========${RST}"
    show_status
    echo " 1) 주변 Wi-Fi 검색해서 추가   ${CYN}← 처음이면 이것${RST}"
    echo " 2) 저장된 Wi-Fi 목록 보기"
    echo " 3) 저장된 Wi-Fi 로 지금 전환"
    echo " 4) 우선순위 바꾸기"
    echo " 5) 저장된 Wi-Fi 삭제"
    echo " 6) 예전 wpa_supplicant.conf 내용 가져오기"
    echo " 7) 핫스팟(AP) 자동 시작 켜기/끄기"
    echo " q) 종료"
    local c
    read -r -p "선택: " c
    case "$c" in
      1) add_interactive ;;
      2) list_saved ;;
      3) pick_profile && connect_now "$PICKED" ;;
      4) change_priority ;;
      5) delete_profile ;;
      6) import_wpa_conf ;;
      7) toggle_hotspot ;;
      q|Q) exit 0 ;;
      *) warn "잘못된 입력입니다." ;;
    esac
  done
}

# ---------------------------------------------------------------------
check_env
cmd="${1:-menu}"
case "$cmd" in
  menu) menu ;;
  status) show_status ;;
  list) list_saved ;;
  add)
    [ $# -ge 2 ] || { err "사용법: $0 add \"SSID\" [\"비밀번호\"] [우선순위]"; exit 1; }
    ssid="$2"; pass="${3:-}"; prio="${4:-$DEFAULT_PRIO}"
    [[ "$prio" =~ ^-?[0-9]+$ ]] || prio=$DEFAULT_PRIO
    if [ -z "$pass" ]; then km=none; else km=wpa-psk; fi
    save_profile "$ssid" "$pass" "$prio" no "$km" || exit 1
    info "현재 연결은 그대로입니다. 바로 전환하려면:  sudo bash $0 connect \"$SAVED_NAME\""
    ;;
  connect)
    [ $# -ge 2 ] || { err "사용법: $0 connect \"프로필이름\""; exit 1; }
    connect_now "$2" ;;
  delete)
    [ $# -ge 2 ] || { err "사용법: $0 delete \"프로필이름\""; exit 1; }
    delete_profile "$2" ;;
  import) import_wpa_conf "${2:-$WPA_CONF}" ;;
  -h|--help|help) sed -n '2,20p' "$0" ;;
  *) err "알 수 없는 명령: $cmd  (도움말: $0 help)"; exit 1 ;;
esac
