# 5. Visual Design System

## 5.1 Design Tokens
```css
/* Semantic Color System */
--color-profit: #10b981;     /* Green for gains */
--color-loss: #ef4444;       /* Red for losses */
--color-neutral: #6b7280;    /* Gray for no change */
--color-primary: #3b82f6;    /* Blue for actions */
--color-warning: #f59e0b;    /* Amber for warnings */
--color-surface: #1f2937;    /* Dark surface */
--color-background: #111827; /* Darker background */

/* Typography Scale */
--font-mono: 'JetBrains Mono', monospace;  /* Data */
--font-sans: 'Inter', sans-serif;          /* UI */

/* Spacing Rhythm */
--space-unit: 4px;  /* All spacing multiples of 4 */

/* Animation Timing */
--duration-instant: 100ms;
--duration-fast: 200ms;
--duration-normal: 300ms;
--easing-default: cubic-bezier(0.4, 0, 0.2, 1);
```

## 5.2 Component Patterns

### Cards with Status
```
┌─────────────────────────┐
│ ● Status    Actions ⋮  │  ← Status indicator + quick actions
├─────────────────────────┤
│ Primary Info            │  ← Most important data large
│ Secondary Details       │  ← Supporting info smaller
│ ▓▓▓▓▓▓░░░░ 60%        │  ← Visual progress
└─────────────────────────┘
```

### Data Tables
- Frozen columns for context
- Sortable headers with indicators
- Row highlighting on hover
- Inline actions on row hover
- Virtualized for performance

### Charts
- Consistent color coding across all views
- Interactive tooltips with details
- Zoom/pan with preview
- Export as image/data
- Annotations layer

## 5.3 Responsive Behavior
- **1920px+**: Full desktop, all panels visible
- **1440px**: Slightly condensed, maintain all features
- **1280px**: Minimum supported, some panels collapse
- **< 1280px**: Show warning, provide mobile message
