# AIR_BLAST V3 실제 적용 및 검증 기록 — 2026-11-12

## 원인과 변경
이전 검수 ZIP의 기본 extra_clips.json은 v1.1을 선택했고 START_V3_REVIEW.cmd만 별도 v3_clips.json을 활성화했다. 따라서 새 PNG 포함만으로 기본 실행이 바뀌지 않았다. 이번에는 extra_clips.json의 AIR_BLAST 하나만 V3에 연결하고 별도 manifest/구버전 렌더러/런타임 자산을 제거했다. 이전 앱이 실행 중이면 단일 인스턴스 정책으로 기존 앱이 응답하므로 트레이에서 종료 후 새 exe를 실행한다. 시작 로그에 활성 구현과 실제 effects.json 경로를 기록한다.

캐릭터 CHARGE/RELEASE/RECOVER 12장은 이전 v1.1과 바이트 동일하게 air_blast_v3/character에 보존했다. 이펙트는 CAST4/PROJECTILE6/DISSIPATE4/BACKDRAFT6/FLOW8 총28장 개별 PNG를 사용한다. 첫 네 분류는576×704, FLOW는2048×512 RGBA다. 시트/원본/검수GIF는 런타임에 넣지 않는다. 원본 ZIP/PNG는 수정하지 않았다.

FLOW는 비타일형 1개, 종횡비 유지, 화면 경계 클리핑, 넓은 화면의 남는 영역은 비움. 첫 발사에서 전체 유효 길이를 표시한다. 전경은 동일6장으로4개 독립 인스턴스를 구성했다. 시작 지연0/20/60/110ms, 배율.45/.28/.32/.24, 속도6/8/5/9 캐릭터키/초, 위상0/2/4/1. FLOW60ms/장, PROJECTILE70ms/장, FLOW 불투명도70%, 전경100%, 전방 총1.2초. FLOW 앵커(0,256), 다른 효과(288,352), 손 오프셋은 effects.json을 따른다. 좌측 시전은 전체 좌표계 반전이다. 종료/취소 시 타이머와 레이어를 정리한다. 드래그는 논리 위치만 갱신해 모션을 유지한다.

다중 전경을 위해 새 이미지는 필수가 아니다. 첨부 PNG는 BACKDRAFT05와 픽셀이 같아 새 전경으로 복사하지 않았다. 더 다양한 모양을 원하면 별도 variation을 추가할 수 있다.

## 동작 및 창 관리
모든 동작 살펴보기는 실제 frames 레지스트리에서 정상 로드되고 길이가 양수인 동작을 순서대로 구성한다. 미설치/빈 동작은 제외한다. 신규 테스트 동작도 UI 목록 수정 없이 포함됐다. 현재8종과 테스트용9번째를 검증했다.

Qt 창 플래그 변경으로 네이티브 창이 재생성되는 구간 이후와500ms 주기에 Z-order를 복원한다. 캐릭터/효과/설정 창을 대상으로 포커스를 빼앗지 않는 SetWindowPos를 사용한다. 선택 모니터의 전경 전체화면에서는 topmost를 해제한다. 일반 최대화 창은 전체화면으로 취급하지 않는다. 과거 간헐 현상의 정확한 발생 조건은 확정하지 못했으며 강제 강등 후 복구를 검증했다.
API 근거: https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-setwindowpos , https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shqueryusernotificationstate

## 검증 판정
- PASS: 자동 검사81개. 프레임 로드/순서/실제 알파/크기, 자연 길이, 최초 전체 전개, 좁고 넓은 화면, 독립 타이밍/다중 전경, 좌우/재시전/취소/정리, 드래그/일시정지, 미래 동작 자동 포함, 기존 동작 회귀.
- PASS: Windows 네이티브 소스 실행의 기본 V3 경로, 강제 Z-order 강등 후 드래그 모드 복원, 일반/최대화 창 스타일 정책,9종 순회 후 IDLE 및 효과 정리.
- 제한: 전경 테스트 창의 실제 포커스 획득은 실패했다. fullscreen 검사는 실제 네이티브 창 좌표/스타일과 Z-order를 사용했지만 전경 핸들을 주입했다. 실제 게임/영상 독점 전체화면, 사용자 포커스 전환 안정성은 미검증이다.
- FAIL(시각 품질): FLOW06 사각 잔상. WARNING: FLOW02/07 세부선/스타일, 생성 FLOW08 길이 및08→01 연결. 120px에서 FLOW 가시폭은 약769/794/783/770/782/675/790/585px다. 복제/확대로 결함을 숨기지 않았다. 시각 최종 승인 아님.
- 미검증: 사용자 실제 흰/검정/복합 앱 배경,100/125/150% 물리 DPI, 다중 모니터 이동, 실제 전체화면 및 장시간 클릭 통과/항상 위. 실제 재생 자료와 자동 검사를 별도로 판단한다.

## 버전 교체 및 롤백
기술별 활성 manifest는 하나만 둔다. 신규 자산 로드/기본 실행/회귀 검증 후 매핑을 바꾸고 과거 선택 메뉴/자동 목록/배포 자산을 제거한다. 시각 미승인은 명시적으로 남긴다. 향후 이미지 최종 승인은 FLOW06 교체와 FLOW08 연결 재검수 후 수행한다.
이전 정상 코드/자산은 Git ab242f13422f78b3773c894e5964cd2d98702ae7 전체 체크아웃으로 복구 가능하다. 별도 폴더에 해당 커밋을 체크아웃해 그 버전 빌드 절차로 재빌드한다. 새 코드에 옛 manifest만 덮어쓰면 안 된다. 사용자 settings.ini는 덮어쓰지 않는다. 다운로드 원본 AIR_BLAST_V3_REVIEW.zip도 보존했다.

## 변경 파일
prototype_v0_12: air_blast_v3.py, air_blast.py, animation.py, motion_preview.py, overlay.py, window_stack.py, settings_dialog.py, main.py, build_windows.py 및 관련 테스트/README.
assets/characters/aang: extra_clips.json, air_blast_v3/의 캐릭터12장과 효과28장/config. 과거 air_blast/, air_blast_v11/ 런타임 제거. PROJECT_PLAN.md 및 본 문서 갱신. 별도 TASKBAR_SCENERY_THEME_PLAN 로컬 작업은 이번 커밋 대상에서 제외한다.

## 배포 검사 추가 결과
새 ZIP을 별도 폴더에 다시 풀어 기본 경로로 --check-package --preview-air-blast를 실행했다. Qt 표시배율1/1.25/1.5 모두 종료코드0이며 물리 DPI 검증과 구분한다. QtCore DLL 로드 및12프레임/발사/IDLE 복귀/잔여효과 정리를 통과했다. 구버전 런타임 경로가 ZIP에 없음을 확인했고 사용자 settings.ini SHA-256은 검사 전후 동일했다.
Windows 재생은1모니터/실제DPR1.0, 우·좌·우3회, 합성 드래그로 확인했다. 네이티브 위젯 버퍼를 실제 시간으로 캡처하고 내보낼 때 배경을 합성했다. 효과 paint 평균0.353ms/p950.806ms, 작업 메모리 약147~149MB. 전체 앱 FPS 또는 장시간 누수 보증은 아니다.
배포 ZIP SHA-256: ef850e3f34e5f54e65536e5b80320c9dc166b819c83352fb6a86aa444b911d48.
