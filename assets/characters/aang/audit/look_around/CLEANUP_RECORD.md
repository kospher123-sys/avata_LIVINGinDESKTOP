# 둘러보기 외곽 보정 기록

사용자 첨부 원본을 보존했다. 기본 내장 이미지 수정 도구로 두 차례 정리했으나 낮은 알파의 빨강/노랑 외곽이 남았다. 아래 두 도구 결과는 런타임에 사용하지 않는다. 이후 사용자가 Python 픽셀 보정을 명시적으로 승인하여 원본의 alpha<80 제거와 네 셀 분리를 수행했다.

최종 프레임: `assets/characters/aang/frames_look_around/look_around_01.png`~`look_around_04.png`.
원본: `assets/characters/aang/source/look_around/original_sheet.png`.
재현 코드: `prototype_v0_12/prepare_look_assets.py`.
측정 자료: 같은 폴더 `validation.json`.

총 67,404개의 낮은 알파 픽셀을 제거했다. alpha>=80으로 남긴 픽셀의 RGBA는 원본과 동일하며, PNG를 재개방해 확인했다. 원본 SHA-256은 변하지 않았다. 프레임은 362×1086이며 리사이즈/재그리기를 하지 않았다. 렌더링 단계에서 공통 배율과 프레임별 발 기준점을 사용한다. 눈으로 보이는 외곽만 보고 원래 알파를 정확히 복원했다고 주장하지 않는다.

## 도구 시도 1 프롬프트

```text
Edit the attached existing 4-frame sprite sheet for an adult male air monk desktop companion. This is cleanup and animation registration, NOT a redesign. Preserve the same adult identity, bald head, blue arrow tattoo, orange/gold robe, burgundy sash, brown boots, linework and cel shading. Preserve all FOUR distinct existing head/eye poses in their left-to-right order: (1) neutral right-facing profile, (2) glance slightly upward, (3) glance slightly downward, (4) neutral return. Keep the same torso, arms, hips, feet and garment shape across all frames; head/eyes may change only as already depicted. Remove ALL detached red/yellow color speckles, edge halos, glow and background contamination while keeping legitimate orange/yellow clothing. Use actual transparent RGBA alpha=0 outside the character, no visible background or checkerboard. Keep one horizontal row of FOUR equally spaced identical cells with no visible separators. Prefer exactly 1448x1086 pixels, four cells of 362x1086. Keep full-body same character scale in each cell, feet fully visible, generous transparent margin, common sole baseline 1074/1086 of cell height. Align the stationary boots, hips and torso to exactly the same local position in all four cells: no frame-dependent auto-fit, no enlarging individual poses, no body translation, no camera change. Frame 4 must return to frame 1's neutral pose for a seamless idle continuation. No added limbs, effects, floor shadow, text, labels, border or watermark. This is a clean usable 4-cell sprite atlas, not a presentation or collage.
```

## 도구 시도 2 프롬프트

```text
Technical alpha cleanup of this exact sprite atlas, no repainting. The image is 1448x1086 with four equal 362x1086 cells. It contains unwanted bright red/yellow contamination exclusively in very low alpha pixels. REMOVE ALL diffuse semitransparent particles and fringes: make every contamination pixel outside the main continuous figure fully transparent, especially isolated red speckles and edge reds near heads, wrists, robes and boots. Any exterior pixels with alpha below 80/255 should be fully transparent, not brighter or more saturated. Preserve the legitimate orange/yellow clothing and all high-opacity interior RGB, all anatomy, all four head poses, exact cell geometry and character placement. Do not add glow or shadows. Output a clean transparent RGBA PNG sprite sheet with the exact same dimensions, four cells and no text. This is a cutout/matte repair task only.
```
