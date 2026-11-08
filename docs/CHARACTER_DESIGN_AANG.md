# 아앙 캐릭터 디자인 및 스프라이트 제작 계획

> 작성일: 2026-11-08  
> 대상: 이미지 기반 애니메이션 준비(v0.3 후보)  
> 상태: 디자인·제작 규격 수립 / 이미지 제작 및 앱 적용 전

## 1. 문서의 역할

프로젝트 목적, 오버레이 정책, 개발 단계와 실행 검증 현황은 [통합 기획서](../PROJECT_PLAN.md)를 따른다. 이 문서는 첫 캐릭터인 아앙의 **이미지 제작 기준·납품 목록·프롬프트**만 관리한다. 개발 구조와 진행 현황을 중복 기재하지 않는다.

이번 반영 범위는 Markdown 문서뿐이다. 아래 에셋 경로는 향후 제작물 배치 계획이며, 이미지·메타데이터·코드의 생성 또는 업로드 완료를 뜻하지 않는다.

## 2. 비주얼 기준

- 캐릭터: 아앙(Aang). 사용자가 선호하는 **최신 영화판 분위기**를 참고한다.
- 영화풍의 성숙하고 세련된 인상과 색감을 살리되, 작은 데스크톱 캐릭터에 맞게 단순화한 **2D 스프라이트**로 제작한다.
- 민머리와 파란 화살표 문양, 주황·노랑 계열 공기 유목민 승려 복장, 맑고 가벼운 표정과 실루엣을 유지한다.
- 전신이 보이는 **오른쪽 옆모습**을 기본으로 한다. 과한 원근·카메라 회전·극적인 조명은 피한다.
- 사실적인 배우 얼굴 재현보다 작게 표시했을 때의 식별성과 프레임 간 안정성을 우선한다.
- 왼쪽 방향은 초기에는 오른쪽 프레임의 좌우 반전을 전제로 한다. 좌우 비대칭 의상·문양이 중요해지면 별도 방향 제작을 검토한다.
- 초기 이미지에는 밴딩 효과, 소품, 배경 장식, 바닥 그림자를 넣지 않는다.

**레퍼런스 확정:** 현재 특정 영화 제목·개봉 연도·의상 버전은 지정하지 않았다. “최신 영화판”은 사용자 선호를 나타내는 디자인 방향이며, 특정 작품의 공개·개봉 사실을 뜻하지 않는다. 제작 시작 시 사용자가 선택한 참고 이미지와 작품/버전을 기록하고, 승인된 마스터를 이후 모든 프레임의 기준으로 고정한다.

## 3. 필요한 이미지 — 총 11장

| 구분 | 수량 | 파일명 | 역할 |
| --- | ---: | --- | --- |
| 마스터 레퍼런스 | 1 | `aang_master.png` | 외형·비율·색·시점의 기준. 런타임 애니메이션 프레임 수에서 제외 |
| IDLE | 4 | `idle_01.png` ~ `idle_04.png` | 제자리 호흡 대기 루프 |
| WALK | 6 | `walk_01.png` ~ `walk_06.png` | 오른쪽으로 걷는 동작 루프 |
| 합계 | **11** | 마스터 1 + 애니메이션 10 | 왼쪽 반전본·미리보기·시트는 수량에 포함하지 않음 |

### IDLE: 4프레임 루프

| 파일 | 동작 |
| --- | --- |
| `idle_01.png` | 편안한 기본 자세, 호흡 중립 |
| `idle_02.png` | 들숨 중간, 가슴·어깨가 아주 조금 올라감 |
| `idle_03.png` | 들숨 정점, 옷자락이 미세하게 반응 |
| `idle_04.png` | 날숨 중간, 기본 자세로 돌아가는 중 |

발 위치와 접지선을 고정한다. 04 → 01이 자연스럽게 이어지도록 하고, 과도한 상하 흔들림이나 새 동작을 추가하지 않는다.

### WALK: 6프레임 루프

오른쪽을 향한 **제자리 걷기**로 제작한다. 화면상의 수평 이동은 향후 앱이 처리한다.

| 파일 | 동작 |
| --- | --- |
| `walk_01.png` | 오른발 앞쪽 접지, 왼발 뒤쪽; 팔은 다리와 반대 |
| `walk_02.png` | 오른발에 체중이 실리며 몸이 약간 내려감, 왼발이 앞으로 이동 |
| `walk_03.png` | 왼발이 몸 아래를 지나 앞으로 나가는 통과 자세 |
| `walk_04.png` | 왼발 앞쪽 접지, 오른발 뒤쪽; 01의 반대 보행 단계 |
| `walk_05.png` | 왼발에 체중이 실리며 몸이 약간 내려감, 오른발이 앞으로 이동 |
| `walk_06.png` | 오른발이 몸 아래를 지나 앞으로 나가는 통과 자세 |

