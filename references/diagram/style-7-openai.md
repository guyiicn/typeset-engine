# Style 7: OpenAI Official

Clean, modern aesthetic matching OpenAI's documentation and research diagrams — minimal but precise.

## Color Palette

```
Background:     #ffffff  (pure white)
Primary text:   #0d0d0d  (near black)
Secondary text: #6e6e80  (muted gray)
Border:         #e5e5e5  (light gray)

Accent colors (reserved):
Green accent:   #10a37f  (OpenAI brand green)
Blue accent:    #1d4ed8  (links, actions)
Orange accent:  #f97316  (highlights, warnings)
Gray accent:    #71717a  (secondary elements)
```

## Typography

```
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica Neue, sans-serif
font-size:   16px node labels, 13px descriptions, 12px arrow labels
font-weight: 600 for titles, 500 for labels, 400 for descriptions
letter-spacing: -0.01em (tight)
```

## Node Boxes

```xml
<!-- Standard node -->
<rect x="100" y="100" width="180" height="80" rx="8" ry="8"
      fill="#ffffff" stroke="#e5e5e5" stroke-width="1.5"/>

<!-- Accent node (with green left border) -->
<rect x="100" y="100" width="180" height="80" rx="8" ry="8"
      fill="#ffffff" stroke="#e5e5e5" stroke-width="1.5"/>
<rect x="100" y="100" width="4" height="80" rx="2" ry="2"
      fill="#10a37f"/>
```

## Arrows

```xml
<defs>
  <marker id="arrow-oai" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#71717a"/>
  </marker>
  <marker id="arrow-oai-green" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#10a37f"/>
  </marker>
</defs>

<line stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow-oai)"/>
<line stroke="#10a37f" stroke-width="1.5" marker-end="url(#arrow-oai-green)"/>
```

## Grouping Containers

```xml
<rect x="80" y="80" width="400" height="200" rx="8" ry="8"
      fill="none" stroke="#e5e5e5" stroke-width="1" stroke-dasharray="4,3"/>
<text x="90" y="97" fill="#6e6e80" font-size="12" font-weight="500">Group Label</text>
```

## SVG Template

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600" width="960" height="600">
  <style>
    text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
  </style>
  <defs>
    <marker id="arrow-oai" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#71717a"/>
    </marker>
  </defs>
  <rect width="960" height="600" fill="#ffffff"/>
  <!-- nodes, edges, labels -->
</svg>
```

## Design Philosophy

- **Minimalism**: White on white, only essential visual elements
- **Precision**: Thin strokes, rx=8, grid-aligned
- **Clarity**: Content-first, no visual noise
- **Brand**: `#10a37f` green used sparingly for primary flows
- Avoid: shadows, gradients, colorful fills, thick borders, decorative elements
