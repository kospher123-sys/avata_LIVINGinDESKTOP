# 재사용 가능한 스프라이트 기술 품질 프롬프트

마스터 확정 후 애니메이션 생성 요청에 아래 공통 조건과 해당 프레임 동작을 함께 사용한다. 텍스트 마스터 → 마스터 검수·확정 → 애니메이션 → 검수 → 로컬 적용 순서를 따른다.

```text
Mandatory Sprite Technical Quality Requirements
- Generate a true transparent PNG with alpha = 0 outside the character.
- Do not render white or black backgrounds, checkerboard patterns, paper textures, or simulated transparency.
- No visible grid lines, separators, or cell borders.
- No red, yellow, or white halos outside the character silhouette.
- Preserve clean anti-aliased edges without background color contamination.
- Every animation frame must have an identical canvas size and consistent character scale.
- Maintain a stable torso reference position and a common ground baseline.
- Preserve natural arm and leg movement; do not center the entire changing silhouette artificially.
- Do not resize the character independently in different frames.
- Keep the full character inside each frame, with enough margins for extended walking poses.
- Maintain identical anatomy, adult proportions, facial features, clothing construction, and color palette.
- Keep the approved camera direction and lighting consistent.
- Ensure the final frame transitions naturally into the first frame.
- Verify the actual alpha channel; visual appearance alone does not establish transparency.
- If true transparency cannot be generated or inspected, explicitly report that limitation. Do not simulate transparency with a solid or patterned background or claim an unperformed check passed.
```

## 납품·검수 기준

- 현재 아앙 보정 프레임: 296×444 PNG, IDLE 4장/WALK 6장. 공통 기준점 (148,419), 좌상단 원점. 다른 캐릭터는 승인된 규격으로 치환한다.
- RGBA 표기만으로 통과시키지 않는다. 배경 alpha=0과 반투명 외곽을 실제 측정한다.
- 흰색·검정·중간 회색 배경에서 외곽을 확인하고 정상 의상 색을 halo와 구분한다.
- 공통 배율·몸통 기준 위치·지면선, 접지 교대, 발 미끄러짐, 얼굴·의상 일관성, 마지막→첫 프레임을 검수한다.
- GIF 생성·디코딩, 시간 기반 재생 관찰, 실제 Windows 오버레이 검증은 각각 구분해 기록한다. 검증 불가능한 항목은 미검증으로 남긴다.
