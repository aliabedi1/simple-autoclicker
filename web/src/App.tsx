import { useCallback, useEffect, useRef, useState } from "react"
import {
  ArrowDown,
  ArrowUp,
  CalendarClock,
  Check,
  CircleAlert,
  Clock3,
  Crosshair,
  Download,
  Loader2,
  Monitor,
  Moon,
  MousePointer2,
  Pencil,
  Play,
  Plus,
  Power,
  Repeat2,
  Route,
  ShieldCheck,
  Square,
  Sun,
  Trash2,
  Upload,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useTheme } from "@/components/theme-provider"
import {
  api,
  decodePattern,
  type DesktopState,
  type Settings,
  type Step,
} from "@/lib/desktop"

const initial: Settings = {
  target_mode: "single",
  x: "0",
  y: "0",
  interval: "1",
  unit: "seconds",
  start_mode: "delay",
  delay: "3",
  start_date: "",
  clock: "",
  stop_mode: "count",
  count: "1",
  end_date: "",
  end_clock: "",
}
type Draft = {
  id: string
  x: string
  y: string
  delay: string
  editing: boolean
}
function duration(seconds: number | null | undefined) {
  const n = Math.max(0, Math.ceil(seconds || 0))
  return [Math.floor(n / 3600), Math.floor(n / 60) % 60, n % 60]
    .map((n) => String(n).padStart(2, "0"))
    .join(":")
}

