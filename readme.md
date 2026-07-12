# Khushi AI Assistant

Khushi is a modular voice assistant with memory, skills, and intent-based routing.

## Features
- Voice input and output
- Persistent memory
- Time and date skills
- App launcher
- Google search
- System monitoring
- Calculator skill
- Weather skill with provider abstraction
- Notes skill with persistent note storage

## Calculator Skill
You can ask Khushi to calculate expressions such as:
- 2+2
- 5*8
- 20/4
- (2+3)*4
- percentage-based expressions

## Weather Skill
Weather requests are routed through a provider abstraction. By default, if no provider is configured, Khushi replies:
- Weather service is not configured.

## Notes Skill
You can ask Khushi to:
- take note <content>
- remember this note <content>
- show notes
- delete notes

Notes are stored in memory/notes.json.

## File Search Skill
You can ask Khushi to:
- find resume
- locate report.pdf

These searches scan common user folders such as Desktop, Documents, Downloads, and Pictures.

## Screenshot Skill
You can ask Khushi to:
- take screenshot
- capture screen

Screenshots are saved inside the screenshots/ directory.

## Clipboard Skill
You can ask Khushi to:
- copy
- paste
- show clipboard

## Volume and Brightness Skills
You can ask Khushi to:
- increase volume
- decrease volume
- mute
- increase brightness
- decrease brightness
- current brightness
