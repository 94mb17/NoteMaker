# NoteMaker

A gesture-driven document editor for Windows.

NoteMaker lets you build Microsoft Word documents using a radial menu instead of a traditional toolbar. Simply copy text, hold the mouse button, and choose how the content should be inserted.

Designed for quick note-taking, documentation, and report writing without interrupting your workflow.

## Features

- Circular radial menu interface
- Long-press mouse activation
- Clipboard integration
- Multiple heading levels (H1–H6)
- Paragraph insertion
- Multiple bullet styles
  - • Bullet
  - ○ Circle
  - ■ Square
  - ✓ Check
- Hyperlink insertion
- Screenshot capture
- Live HTML preview
- Save as `.docx`
- Append to existing Word documents
- Undo / Redo
- Automatic session recovery
- System tray integration



# Project Structure
```text
doced/
│
├── gui.py              
├── doced.py            
├── cache/
│   ├── cache.json
│   └── images/
│
└── README.md

```

# Workflow

                                    START
                                      │
                                      ▼
                             Launch Application
                                      │
                                      ▼
                     Create QApplication & Editor
                                      │
                                      ▼
                 Create cache/images directory if absent
                                      │
                                      ▼
                 Initialize System Tray + Mouse Listener
                                      │
                                      ▼
                         cache/cache.json exists?
                         │                     │
                      Yes                     No
                         │                     │
                         ▼                     ▼
          Show "Recover previous session?"    Continue
                 │                │
             Recover          Discard
                 │                │
                 ▼                ▼
        Cache.recover()     Delete cache folder
                 │
                 ▼
            Editor Ready
                 │
                 ▼


## Normal Operation
```text
═══════════════════════════════════════════════════════════════
                    NORMAL OPERATION
═══════════════════════════════════════════════════════════════

                 │
                 ▼
        Wait for mouse long press
                 │
        ┌────────┴────────┐
        │                 │
   Left Button       Right Button
        │                 │
        ▼                 ▼
Copy selected text  Copy selected text
(Ctrl+C simulated)  (Ctrl+C simulated)
        │                 │
        ▼                 ▼
 Read clipboard      Read clipboard
        │                 │
        ▼                 ▼
 Open Format Menu    Open Action Menu
        │
        ├──────────────────────────────────────┐
        │                                      │
        ▼                                      ▼
Formatting Commands                   Document Commands
        │                                      │
        ├─ Heading H1-H6                       ├─ Save
        ├─ Paragraph                           ├─ View
        ├─ Bullet                              ├─ Open
        ├─ Hyperlink                           ├─ Undo
        └─ Screenshot                          ├─ Redo
                                               └─ Quit
```