export default function App() {
  const [form, setForm] = useState(initial)
  const [steps, setSteps] = useState<Step[]>([])
  const [desktop, setDesktop] = useState<DesktopState | null>(null)
  const [connected, setConnected] = useState(false)
  const [pending, setPending] = useState(false)
  const [closed, setClosed] = useState(false)
  const [error, setError] = useState("")
  const [draft, setDraft] = useState<Draft | null>(null)
  const [draftError, setDraftError] = useState("")
  const [fileNotice, setFileNotice] = useState("")
  const initialized = useRef(false)
  const lastSelection = useRef("")
  const fileInput = useRef<HTMLInputElement>(null)
  const { theme, setTheme } = useTheme()
  const pattern = form.target_mode === "pattern"
  const busy = Boolean(
    desktop?.running || desktop?.picking || pending || !connected || closed
  )

  const accept = useCallback((state: DesktopState) => {
    setDesktop(state)
    setConnected(true)
    if (!initialized.current) {
      initialized.current = true
      setForm(state.settings)
      setSteps(state.pattern.map((s) => ({ ...s, id: crypto.randomUUID() })))
    }
    if (state.selection && state.selection.nonce !== lastSelection.current) {
      lastSelection.current = state.selection.nonce
      const selection = state.selection
      if (selection.id === "single")
        setForm((f) => ({
          ...f,
          x: String(selection.x),
          y: String(selection.y),
        }))
      else
        setDraft((d) =>
          d?.id === selection.id
            ? { ...d, x: String(selection.x), y: String(selection.y) }
            : d
        )
    }
  }, [])

  useEffect(() => {
    if (closed) return
    let active = true
    let timer: ReturnType<typeof setTimeout>
    async function poll() {
      try {
        const state = await api("state")
        if (active) accept(state)
      } catch (cause) {
        if (active) {
          setConnected(false)
          setError(
            cause instanceof Error
              ? cause.message
              : "App disconnected. Reopen the launcher."
          )
        }
      }
      if (active) timer = setTimeout(poll, 350)
    }
    void poll()
    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [accept, closed])

  const action = useCallback(
    async (name: string, payload: object = {}) => {
      setPending(true)
      setError("")
      try {
        const state = await api(name, payload)
        if (name === "quit") {
          setClosed(true)
          return
        }
        accept(state)
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Could not complete the action."
        )
      } finally {
        setPending(false)
      }
    },
    [accept]
  )

  useEffect(() => {
    function stop(event: KeyboardEvent) {
      if (
        event.key === "Escape" &&
        !draft &&
        (desktop?.running || desktop?.picking)
      )
        void action("stop")
    }
    window.addEventListener("keydown", stop)
    return () => window.removeEventListener("keydown", stop)
  }, [action, desktop?.running, desktop?.picking, draft])

  function change(name: keyof Settings, value: string) {
    setForm((f) => ({ ...f, [name]: value }))
  }
  function newDraft(step?: Step) {
    setDraftError("")
    setDraft({
      id: step?.id || crypto.randomUUID(),
      x: String(step?.x ?? form.x),
      y: String(step?.y ?? form.y),
      delay: String(step?.delay ?? 1),
      editing: Boolean(step),
    })
  }
  function applyDraft() {
    if (!draft) return
    const x = Number(draft.x),
      y = Number(draft.y),
      delay = Number(draft.delay)
    if (
      !draft.x.trim() ||
      !draft.y.trim() ||
      !Number.isInteger(x) ||
      !Number.isInteger(y) ||
      !Number.isFinite(delay) ||
      delay < 0.05 ||
      delay > 315360000
    ) {
      setDraftError(
        "Use whole-number coordinates and a wait between 0.05 and 315360000 seconds."
      )
      return
    }
    const step = { id: draft.id, x, y, delay }
    setSteps((list) =>
      draft.editing
        ? list.map((s) => (s.id === step.id ? step : s))
        : [...list, step]
    )
    setDraft(null)
  }
  function move(index: number, direction: number) {
    setSteps((list) => {
      const next = [...list]
      ;[next[index], next[index + direction]] = [
        next[index + direction],
        next[index],
      ]
      return next
    })
  }
  function savePattern() {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            version: 1,
            steps: steps.map(({ x, y, delay }) => ({ x, y, delay })),
          },
          null,
          2
        ),
      ],
      { type: "application/json" }
    )
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "click-pattern.json"
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    setFileNotice("Pattern downloaded as click-pattern.json.")
  }
  const progress = desktop?.limit
    ? Math.min(100, (desktop.completed / desktop.limit) * 100)
    : 0
  const themeIcon = theme === "system" ? Monitor : theme === "dark" ? Moon : Sun
  const ThemeIcon = themeIcon
  const repeatLabel = pattern ? "cycles" : "clicks"

  if (closed)
    return (
      <main className="closed-screen">
        <Check className="size-8 text-primary" />
        <h1>App closed</h1>
        <p>All clicks have stopped. You can close this tab.</p>
        <p>Use the desktop launcher to open Simple Autoclicker again.</p>
      </main>
    )

  return (
    <div className="app-shell">
      <header className="app-header">
        <a href="#" className="brand" aria-label="Simple Autoclicker home">
          <img src="/icon.png" alt="" className="size-10" />
          <span>Simple Autoclicker</span>
        </a>
        <div className="header-actions">
          <Badge variant="outline">
            <ShieldCheck data-icon="inline-start" />
            Runs locally
          </Badge>
          <Button
            variant="ghost"
            aria-label={`Theme: ${theme}. Change theme`}
            onClick={() =>
              setTheme(
                theme === "system"
                  ? "light"
                  : theme === "light"
                    ? "dark"
                    : "system"
              )
            }
          >
            <ThemeIcon data-icon="inline-start" />
            <span className="theme-name">
              {theme.charAt(0).toUpperCase() + theme.slice(1)}
            </span>
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <Button
            variant="ghost"
            disabled={!connected || pending}
            onClick={() => void action("quit")}
          >
            <Power data-icon="inline-start" />
            Quit app
          </Button>
        </div>
      </header>

      <main className="workspace">
        <div className="page-heading">
          <div>
            <h1>Clicks, on your schedule.</h1>
            <p>
              A single point or a whole sequence. Set it up, then let it run.
            </p>
          </div>
          <Badge variant={desktop?.running ? "default" : "secondary"}>
            {desktop?.running
              ? "Running"
              : desktop?.picking
                ? "Picking a point"
                : connected
                  ? "Ready"
                  : "Connecting"}
          </Badge>
        </div>
        {error && (
          <Alert variant="destructive">
            <CircleAlert />
            <AlertTitle>
              {connected
                ? "Check your settings"
                : "Desktop connection unavailable"}
            </AlertTitle>
            <AlertDescription>
              {error}
              {!connected &&
                " Open this page using Start Clicker.cmd or start-clicker.sh."}
            </AlertDescription>
          </Alert>
        )}
        <div className="workspace-grid">
          <section className="setup-panel" aria-labelledby="setup-title">
            <div className="panel-heading">
              <div>
                <h2 id="setup-title">Click setup</h2>
                <p>Where to click, and what happens next.</p>
              </div>
              <MousePointer2 className="section-icon" />
            </div>
            <ToggleGroup
              type="single"
              value={form.target_mode}
              onValueChange={(value) => value && change("target_mode", value)}
              disabled={busy}
              variant="outline"
              className="mode-control"
              aria-label="Click mode"
            >
              <ToggleGroupItem value="single">
                <MousePointer2 />
                Single point
              </ToggleGroupItem>
              <ToggleGroupItem value="pattern">
                <Route />
                Click pattern
              </ToggleGroupItem>
            </ToggleGroup>
            {!pattern ? (
              <div className="single-setup">
                <FieldGroup className="coordinate-fields">
                  <Field data-disabled={busy}>
                    <FieldLabel htmlFor="point-x">X position</FieldLabel>
                    <Input
                      id="point-x"
                      type="number"
                      step="1"
                      value={form.x}
                      onChange={(e) => change("x", e.target.value)}
                      disabled={busy}
                    />
                  </Field>
                  <Field data-disabled={busy}>
                    <FieldLabel htmlFor="point-y">Y position</FieldLabel>
                    <Input
                      id="point-y"
                      type="number"
                      step="1"
                      value={form.y}
                      onChange={(e) => change("y", e.target.value)}
                      disabled={busy}
                    />
                  </Field>
                </FieldGroup>
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full"
                  disabled={busy}
                  onClick={() => void action("pick", { id: "single" })}
                >
                  <Crosshair data-icon="inline-start" />
                  Pick a point on screen
                </Button>
                <p className="helper">
                  A crosshair appears over your desktop. Click your target to
                  capture it.
                </p>
                <Separator />
                <FieldGroup className="interval-fields">
                  <Field data-disabled={busy}>
                    <FieldLabel htmlFor="interval">
                      Wait between clicks
                    </FieldLabel>
                    <Input
                      id="interval"
                      type="number"
                      min={
                        form.unit === "milliseconds"
                          ? "50"
                          : form.unit === "minutes"
                            ? String(0.05 / 60)
                            : ".05"
                      }
                      step="any"
                      value={form.interval}
                      onChange={(e) => change("interval", e.target.value)}
                      disabled={busy}
                    />
                  </Field>
                  <Field data-disabled={busy}>
                    <FieldLabel htmlFor="unit">Unit</FieldLabel>
                    <Select
                      value={form.unit}
                      onValueChange={(value) => change("unit", value)}
                      disabled={busy}
                    >
                      <SelectTrigger id="unit" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {["seconds", "minutes", "milliseconds"].map(
                            (unit) => (
                              <SelectItem key={unit} value={unit}>
                                {unit.charAt(0).toUpperCase() + unit.slice(1)}
                              </SelectItem>
                            )
                          )}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                </FieldGroup>
                <p className="helper">
                  Each repetition is one left click. Minimum wait: 50
                  milliseconds.
                </p>
                <div className="point-explainer">
                  <Crosshair className="size-6" />
                  <div>
                    <h3>Your target stays fixed</h3>
                    <p>
                      Every click returns to this screen position, even if you
                      move the pointer.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="pattern-setup">
                <div className="pattern-toolbar">
                  <span>
                    {steps.length} {steps.length === 1 ? "step" : "steps"}
                  </span>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={busy}
                      onClick={() => fileInput.current?.click()}
                    >
                      <Upload data-icon="inline-start" />
                      Load
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={busy || !steps.length}
                      onClick={savePattern}
                    >
                      <Download data-icon="inline-start" />
                      Save
                    </Button>
                  </div>
                </div>
                <input
                  ref={fileInput}
                  type="file"
                  accept=".json,application/json"
                  hidden
                  onChange={async (e) => {
                    const file = e.target.files?.[0]
                    if (!file) return
                    try {
                      if (file.size > 262144)
                        throw new Error(
                          "Choose a pattern file smaller than 256 KB."
                        )
                      setSteps(decodePattern(await file.text()))
                      setError("")
                      setFileNotice(`Loaded ${file.name}.`)
                    } catch (cause) {
                      setError(
                        cause instanceof Error
                          ? cause.message
                          : "Could not load the pattern."
                      )
                    }
                    e.target.value = ""
                  }}
                />
                {!steps.length ? (
                  <Empty>
                    <EmptyHeader>
                      <EmptyMedia variant="icon">
                        <Route />
                      </EmptyMedia>
                      <EmptyTitle>Build your first pattern</EmptyTitle>
                      <EmptyDescription>
                        Add points in the order you want to click them. Give
                        each step its own wait.
                      </EmptyDescription>
                    </EmptyHeader>
                    <EmptyContent>
                      <Button disabled={busy} onClick={() => newDraft()}>
                        <Plus data-icon="inline-start" />
                        Add first step
                      </Button>
                    </EmptyContent>
                  </Empty>
                ) : (
                  <>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Step</TableHead>
                          <TableHead>Position</TableHead>
                          <TableHead>Wait</TableHead>
                          <TableHead>
                            <span className="sr-only">Step actions</span>
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {steps.map((step, index) => (
                          <TableRow
                            key={step.id}
                            data-state={
                              desktop?.running && desktop.step === index + 1
                                ? "selected"
                                : undefined
                            }
                          >
                            <TableCell>
                              <span className="step-number">{index + 1}</span>
                            </TableCell>
                            <TableCell className="tabular-nums">
                              {step.x}, {step.y}
                            </TableCell>
                            <TableCell className="tabular-nums">
                              {step.delay}s
                            </TableCell>
                            <TableCell>
                              <div className="flex justify-end gap-0.5">
                                {[
                                  ["up", ArrowUp, -1],
                                  ["down", ArrowDown, 1],
                                ].map(([label, Icon, direction]) => {
                                  const StepIcon = Icon as typeof ArrowUp
                                  return (
                                    <Button
                                      key={String(label)}
                                      variant="ghost"
                                      size="icon-sm"
                                      aria-label={`Move step ${index + 1} ${label}`}
                                      disabled={
                                        busy ||
                                        (direction === -1
                                          ? index === 0
                                          : index === steps.length - 1)
                                      }
                                      onClick={() =>
                                        move(index, Number(direction))
                                      }
                                    >
                                      <StepIcon />
                                    </Button>
                                  )
                                })}
                                <Button
                                  variant="ghost"
                                  size="icon-sm"
                                  aria-label={`Edit step ${index + 1}`}
                                  disabled={busy}
                                  onClick={() => newDraft(step)}
                                >
                                  <Pencil />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon-sm"
                                  aria-label={`Remove step ${index + 1}`}
                                  disabled={busy}
                                  onClick={() =>
                                    setSteps((list) =>
                                      list.filter((s) => s.id !== step.id)
                                    )
                                  }
                                >
                                  <Trash2 />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    <Button
                      variant="outline"
                      className="w-full"
                      disabled={busy || steps.length >= 1000}
                      onClick={() => newDraft()}
                    >
                      <Plus data-icon="inline-start" />
                      Add step
                    </Button>
                  </>
                )}
                <p className="helper">
                  Runs from top to bottom. The last step’s wait separates
                  cycles.
                </p>
                {fileNotice && (
                  <p className="helper" role="status">
                    {fileNotice}
                  </p>
                )}
              </div>
            )}
          </section>

          <section className="schedule-panel" aria-labelledby="schedule-title">
            <div className="panel-heading">
              <div>
                <h2 id="schedule-title">Schedule</h2>
                <p>Choose when to start and stop.</p>
              </div>
              <CalendarClock className="section-icon" />
            </div>
            <FieldGroup>
              <FieldSet disabled={busy}>
                <FieldLegend>Start clicking</FieldLegend>
                <ToggleGroup
                  type="single"
                  value={form.start_mode}
                  onValueChange={(v) => v && change("start_mode", v)}
                  disabled={busy}
                  variant="outline"
                  className="schedule-toggle"
                  aria-label="Start condition"
                >
                  <ToggleGroupItem value="delay">
                    <Clock3 />
                    After a delay
                  </ToggleGroupItem>
                  <ToggleGroupItem value="date">
                    <CalendarClock />
                    Date & time
                  </ToggleGroupItem>
                </ToggleGroup>
                {form.start_mode === "delay" ? (
                  <Field>
                    <FieldLabel htmlFor="start-delay">
                      Start delay, in seconds
                    </FieldLabel>
                    <Input
                      id="start-delay"
                      type="number"
                      min="0"
                      step="any"
                      value={form.delay}
                      onChange={(e) => change("delay", e.target.value)}
                    />
                    <FieldDescription>
                      A moment to get your desktop ready.
                    </FieldDescription>
                  </Field>
                ) : (
                  <FieldGroup className="date-fields">
                    <Field>
                      <FieldLabel htmlFor="start-date">Start date</FieldLabel>
                      <Input
                        id="start-date"
                        type="date"
                        value={form.start_date}
                        onChange={(e) => change("start_date", e.target.value)}
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="start-time">Start time</FieldLabel>
                      <Input
                        id="start-time"
                        type="time"
                        step="1"
                        value={form.clock}
                        onChange={(e) =>
                          change(
                            "clock",
                            e.target.value.length === 5
                              ? `${e.target.value}:00`
                              : e.target.value
                          )
                        }
                      />
                    </Field>
                  </FieldGroup>
                )}
              </FieldSet>
              <Separator />
              <FieldSet disabled={busy}>
                <FieldLegend>Stop clicking</FieldLegend>
                <ToggleGroup
                  type="single"
                  value={form.stop_mode}
                  onValueChange={(v) => v && change("stop_mode", v)}
                  disabled={busy}
                  variant="outline"
                  className="schedule-toggle"
                  aria-label="Stop condition"
                >
                  <ToggleGroupItem value="count">
                    <Repeat2 />
                    By count
                  </ToggleGroupItem>
                  <ToggleGroupItem value="date">
                    <CalendarClock />
                    End date
                  </ToggleGroupItem>
                </ToggleGroup>
                {form.stop_mode === "count" ? (
                  <Field>
                    <FieldLabel htmlFor="count">
                      Number of {repeatLabel}
                    </FieldLabel>
                    <Input
                      id="count"
                      type="number"
                      min="1"
                      step="1"
                      value={form.count}
                      onChange={(e) => change("count", e.target.value)}
                    />
                    <FieldDescription>
                      {pattern
                        ? `One cycle runs all ${steps.length} steps once.`
                        : "Set to 1 for a single click."}
                    </FieldDescription>
                  </Field>
                ) : (
                  <FieldGroup className="date-fields">
                    <Field>
                      <FieldLabel htmlFor="end-date">End date</FieldLabel>
                      <Input
                        id="end-date"
                        type="date"
                        value={form.end_date}
                        onChange={(e) => change("end_date", e.target.value)}
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="end-time">End time</FieldLabel>
                      <Input
                        id="end-time"
                        type="time"
                        step="1"
                        value={form.end_clock}
                        onChange={(e) =>
                          change(
                            "end_clock",
                            e.target.value.length === 5
                              ? `${e.target.value}:00`
                              : e.target.value
                          )
                        }
                      />
                    </Field>
                  </FieldGroup>
                )}
              </FieldSet>
            </FieldGroup>
            <p className="timezone-note">
              <Clock3 className="size-3.5" />
              All times use your computer’s local clock.
            </p>
          </section>
        </div>

        <section className="run-bar" aria-label="Run controls">
          <div className="run-info">
            <span className="run-icon">
              {desktop?.running ? (
                <Loader2 className="size-5 motion-safe:animate-spin" />
              ) : (
                <MousePointer2 className="size-5" />
              )}
            </span>
            <div>
              <h2>
                {desktop?.running
                  ? `Next click in ${duration(desktop.next_in)}`
                  : desktop?.picking
                    ? "Select your point on the desktop"
                    : "Ready when you are"}
              </h2>
              <p role="status" aria-live="polite">
                {desktop?.running
                  ? `${desktop.completed}${desktop.limit ? ` of ${desktop.limit}` : ""} clicks completed${desktop.step ? ` · Next: step ${desktop.step}` : ""}`
                  : desktop?.status || "Connecting to the desktop app…"}
              </p>
            </div>
          </div>
          <div className="run-actions">
            <Button
              size="lg"
              variant="outline"
              disabled={!connected || (!desktop?.running && !desktop?.picking)}
              onClick={() => void action("stop")}
            >
              <Square data-icon="inline-start" />
              Stop<span className="key-hint">Esc</span>
            </Button>
            <Button
              size="lg"
              disabled={busy || (pattern && !steps.length)}
              onClick={() =>
                void action("start", {
                  settings: form,
                  pattern: steps.map(({ x, y, delay }) => ({ x, y, delay })),
                })
              }
            >
              {pending ? (
                <Loader2
                  data-icon="inline-start"
                  className="motion-safe:animate-spin"
                />
              ) : (
                <Play data-icon="inline-start" />
              )}
              Start clicking
            </Button>
          </div>
          {Boolean(desktop?.running && desktop.limit) && (
            <Progress
              value={progress}
              aria-label="Clicks completed"
              className="run-progress"
            />
          )}
        </section>
        <footer className="workspace-footer">
          <span>
            <ShieldCheck className="size-3.5" />
            Keep your desktop unlocked and the target visible.
          </span>
          <span>
            {desktop?.platform === "linux"
              ? "X11 desktop · Disable automatic sleep"
              : "Windows · Keeps the computer awake while running"}
          </span>
          <p>Closing this tab does not stop a run. Use Stop or Quit app.</p>
        </footer>
      </main>

      <Dialog
        open={Boolean(draft)}
        onOpenChange={(open) => {
          if (!open && !desktop?.picking) setDraft(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {draft?.editing ? "Edit pattern step" : "Add a pattern step"}
            </DialogTitle>
            <DialogDescription>
              Pick the target and set how long to wait after this click.
            </DialogDescription>
          </DialogHeader>
          {draft && (
            <FieldGroup>
              <FieldGroup className="coordinate-fields">
                <Field data-invalid={Boolean(draftError)}>
                  <FieldLabel htmlFor="step-x">X position</FieldLabel>
                  <Input
                    id="step-x"
                    type="number"
                    step="1"
                    value={draft.x}
                    aria-invalid={Boolean(draftError)}
                    onChange={(e) =>
                      setDraft((d) => d && { ...d, x: e.target.value })
                    }
                  />
                </Field>
                <Field data-invalid={Boolean(draftError)}>
                  <FieldLabel htmlFor="step-y">Y position</FieldLabel>
                  <Input
                    id="step-y"
                    type="number"
                    step="1"
                    value={draft.y}
                    aria-invalid={Boolean(draftError)}
                    onChange={(e) =>
                      setDraft((d) => d && { ...d, y: e.target.value })
                    }
                  />
                </Field>
              </FieldGroup>
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => void action("pick", { id: draft.id })}
              >
                <Crosshair data-icon="inline-start" />
                Pick a point on screen
              </Button>
              <Field data-invalid={Boolean(draftError)}>
                <FieldLabel htmlFor="step-delay">
                  Wait after click, in seconds
                </FieldLabel>
                <Input
                  id="step-delay"
                  type="number"
                  min="0.05"
                  step="any"
                  value={draft.delay}
                  aria-invalid={Boolean(draftError)}
                  onChange={(e) =>
                    setDraft((d) => d && { ...d, delay: e.target.value })
                  }
                />
                <FieldDescription>
                  Minimum 0.05 seconds. The last step’s wait separates cycles.
                </FieldDescription>
              </Field>
              {draftError && (
                <p role="alert" className="text-sm text-destructive">
                  {draftError}
                </p>
              )}
            </FieldGroup>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              disabled={Boolean(desktop?.picking)}
              onClick={() => setDraft(null)}
            >
              <X data-icon="inline-start" />
              Cancel
            </Button>
            <Button disabled={Boolean(desktop?.picking)} onClick={applyDraft}>
              <Check data-icon="inline-start" />
              {draft?.editing ? "Save step" : "Add step"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