01과 04는 같은 오른쪽 시점에서 팔다리의 보행 단계만 바꾼다. 이미지를 좌우 반전해 만들지 않는다. 06 → 01의 연결을 확인하며, 마지막에 01 복제본을 추가하지 않는다.

## 4. 파일명과 폴더 구조

저장소 루트 기준의 계획 경로:

```text
assets/
└── characters/
    └── aang/
        ├── reference/
        │   └── aang_master.png
        ├── idle/
        │   ├── idle_01.png
        │   ├── idle_02.png
        │   ├── idle_03.png
        │   └── idle_04.png
        └── walk/
            ├── walk_01.png
            ├── walk_02.png
            ├── walk_03.png
            ├── walk_04.png
            ├── walk_05.png
            └── walk_06.png
```

영문 소문자와 두 자리 번호를 사용한다. 우선 개별 PNG로 관리하고 스프라이트 시트와 `meta.json`은 향후 구현 단계에서 필요할 때 별도로 정의한다.

## 5. 출력 규격과 일관성

- **실제 알파 채널이 있는 투명 PNG(RGBA)**. 흰색·체커보드를 이미지에 그려 넣은 가짜 투명 배경은 불가.
- 작업 규격 제안: 11장 모두 **512 × 512 px**, 동일 캔버스. 마스터 승인 전에 최종 확정한다.
- 모든 이미지의 캐릭터 크기, 수평 중심축, 발 접지선과 여백을 맞춘다. 걷기에 필요한 자연스러운 몸 높이 변화만 허용한다.
- 머리·손·발·옷자락이 잘리지 않도록 충분한 여백을 확보한다. 프레임별 자동 잘라내기나 개별 크기 맞춤은 하지 않는다.
- 얼굴, 머리 크기, 신체 비율, 화살표 위치·형태, 의상 구조, 색 팔레트, 선 두께, 명암과 광원을 마스터에 맞춘다.
- 배경, 글자, 프레임 번호, 워터마크, 테두리, 모션 블러, 잔상을 넣지 않는다.
- 각 PNG에는 캐릭터 1명과 동작 1개만 담는다. 비교용 시트는 최종 개별 프레임을 대체하지 않는다.
- 원본 크기와 실제 표시 예정 크기로 축소한 화면을 모두 확인한다. 투명 가장자리의 흰 테두리·색 번짐을 밝고 어두운 배경에서 검사한다.
- 루프를 순서대로 재생해 외형 튐, 발 미끄러짐, 위치 흔들림, 관절 오류, 마지막 → 첫 프레임 연결을 확인한다. 재생 속도는 실제 프리뷰에서 조정한다.

## 6. 제작 순서와 검수

1. 원하는 영화판 참고 이미지와 작품/버전을 선택하고 기록한다.
2. 마스터 1장을 만든 뒤 외형·오른쪽 시점·캔버스·크기·접지선을 승인한다.
3. 승인 마스터를 매번 첨부해 IDLE 01 → 04를 제작하고 호흡 루프를 확인한다.
4. 동일 마스터와 승인된 이전 프레임을 참고해 WALK 01 → 06을 제작한다. 접지 자세 01·04를 먼저 맞춘 뒤 중간 자세를 보완해도 된다.
5. 11장의 캔버스·정렬·알파 채널을 확인하고, 대기·걷기 루프와 왼쪽 반전 미리보기를 검수한다.
6. 파일명을 확정해 계획 폴더에 정리한다. 승인 후 별도 개발 작업으로 이미지 로딩과 상태 연결을 진행한다.

완료 조건: **마스터 1장 + IDLE 4장 + WALK 6장**이 규격과 루프 검수를 통과한 상태. 문서 작성만으로 이미지 제작이나 앱 실행 검증을 완료 처리하지 않는다.

## 7. 이미지 생성 프롬프트

### A. 마스터 레퍼런스

선택한 영화판 참고 이미지를 첨부해 사용한다. 처음에는 이 한 장만 생성하고, 승인된 결과를 후속 작업에 재사용한다.

