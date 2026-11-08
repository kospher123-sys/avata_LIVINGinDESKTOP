# Avatar Living in Desktop

Windows 바탕화면 위에서 아앙이 걷고 쉬는 PySide6 데스크톱 아바타입니다.

## 최신 실행 버전: v0.6

Python 3.11 환경에서 저장소 루트의 PowerShell로 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r prototype_v0_6\requirements.txt
.\.venv\Scripts\python.exe prototype_v0_6\main.py --settings
```

이미 가상환경과 PySide6가 설치되어 있으면 마지막 실행 명령만 사용합니다.

- 투명 배경, 항상 위 표시, 기본 클릭 통과, 대기/걷기 애니메이션
- 기본 높이 120px, 크기/속도 실시간 미리보기와 사용자별 설정 저장
- 모니터 선택 및 자동 크기, 드래그 모드와 트레이 종료
- 선택적으로 켜는 생활 시간표: 기본 22:00~07:00 휴식(대기)

[v0.6 사용법](prototype_v0_6/README.md) · [통합 기획서](PROJECT_PLAN.md)

v0.3 움직임/이미지 및 v0.4 실시간 설정은 사용자 확인을 마쳤습니다. v0.5 다중 모니터는 모의 검사만 수행했고, 실기기 검사는 사용자 요청으로 보류했습니다. v0.6 시간표는 자동 검사를 통과했으며 사용자 검수는 남아 있습니다.

이전 프로토타입은 각 버전 폴더에 보존했습니다. 한 번에 하나의 버전만 실행하세요.
