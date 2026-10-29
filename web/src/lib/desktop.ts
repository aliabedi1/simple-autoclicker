export type Settings = {
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
export type Step = { id: string; x: number; y: number; delay: number }
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
    data?.version !== 1 ||
    !Array.isArray(data.steps) ||
    data.steps.length === 0 ||
    data.steps.length > 1000
  )
    throw new Error("Choose a version 1 pattern with 1 to 1000 steps.")
  return data.steps.map((step: { x: unknown; y: unknown; delay: unknown }) => {
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
    return { ...step, id: crypto.randomUUID() } as Step
  })
}
