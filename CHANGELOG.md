# Changelog

## [V5.9] - 2026-01-19
### Added
- **Session Logging:** Added a "Log This Shot" button. Users can now build a table of their shots during a single session to track trends.
- **Dynamic Yield Baseline:** When advising a Ratio Extension (for Sourness), the system now calculates the "Next Target" based on the *Actual Yield* (if the user already went long) rather than the original target. This prevents the system from suggesting a shorter shot to fix a sour one.

### Fixed
- **Temp Safety Enforcement:** If the user enters a temperature above the Safe Limit (e.g., 92°C for Dark Roast), the system now actively advises reducing it to the cap (91°C), even if the shot is Sour. It compensates for the lost heat by aggressively extending the Target Yield.

## [V5.7] - 2026-01-19
### Added
- **Dynamic Yield Targets:** The Wizard now explicitly calculates and displays a "Next Target Yield" (e.g., 40g) when Ratio adjustments are required.
- **Visual Feedback for Ratio Changes:** Added an `st.info` box that appears when the "Sour Fallback" logic is triggered, clearly instructing the user to "Extend shot to fix Sourness."

## [V5.6] - 2026-01-19
### Fixed
- **Sour Loop (Dead End):** Fixed logic where "Sour" shots at max temperature resulted in no advice. Now suggests "Increase Yield +2g" (Ratio change) to improve extraction without heat.
- **Dose Safety:** Reverted Dose Increment from +1.0g to +0.5g to prevent basket overfilling. Added specific warning to check Headroom (Razor Tool).

## [V5.5] - 2026-01-19
### Added
- **Logic Explanation Module:** Added an "Analysis" dropdown that explains the "Why" behind every adjustment (Grind, Dose, Temp, PI) in plain English.
- **Detailed Decaf Logging:** The analysis now explicitly states when Decaf safety caps are applied.
- **Yield Analysis:** Added explanation for why missing the target yield invalidates other flavor data.

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
