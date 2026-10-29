export type Settings = {
  action: Action
  key: string
  target_mode: string
  x: string
  y: string
  interval: string
  unit: string
  start_mode: string
  delay: string
  start_date: string
  clock: string
  stop_mode: string
  count: string
  end_date: string
  end_clock: string
}
export type Action = "left" | "right" | "middle" | "key"
export const ACTION_LABELS: Record<Action, string> = {
  left: "Left click",
  right: "Right click",
  middle: "Middle click",
  key: "Keyboard key",
}
export function isShortcut(value: string): boolean {
  const aliases: Record<string, string> = {
    escape: "esc",
    return: "enter",
    spacebar: "space",
    control: "ctrl",
    windows: "cmd",
    win: "cmd",
    super: "cmd",
    pgup: "page_up",
    pgdn: "page_down",
    arrowup: "up",
    arrowdown: "down",
    arrowleft: "left",
    arrowright: "right",
    plus: "+",
  }
  const parts = value.split("+").map((part) => {
    const lower = part.trim().toLowerCase()
    return aliases[lower] ?? lower
  })
  const modifiers = ["ctrl", "alt", "shift", "cmd"]
  const names = [
    ...modifiers,
    "enter",
    "space",
    "tab",
    "esc",
    "backspace",
    "delete",
    "insert",
    "home",
    "end",
    "page_up",
    "page_down",
    "up",
    "down",
    "left",
    "right",
    "caps_lock",
  ]
  const last = parts.at(-1) || ""
  return (
    parts.length <= 5 &&
    new Set(parts).size === parts.length &&
    parts.slice(0, -1).every((part) => modifiers.includes(part)) &&
    (names.includes(last) ||
      /^f(?:[1-9]|1\d|2[0-4])$/.test(last) ||
      (Array.from(last).length === 1 && !/\s|\p{C}/u.test(last)))
  )
}
export type Step = {
  id: string
  x: number
  y: number
  delay: number
  action: Action
  key: string
}
export type DesktopState = {
  settings: Settings
  pattern: Omit<Step, "id">[]
  running: boolean
  picking: boolean
  status: string
  completed: number
  limit: number | null
  next_in: number | null
  step: number | null
  selection: { id: string; x: number; y: number; nonce: string } | null
  platform: string
}
const fragment = new URLSearchParams(window.location.hash.slice(1)).get("token")
if (fragment) {
  sessionStorage.setItem("clicker-session", fragment)
  history.replaceState(null, "", window.location.pathname)
}
const token = fragment || sessionStorage.getItem("clicker-session") || ""
export async function api(
  action: string,
  payload: object = {}
): Promise<DesktopState> {
  const response = await fetch("/api/action", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Clicker-Token": token },
    body: JSON.stringify({ action, payload }),
    signal: AbortSignal.timeout(7000),
  })
  const result = await response.json()
  if (!response.ok)
    throw new Error(result.error || "The desktop action failed.")
  return result
}
export function decodePattern(text: string): Step[] {
  const data = JSON.parse(text)
  if (
    ![1, 2].includes(data?.version) ||
    !Array.isArray(data.steps) ||
    data.steps.length === 0 ||
    data.steps.length > 1000
  )
    throw new Error("Choose a version 1 or 2 pattern with 1 to 1000 steps.")
  return data.steps.map(
    (step: {
      x: unknown
      y: unknown
      delay: unknown
      action?: unknown
      key?: unknown
    }) => {
      if (
        !Number.isInteger(step?.x) ||
        !Number.isInteger(step?.y) ||
        typeof step?.delay !== "number" ||
        !Number.isFinite(step.delay) ||
        step.delay < 0.05 ||
        step.delay > 315360000
      )
        throw new Error(
          "Each step needs integer coordinates and a wait of at least 0.05 seconds."
        )
      const action = step.action ?? "left"
      const key = step.key ?? ""
      if (
        typeof action !== "string" ||
        !Object.hasOwn(ACTION_LABELS, action) ||
        typeof key !== "string" ||
        (action === "key" && !isShortcut(key))
      )
        throw new Error(
          "Choose a valid action and specify the keyboard key for keyboard steps."
        )
      return { ...step, action, key, id: crypto.randomUUID() } as Step
    }
  )
}
