// The small Display sheet (mobile v2 §4.6): light, dark, or whatever the phone says. Text size
// follows the iOS setting on its own (Dynamic Type), so there is no slider here.
import { Sheet } from "./Sheet";
import { THEME_CHOICES, useThemeChoice } from "./theme";

export function DisplaySheet({ onClose }: { onClose: () => void }) {
  const [choice, choose] = useThemeChoice();
  return (
    <Sheet title="Display" onClose={onClose} closeLabel="Done">
      <fieldset className="choices">
        <legend>Colours</legend>
        {THEME_CHOICES.map((option) => (
          <label key={option.value} className="choice">
            <input type="radio" name="theme" value={option.value} checked={choice === option.value} onChange={() => choose(option.value)} />
            <span>{option.label}</span>
          </label>
        ))}
      </fieldset>
      <p className="dim">Text size follows your phone's setting.</p>
    </Sheet>
  );
}
