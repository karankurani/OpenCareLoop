# OpenCareLoop Brand

## The mark

**Torus knot (2,3)** — a single unbroken stroke woven into three lobes. The bright bead is the step you're on; it travels the whole loop and never lifts. One full lap = one care loop.

For OpenCareLoop those strands are **you**, **the agent**, and **your data**: distinct, but inseparable and always in motion. The loop has no beginning or end, which mirrors the product: care isn't a one-off answer, it's a cycle you keep running.

---

## Palette

| Name       | Hex       | Use                          |
| ---------- | --------- | ---------------------------- |
| Forest     | `#0E5C30` | Primary mark stroke, dark UI |
| Bright     | `#5BD17E` | The bead, accents            |
| Near-black | `#0C1410` | Hero backgrounds             |
| Ink        | `#14241B` | Body text on light           |
| Paper      | `#FFFFFF` | Reversed mark ground         |

---

## Stroke rules

- viewBox: `0 0 100 100`
- stroke-width: `6` at large sizes → `9.5` at or below 24px (favicon)
- Always `stroke-linecap="round"` + `stroke-linejoin="round"`, `fill="none"`

---

## Variants

| File                    | Stroke    | Bead                        | Use                                     |
| ----------------------- | --------- | --------------------------- | --------------------------------------- |
| `logomark-animated.svg` | `#0E5C30` | `#5BD17E` animated          | General use on light grounds, docs hero |
| `logomark-static.svg`   | `#0E5C30` | `#5BD17E` parked at (86,50) | Static contexts, emails, print          |
| `logomark-white.svg`    | `#ffffff` | `#5BD17E` parked            | Navbar, dark/forest backgrounds         |
| `logomark-mono.svg`     | `#14241B` | `#14241B`                   | Single-colour print, emboss             |
| `favicon.svg`           | `#0E5C30` | none, stroke-width 9.5      | Browser tab, app icon ≤24px             |

Clear space ≥ the height of one lobe on all sides. Below ~24px, drop the bead and let the knot read on its own; bump stroke weight to 8–9.5.

---

## Animation

- **Motion** — bead follows the path via SVG `animateMotion` + `mpath`
- **Timing** — 8s per lap, linear, loops forever (`repeatCount="indefinite"`)
- **Bead** — radius 5.5, fill `#5BD17E`; `rotate="auto"` keeps it true to the curve
- **Reduced motion** — under `prefers-reduced-motion: reduce`, park the bead at (86,50) and don't animate

---

## Copy-paste SVG (animated, forest on transparent)

```svg
<svg viewBox="0 0 100 100" width="120" height="120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OpenCareLoop">
  <path id="ocl-loop" fill="none" stroke="#0E5C30" stroke-width="6"
        stroke-linecap="round" stroke-linejoin="round"
        d="M86.0,50.0 L85.9,52.8 L85.4,55.6 L84.5,58.2 L83.4,60.8 L81.9,63.2 L80.2,65.4 L78.3,67.3 L76.1,69.0 L73.9,70.4 L71.5,71.6 L69.0,72.5 L66.5,73.1 L64.0,73.4 L61.5,73.4 L59.2,73.3 L56.9,72.9 L54.7,72.3 L52.7,71.6 L50.9,70.8 L49.2,69.9 L47.7,68.9 L46.4,67.9 L45.1,66.9 L44.1,65.9 L43.1,65.0 L42.2,64.2 L41.4,63.4 L40.6,62.7 L39.8,62.1 L39.0,61.6 L38.2,61.2 L37.3,60.8 L36.3,60.5 L35.2,60.1 L34.1,59.8 L32.8,59.4 L31.4,59.0 L29.9,58.4 L28.4,57.7 L26.8,56.9 L25.1,55.9 L23.5,54.7 L21.9,53.4 L20.3,51.8 L18.9,50.0 L17.5,48.0 L16.3,45.9 L15.4,43.5 L14.6,41.1 L14.2,38.5 L14.0,35.9 L14.1,33.2 L14.5,30.5 L15.2,27.8 L16.2,25.2 L17.6,22.8 L19.2,20.5 L21.1,18.5 L23.2,16.6 L25.6,15.1 L28.1,13.8 L30.7,12.9 L33.5,12.3 L36.3,12.0 L39.0,12.1 L41.8,12.5 L44.4,13.2 L47.0,14.2 L49.4,15.4 L51.6,16.9 L53.6,18.6 L55.3,20.5 L56.8,22.5 L58.1,24.6 L59.2,26.7 L60.0,28.9 L60.6,31.0 L60.9,33.1 L61.1,35.1 L61.2,37.0 L61.1,38.8 L60.9,40.5 L60.6,42.1 L60.3,43.5 L60.0,44.8 L59.8,46.0 L59.5,47.1 L59.3,48.1 L59.2,49.1 L59.2,50.0 L59.2,50.9 L59.3,51.9 L59.5,52.9 L59.8,54.0 L60.0,55.2 L60.3,56.5 L60.6,57.9 L60.9,59.5 L61.1,61.2 L61.2,63.0 L61.1,64.9 L60.9,66.9 L60.6,69.0 L60.0,71.1 L59.2,73.3 L58.1,75.4 L56.8,77.5 L55.3,79.5 L53.6,81.4 L51.6,83.1 L49.4,84.6 L47.0,85.8 L44.4,86.8 L41.8,87.5 L39.0,87.9 L36.3,88.0 L33.5,87.7 L30.7,87.1 L28.1,86.2 L25.6,84.9 L23.2,83.4 L21.1,81.5 L19.2,79.5 L17.6,77.2 L16.2,74.8 L15.2,72.2 L14.5,69.5 L14.1,66.8 L14.0,64.1 L14.2,61.5 L14.6,58.9 L15.4,56.5 L16.3,54.1 L17.5,52.0 L18.9,50.0 L20.3,48.2 L21.9,46.6 L23.5,45.3 L25.1,44.1 L26.8,43.1 L28.4,42.3 L29.9,41.6 L31.4,41.0 L32.8,40.6 L34.1,40.2 L35.2,39.9 L36.3,39.5 L37.3,39.2 L38.2,38.8 L39.0,38.4 L39.8,37.9 L40.6,37.3 L41.4,36.6 L42.2,35.8 L43.1,35.0 L44.1,34.1 L45.1,33.1 L46.4,32.1 L47.7,31.1 L49.2,30.1 L50.9,29.2 L52.7,28.4 L54.7,27.7 L56.9,27.1 L59.2,26.7 L61.5,26.6 L64.0,26.6 L66.5,26.9 L69.0,27.5 L71.5,28.4 L73.9,29.6 L76.1,31.0 L78.3,32.7 L80.2,34.6 L81.9,36.8 L83.4,39.2 L84.5,41.8 L85.4,44.4 L85.9,47.2 Z"/>
  <circle r="5.5" fill="#5BD17E">
    <animateMotion dur="8s" repeatCount="indefinite" rotate="auto">
      <mpath href="#ocl-loop"/>
    </animateMotion>
  </circle>
</svg>
```

For a static logo, remove the `<animateMotion>` block — the bead stays parked at (86,50). The path is identical at every size; only stroke-width and the bead change.
