# v0.9 — 복구·오류 기록·Windows 배포 준비

소스로 실행:

```powershell
.\.venv\Scripts\python.exe prototype_v0_9\main.py --settings
```

## 추가한 기능

- Windows 절전 복귀 알림과 긴 타이머 간격/시계 변경을 감지하여 화면·배율·작업 영역·시간표를 다시 확인합니다. 복구 중에도 숨김/일시정지 선택을 유지합니다.
- 화면 밖으로 벗어난 설정 창을 다시 접근 가능한 위치로 옮깁니다. 복귀 후 대기 시간을 이동량으로 합산하지 않습니다.
- 트레이의 **문제 기록 폴더 열기**에서 app.log를 확인합니다. UTF-8 로그는 약 1MB씩 최대 4개를 유지합니다. 자동 전송하지 않습니다.
- 예상하지 못한 오류는 기록하고 안내 후 앱을 종료합니다. 중복 실행 보호 잠금은 해제하며 다시 실행할 수 있습니다.
- 이전 크기/속도/시간표 설정, 휴식 이미지 대체, 일시정지/숨기기 기능은 유지합니다. 요일별 시간표는 추가하지 않습니다.

## Windows 실행 파일

```powershell
.\.venv\Scripts\python.exe -m pip install -r prototype_v0_9\requirements-dev.txt
.\.venv\Scripts\python.exe prototype_v0_9\build_windows.py
```

결과는 `dist/AangOverlay-v0.9/AangOverlay-v0.9.exe`입니다. **폴더 전체**를 함께 보관/배포해야 하며 실행 파일만 따로 옮기면 안 됩니다. 실행 파일 옆 assets/characters/aang 폴더에 동작별 PNG가 있으므로 이미지를 추가한 뒤 다시 불러올 수 있습니다. 설정·로그는 Windows 사용자 폴더에 저장합니다.

기존 소스 버전과 동시에 실행하지 마세요. v0.8 이후 소스/실행 파일은 같은 사용자 실행 잠금을 사용합니다. 이미지 원본 참고 자료·검수 자료·사용자 설정·로그는 배포 폴더에 복사하지 않습니다.

## 검사

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s prototype_v0_9 -v
.\.venv\Scripts\python.exe prototype_v0_9\soak_check.py --seconds 600 --output reports/soak-v0.9.json
```

자원 검사는 임시 설정과 별도 화면 환경(Qt offscreen)을 사용하여 실제 사용자 설정을 바꾸지 않습니다. 걷기·정지·숨기기·복구·설정 창 열기/닫기를 반복하고 메모리·CPU·핸들 수를 기록합니다. `--seconds 28800`이면 8시간 검사입니다. 자동 검사를 실제 바탕화면의 하루 사용, 실제 절전 또는 다중 모니터 검증과 동일하게 보지 않습니다.

`--quit-after 5` 실행 옵션은 실행 파일의 자동 시작/종료 검사에 사용할 수 있습니다.

## 참고

- [PyInstaller 실행 경로 설명](https://pyinstaller.org/en/stable/runtime-information.html)
- [Windows 절전 복귀 알림](https://learn.microsoft.com/en-us/windows/win32/power/pbt-apmresumeautomatic)
- 휴식 이미지 파일 규격은 저장소의 docs/REST_ASSET_IMPORT.md 또는 배포 폴더의 REST_ASSET_IMPORT.md를 참고합니다.
