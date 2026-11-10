# ComfyUI + Wan Animate 캐릭터 애니메이션 제작 가이드

> 작성: 2026-11-10  
> 상태: **ComfyUI CPU 모드 브라우저 접속 사용자 성공 보고 / Wan Animate 생성 미검증**  
> 적용 대상: Avatar Living in Desktop, Windows 데스크톱, Intel(R) Iris(R) Xe Graphics

## 1. 목적과 현재 결정

- 기존에 확정한 아앙 분위기의 2D 캐릭터 외형을 유지하면서 WALK, IDLE, 공격, 공기 제어 등의 애니메이션을 추가한다.
- **마스터 이미지와 기존 검수된 자산을 기준으로** 애니메이션을 제작한다.
- 간단한 호흡/눈 깜빡임/옷 흔들림은 Synfig를 활용한다.
- 걷기 등 큰 실루엣 변화는 기존 GPT 이미지 생성 방식 우선이라는 기존 결정 유지. Wan Animate는 **복잡한 동작의 시험 후보**이며 채택 전 실제 품질 검수 필요.
- 캐릭터 동작과 바람 등 효과를 가능하면 분리하고, 투명 PNG 시퀀스를 만들어 PySide6 앱에 적용한다.
- GitHub에는 문서만 반영. 사용자 로컬의 코드·이미지·ZIP 및 ComfyUI 모델을 임의 업로드하지 않는다.

## 2. 컴퓨터 환경과 오류

- OS: Windows
- GPU: Intel(R) Iris(R) Xe Graphics (사용자 확인)
- ComfyUI Desktop 설치 Python: 3.13.12 (첨부 로그 기준)
- 설치 위치(해당 사용자 환경):
  `C:\Users\kccistc\AppData\Local\Comfy-Desktop\ComfyUI-Installs\baromandu\ComfyUI`
- 최초 Desktop 기동 로그에 다음 메시지가 나타남:
  - `AssertionError: Torch not compiled with CUDA enabled`
  - `XPU device count is zero!`
  - `Windows fatal exception: access violation`, `0xc0000139`
- 해석: PyTorch/ComfyUI가 CUDA 장치를 기대했으나 사용할 수 없었고 Intel XPU도 감지하지 못함. DLL/드라이버 호환 문제의 상세 원인은 확정하지 않음.
- **해결 확인 범위**: 사용자가 PowerShell CPU 실행 후 브라우저 `http://127.0.0.1:8188` 접속에 성공한 것으로 보고함. 이미지 생성·Wan 구동·Desktop 앱 자체 복구는 아직 검증하지 않음.

## 3. 재실행 명령 (PowerShell)

ComfyUI Desktop 앱을 종료하고 PowerShell에서 실행한다.

```powershell
cd "C:\Users\kccistc\AppData\Local\Comfy-Desktop\ComfyUI-Installs\baromandu\ComfyUI"
& ".\.venv\Scripts\python.exe" -s ".\main.py" --cpu --disable-xformers
```

- 서버가 시작되면 **표시된 URL**에 접속한다(일반적으로 `http://127.0.0.1:8188`).
- `127.0.0.1`은 자신의 PC를 가리킨다. 브라우저 화면이 뜬다고 클라우드 GPU를 사용하는 것은 아니다.
- PowerShell 서버 프로세스를 닫으면 브라우저의 ComfyUI 연결도 끊어진다.
- 이 절의 `.venv`는 **ComfyUI 자체 Python 환경**이고 프로젝트 v0.12의 Python 3.11 가상환경과 다르므로 혼동하지 않는다.
- 향후 ComfyUI Desktop 재설치 또는 설치 폴더 변경 시 경로를 다시 확인한다.

### 선택: 바탕화면 실행 BAT

메모장에 아래 코드를 저장하고 파일 이름을 `ComfyUI_CPU_실행.bat`, 파일 형식을 '모든 파일'로 설정한다. 이 파일은 **로컬에만 생성**한다.

```bat
@echo off
cd /d "C:\Users\kccistc\AppData\Local\Comfy-Desktop\ComfyUI-Installs\baromandu\ComfyUI"
".venv\Scripts\python.exe" -s "main.py" --cpu --disable-xformers
pause
```

BAT 더블클릭 후 콘솔의 서버 URL을 브라우저에서 열면 된다. 종료는 콘솔에서 `Ctrl+C`. 자동으로 브라우저를 여는 기능은 필수가 아니며, 서버 기동 전 브라우저가 열리는 경합을 피하기 위해 이 예시는 수동 접속을 사용한다.

## 4. Wan Animate 실행 전략

### 현재 하드웨어 판단

Intel Iris Xe 환경에서 Wan2.2 Animate 14B를 로컬 CPU로 생성하는 것은 메모리·속도 측면에서 **현실적인 작업 방식으로 권장하지 않음**. CPU 모드 ComfyUI 성공과 Wan 모델 생성 가능성은 별개다.

### 실행 선택지

