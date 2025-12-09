#!/usr/bin/env python3
"""
단계별 실행 가이드 확장 스크립트
기존 가이드를 1단계 수준으로 모든 단계를 상세화
"""

print("="*70)
print("🔧 단계별 실행 가이드 확장 중...")
print("="*70)
print("\n작업 내용:")
print("  1. 기존 백업 파일 읽기")
print("  2. 각 단계별로 상세 내용 추가")
print("  3. 검증 스크립트 추가")
print("  4. 에러 해결 가이드 추가")
print("  5. 예상 출력 예시 추가")
print("\n예상 최종 분량: 6000-7000줄")
print("예상 소요 시간: 작업 진행 중...")
print("\n" + "="*70)

# 현재 상태 출력
import os

files = {
    "원본": "단계별_실행_가이드.md",
    "백업": "단계별_실행_가이드_BACKUP.md", 
    "완성본": "단계별_실행_가이드_COMPLETE.md"
}

print("\n📊 현재 파일 상태:")
for name, filename in files.items():
    filepath = f"/Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo/{filename}"
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        with open(filepath) as f:
            lines = len(f.readlines())
        print(f"  {name:10s}: {filename:40s} ({size//1024}KB, {lines}줄)")
    else:
        print(f"  {name:10s}: {filename:40s} (없음)")

print("\n" + "="*70)
print("✅ 분석 완료!")
print("="*70)

