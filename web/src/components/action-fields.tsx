import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ACTION_LABELS, type Action } from "@/lib/desktop"

export function ActionFields({
  id,
  action,
  keyboardKey,
  onAction,
  onKey,
  disabled = false,
}: {
  id: string
  action: Action
  keyboardKey: string
  onAction: (action: Action) => void
  onKey: (key: string) => void
  disabled?: boolean
}) {
  return (
    <FieldGroup>
      <Field data-disabled={disabled}>
        <FieldLabel htmlFor={`${id}-action`}>Action</FieldLabel>
        <Select
          value={action}
          onValueChange={(value) => onAction(value as Action)}
          disabled={disabled}
        >
          <SelectTrigger id={`${id}-action`} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {Object.entries(ACTION_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </Field>
      {action === "key" && (
        <Field data-disabled={disabled}>
          <FieldLabel htmlFor={`${id}-key`}>Key or shortcut</FieldLabel>
          <Input
            id={`${id}-key`}
            value={keyboardKey}
            disabled={disabled}
            placeholder="enter, space, ctrl+s"
            onChange={(e) => onKey(e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
          <FieldDescription>
            Use a character, Enter, Space, Tab, Esc, arrows, F1–F24, or a
            shortcut like ctrl+shift+s. Keys go to the focused app; use the
            start delay to switch to it.
          </FieldDescription>
        </Field>
      )}
    </FieldGroup>
  )
}
