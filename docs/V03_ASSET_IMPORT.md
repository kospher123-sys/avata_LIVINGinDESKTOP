# v0.3 보정 에셋 반영 기록 — 2026-11-08

판정: **WARNING / 외곽 수정 및 Windows 애니메이션 검증 대기**.

## 반영 및 검증

- 이전 대화 첨부 `Avatar_Living_in_Desktop_v03_assets.zip`을 열어 선별했다. ZIP 내 해시 목록 20개 항목은 모두 실제 파일과 일치했다. 스크립트는 읽기 대상 해시 확인에만 포함되며 실행·업로드하지 않았다.
- IDLE 4장/WALK 6장을 각각 `idle/`, `walk/`에 배치했다. 실제 PNG를 디코딩하여 모두 296×444, alpha=0 픽셀 존재, alpha>0 최하단 Y=419임을 재확인했다. 수치는 `audit/v03/import_validation.json`에 기록했다.
- `spritesheet_6x2.png`는 1776×888의 보정 시트다. `previews/`의 어두운 배경 비교 PNG와 GIF 2개도 보존했다. GIF는 회색 배경의 검수용이며 투명 PNG를 대체하지 않는다. ZIP 검수 자료의 시간은 IDLE 320ms/WALK 120ms이며 이번 반영에서 시간 기반 재생 관찰은 수행하지 않았다.
- ZIP의 `validation.json`, `prior_measurements.json`, `package_hashes.json`, 보정 리포트를 `audit/v03/`에 원문 보존했다. 리포트의 경로 및 'GitHub 업로드 미수행'은 ZIP 작성 시점 기록이다. 현재 배치와 업로드 상태는 이 문서를 따른다.

## 원본 보존 및 선별

- ZIP 원본 마스터는 기존 `base_reference.png`와 SHA-256이 같아 중복 복사하지 않았다. 기존 확정 마스터를 유지한다. 과거 측정 JSON의 마스터 해시와 다르다는 원문 기록도 유지한다.
- ZIP 원본 시트(8345b47e…afda)는 기존 참고 시트(e38e9cc8…b7d)와 해시가 달라 `source/v03/original_sheet.png`로 별도 보존했다. 기존 `reference/idle_walk_sheet_draft.png`는 덮어쓰지 않았다.
- ZIP 전체와 `data/correct_assets.py`는 커밋하지 않았다. ZIP과 추출 원본은 로컬에 보존되며 처리 코드를 새로 업로드하지 않는다.
- `package_hashes.json`은 ZIP 내부 경로 기준의 원본 목록이다. 저장소 재배치 후의 파일 경로 목록이 아니며, 제외된 처리 스크립트 해시도 감사 이력으로 남아 있다.

## 남은 검수

배경 제거·프레임 10개 분리·공통 캔버스·세로 발 기준선 보정은 완료됐다. 단 alpha 최하단 정렬은 해부학적 발 접점 확정을 뜻하지 않는다. 몸통의 수평 위치는 원본 셀 기준이며 수동 앵커 확정은 남아 있다. 프리뷰에서 흰 점과 밝은 프린지가 보여 외곽 무결성 PASS로 판정하지 않는다.

외곽 수정, 팔·다리 접지 교대, 루프 자연스러움, 축소 표시·좌우 반전, IDLE/WALK 전환 및 Windows/PySide6 애니메이션 검증이 남아 있다. 코드 연결은 이번 작업 범위가 아니다. 항상 위에 표시와 클릭 통과 정책은 유지한다.

추가 생성 공통 조건: [스프라이트 품질 프롬프트](SPRITE_QUALITY_PROMPT.md).
