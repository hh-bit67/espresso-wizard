# Changelog

## [V5.4] - 2026-01-19
### Added
- **PI Time Input:** Added field to capture Pre-Infusion duration (seconds).
- **Roast Date Toggle:** Users can now uncheck "Know Roast Date?" to skip age logic.
- **Target Reference:** Added text showing calculated Target Yield next to the input.

### Fixed
- **Yield Input Bug:** Stopped the "Yield Out" field from auto-resetting when Dose was changed. It now behaves as a static input field.
- **Harsh Logic:** Split harshness logic to distinguish between Light Roast (Temp/Prep) and Dark Roast (Prep only).

## [V5.3] - 2026-01-18
### Changed
- **Dose Logic:** Increased "Up-Dose" suggestion from +0.5g to +1.0g for watery shots.
- **Decaf Safety:** Re-introduced 92°C temperature cap for all Decaf beans.
- **Bean Age:** Tightened "Stale" threshold from 45 days to 30 days.

### Added
- **Sensitivity Override:** Added slider to manually tune grind sensitivity (0.5x - 1.5x).
- **Viscosity Warning:** Added logic to warn that temperature changes may affect flow rate.

## [V5.1] - 2026-01-18
- Initial release of Peer-Reviewed Logic.
- Implemented Non-Linear Grind Sensitivity.
- Implemented Hardware Constraints (86-96°C).
