# 4. Interaction Design

## 4.1 Core Interaction Patterns

### Direct Manipulation
- **Drag & Drop**: Parameters between configs, strategies to compare
- **Inline Editing**: Double-click any value to edit
- **Gestural Controls**: Pinch to zoom charts, swipe between results

### Predictive Assistance
- **Smart Defaults**: Learn from usage patterns
- **Auto-complete**: Strategy names, parameter values
- **Suggested Actions**: "Users who ran this also..."

### Responsive Feedback
- **Micro-animations**: Button states, loading indicators
- **Progress Communication**: Not just %, but meaningful stages
- **State Persistence**: Never lose work, auto-save everything

## 4.2 Keyboard-First Design
```
Essential Shortcuts:
Cmd+K     → Command palette
Cmd+Enter → Run backtest
Cmd+D     → Duplicate config
Cmd+/     → Toggle help
Space     → Play/pause execution
Esc       → Cancel/close
Tab       → Navigate fields
```

## 4.3 Error Prevention & Recovery
- **Validation**: Real-time, inline with helpful messages
- **Confirmation**: Only for destructive actions
- **Undo/Redo**: Full history with Cmd+Z/Cmd+Shift+Z
- **Auto-recovery**: Resume interrupted backtests