| 선택 | 장점 | 제약 |
| --- | --- | --- |
| 로컬 ComfyUI CPU | 기초 노드·워크플로 인터페이스 학습, 모델 없이 구조 확인 | 대형 영상 생성은 실용적이지 않음 |
| GPU 대여형 클라우드 ComfyUI | 같은 모델/워크플로 사용 가능, 노드·LoRA 등 제어 | GPU 시간·저장소 요금, 업로드 필요, 서비스별 제약 |
| 간편 웹 영상 생성 서비스 | 설치 간단 | 모델/LoRA/노드 통제, 참조 영상 입력, 저작권 관련 정책이 더 제한적일 수 있음 |

비용은 고정 요금으로 확정하지 않는다. GPU 기종, 사용시간, 스토리지, 영상 길이·프레임 수·해상도, 서비스 정책에 따라 변경된다. 클라우드에 실제 접속하기 전에 사용료와 종료 후 청구 정책을 확인한다.

참고:
- ComfyUI: https://www.comfy.org/download
- Wan Animate 설명: https://docs.comfy.org/tutorials/video/wan/wan2-2-animate
- 공식 워크플로 탐색: https://comfy.org/hub/workflows/?category=animate-characters
- ComfyUI 소스: https://github.com/comfyanonymous/ComfyUI

## 5. 다음 애니메이션 제작 실험 절차

1. **원본 확정**: 확정 마스터(측면 전신, 얼굴·의상·색·비율 기준)를 복제하여 참조 이미지로 사용. 기존 v0.12 에셋은 보존.
2. **짧은 동작 선택**: 첫 시험은 2초가량의 팔 올리기/공기 제어 준비 동작으로 한정. 제자리·고정 카메라, 전체 신체가 보이는 단순 배경의 참고 영상 준비.
3. **ComfyUI GPU 워크플로 준비**: 공식 Wan Animate 워크플로를 클라우드 GPU에서 불러오고, 해당 워크플로가 요구하는 정확한 모델·노드·버전을 확인하여 설치. 모델명/폴더를 추측해 대량 다운로드하지 않음.
4. **시험 설정**: 짧은 영상, 낮은 해상도, 적은 프레임 수부터 시작. 예시 목표 512×512/12FPS/24프레임이나 실제 지원 값은 워크플로 기준.
5. **실행 및 비교**: 캐릭터 참조 이미지 + 동작 참조 영상 사용. 얼굴, 허리띠 기준 하체 비율, 긴 상의, 바지/부츠, 색상, 카메라 위치, 손발 형태 유지 확인.
6. **프레임 추출**: 영상 생성이 완료되면 FFmpeg 예시:
   ```bash
   ffmpeg -i animation.mp4 -vf fps=12 frame_%03d.png
   ```
   이는 PNG 추출일 뿐 자동 배경 투명화는 아님. 배경 제거/크기 정렬/발 기준선 및 알파 가장자리 정리를 별도로 수행.
7. **게임 적용 전 검수**: 투명 RGBA, 이미지 크기, 앵커/접지, 프레임 간 흔들림, 첫↔끝 루프, 바람 이펙트 분리, 기존 IDLE/WALK 외형 전환 검수. 실기기 PySide6 재생까지 완료해야 적용 완료 판정.
8. **결과 기록**: GPU 종류, 워크플로·모델 버전, 영상 길이, 프레임 수, 생성 시간과 총 비용, 성공/실패 이미지 품질 기록. 실패한 초안은 적용하지 않는다.

### 권장 제작 난이도

- **간단**: 눈 깜빡임, 호흡, 가벼운 옷 흔들림 → Synfig 우선
- **중간**: 제자리 걷기, 팔 동작 → 실루엣/가려지는 팔다리 복원이 필요하여 검수 중요
- **어려움**: 공기 제어, 회전, 점프, 연속 전투 → 신체 각도·의상·손/발·효과 일관성 문제. Wan 시험 후보
- 영상 AI 생성 품질의 주요 리스크는 **외형 드리프트, 프레임 깜빡임, 부정확한 루프**. 클라우드 사용이 이를 자동으로 해결하지 않음.

## 6. 저작권 및 자료 관리

- 원작 캐릭터에 가까운 팬아트를 생성할 수 있는 것과 공개/배포/상업 활용 권리가 생기는 것은 별개다.
- 모델 라이선스, 클라우드 서비스 정책, 참고 영상·이미지 권리를 확인한다.
- 업로드 대상은 사용자가 권한을 가진 자료를 우선하고 민감한 원본의 외부 업로드를 피한다.

## 7. 검증 상태 체크리스트 (2026-11-10)

- [x] Windows + Intel Iris Xe GPU 확인 (사용자)
- [x] ComfyUI Desktop 기동 실패 로그 분석
- [x] PowerShell `--cpu --disable-xformers` 경로 제공
- [x] 사용자 CPU 서버 구동 및 localhost 브라우저 접속 성공 보고
- [ ] CPU 모드 기본 노드/간단한 생성 작업 확인
- [ ] BAT 런처 로컬 생성 및 재실행 확인
- [ ] 클라우드 GPU 선택 및 과금 검토
- [ ] Wan Animate 워크플로 실제 실행
- [ ] PNG 시퀀스 변환·루프·일관성 검수
- [ ] v0.12 앱 적용 및 실기기 검증

**현 상태: 환경 기동 우회 성공(사용자 보고), 애니메이션 생성 파이프라인은 시험 전.**