```text
Create one master reference image of Aang for a desktop companion app.
Use the attached user-selected movie reference for the overall mood and costume cues.
Translate it into a clean, simplified 2D animation sprite with a mature, polished cinematic feeling and a clear silhouette readable at small size.
Full body, strict right-facing side view, relaxed neutral standing pose.
Bald head with the recognizable blue arrow tattoo, orange and yellow Air Nomad monk clothing, calm and lighthearted expression.
Consistent animation-ready proportions, clean outlines, restrained cel shading, fixed soft lighting, no dramatic perspective.
One character only, centered horizontally on a 512 x 512 canvas, generous margins, both feet on a clearly consistent baseline.
Export as a transparent RGBA PNG with a real alpha channel.
No background, floor shadow, effects, props, text, labels, watermark, checkerboard pattern, cropped limbs, or motion blur.
```

한국어 의도: 선택한 영화의 분위기를 작은 2D 캐릭터로 단순화하고, 전신 오른쪽 옆모습의 기본 자세를 만든다. 승인된 한 장을 외형 기준으로 사용한다.

### B. 모든 애니메이션 프레임에 붙일 공통 지시문

매 요청에 승인 마스터를 첨부하고, 아래 공통문과 C 또는 D의 **해당 프레임 동작 한 줄**을 함께 사용한다.

```text
Use the attached approved aang_master.png as the fixed character reference.
Create exactly ONE animation frame, not a sprite sheet or a collage.
Keep the same face, head size, body proportions, arrow tattoo, outfit construction, palette, outline thickness, shading, lighting, and strict right-facing side-view camera.
Use the same 512 x 512 canvas, character scale, horizontal center, ground baseline, and margins as the master.
Keep the character in place; do not translate it horizontally across the canvas.
Allow only the small body motion required by the specified animation phase.
Full body visible, no cropped limbs. Transparent RGBA PNG with real alpha.
No new accessories, effects, background, floor shadow, text, labels, watermark, blur, or ghost limbs.
Change only the pose described below.
```

### C. IDLE 프레임별 동작

각 행을 별도 요청으로 생성한다. 파일명은 저장 시 부여하며 이미지 안에 쓰지 않는다.

| 저장 파일 | 공통문 뒤에 붙일 프롬프트 |
| --- | --- |
| `idle_01.png` | Idle frame 1 of 4: relaxed neutral breathing pose, both feet planted, arms resting naturally, calm expression. |
| `idle_02.png` | Idle frame 2 of 4: gentle inhale halfway, chest and shoulders rise very slightly, feet remain exactly planted. |
| `idle_03.png` | Idle frame 3 of 4: gentle inhale at its peak, subtle chest lift and minimal cloth response, feet remain exactly planted. |
| `idle_04.png` | Idle frame 4 of 4: gentle exhale halfway back toward frame 1, suitable for a seamless return to the neutral pose, feet remain exactly planted. |

### D. WALK 프레임별 동작

캐릭터 본인의 오른발·왼발을 기준으로 한다. 카메라와 바라보는 방향은 6장 모두 동일하다.

| 저장 파일 | 공통문 뒤에 붙일 프롬프트 |
| --- | --- |
| `walk_01.png` | Walk frame 1 of 6: in-place right-facing walk, right foot forward at ground contact, left foot behind, left arm forward and right arm back. |
| `walk_02.png` | Walk frame 2 of 6: weight settles onto the right foot, body lowers slightly, left foot lifts from behind and swings forward, natural opposite arm swing. |
| `walk_03.png` | Walk frame 3 of 6: left leg passes under the body and begins moving ahead, right foot supports the body, body rises subtly, arms pass near the torso. |
| `walk_04.png` | Walk frame 4 of 6: left foot forward at ground contact, right foot behind, right arm forward and left arm back. Keep the same right-facing camera; do not mirror the image. |
| `walk_05.png` | Walk frame 5 of 6: weight settles onto the left foot, body lowers slightly, right foot lifts from behind and swings forward, natural opposite arm swing. |
| `walk_06.png` | Walk frame 6 of 6: right leg passes under the body and begins moving ahead, left foot supports the body, body rises subtly, arms pass near the torso. Prepare a seamless return to frame 1. |

### E. 수정용 공통 프롬프트

```text
Correct this single frame to match the attached approved master.
Preserve the requested animation phase.
Restore the exact character design, palette, proportions, right-facing camera, canvas size, scale, horizontal alignment, and ground baseline.
Fix malformed or extra limbs and remove any background pixels or edge halos.
Keep a real transparent alpha channel. Do not redesign the character or add details.
```

생성 결과는 프롬프트 준수 여부를 직접 확인한다. 한 번의 생성으로 외형 일관성·정렬·투명도·자연스러운 루프가 모두 확보됐다고 가정하지 않는다.
