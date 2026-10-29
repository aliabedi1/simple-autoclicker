import { test, expect } from "@playwright/test"
import { spawn, type ChildProcess } from "node:child_process"
import { createInterface } from "node:readline"
import { resolve } from "node:path"
import { readFile } from "node:fs/promises"
let child: ChildProcess
let url: string

test.beforeAll(async () => {
  const python =
    process.platform === "win32"
      ? "../.venv/Scripts/python.exe"
      : "../.venv/bin/python"
  child = spawn(resolve(python), ["../tests/browser_host.py"], {
    cwd: process.cwd(),
    stdio: ["pipe", "pipe", "pipe"],
  })
  child.stderr?.on("data", (value) => process.stderr.write(value))
  url = await new Promise<string>((done, reject) => {
    const timeout = setTimeout(
      () => reject(new Error("Desktop fixture did not start")),
      12000
    )
    const lines = createInterface({ input: child.stdout! })
    lines.once("line", (line) => {
      clearTimeout(timeout)
      done(JSON.parse(line).url)
      lines.close()
    })
    child.once("error", reject)
  })
})
test.afterAll(async () => {
  if (url) {
    const address = new URL(url)
    const token = new URLSearchParams(address.hash.slice(1)).get("token") || ""
    try {
      await fetch(`${address.origin}/api/action`, {
        method: "POST",
        headers: { "X-Clicker-Token": token },
        body: JSON.stringify({ action: "quit" }),
        signal: AbortSignal.timeout(2000),
      })
    } catch {
      /* The UI may already have quit. */
    }
  }
  if (child && child.exitCode === null) {
    await Promise.race([
      new Promise((done) => child.once("exit", done)),
      new Promise((done) => setTimeout(done, 2000)),
    ])
    if (child.exitCode === null) child.kill()
  }
})

test("desktop controls and patterns work in the system theme", async ({
  page,
}, testInfo) => {
  const errors: string[] = []
  page.on("pageerror", (error) => errors.push(error.message))
  await page.goto(url)
  await expect(page.getByText("Ready", { exact: true })).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Theme: system. Change theme" })
  ).toBeVisible()
  if (testInfo.project.name === "desktop-dark")
    await expect(page.locator("html")).toHaveClass(/dark/)
  else await expect(page.locator("html")).not.toHaveClass(/dark/)
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-single.png`,
    fullPage: true,
  })
  await page.getByLabel("Start delay, in seconds").fill("0")
  await page.getByLabel("Number of clicks").fill("2")
  await page.getByLabel("Wait between clicks").fill("0.05")
  await page
    .getByRole("button", { name: "Start clicking", exact: true })
    .click()
  await expect(page.getByText("Completed 2 click(s).")).toBeVisible()

  await page.getByRole("radio", { name: "Click pattern", exact: true }).click()
  await expect(page.getByText("Build your first pattern")).toBeVisible()
  await page.getByRole("button", { name: "Add first step" }).click()
  const dialog = page.getByRole("dialog")
  await dialog.getByLabel("X position").fill("10")
  await dialog.getByLabel("Y position").fill("20")
  await dialog.getByLabel("Wait after click, in seconds").fill("0.05")
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-dialog.png`,
    fullPage: true,
  })
  await dialog.getByRole("button", { name: "Add step", exact: true }).click()
  await page.getByRole("button", { name: "Add step", exact: true }).click()
  await dialog.getByLabel("X position").fill("30")
  await dialog.getByLabel("Y position").fill("40")
  await dialog.getByLabel("Wait after click, in seconds").fill("0.05")
  await dialog.getByRole("button", { name: "Add step", exact: true }).click()
  await page.getByRole("button", { name: "Move step 2 up" }).click()
  await expect(page.getByRole("row").nth(1)).toContainText("30, 40")
  await page.getByLabel("Number of cycles").fill("2")
  await page.screenshot({
    path: `test-results/${testInfo.project.name}-pattern.png`,
    fullPage: true,
  })
  await page
    .getByRole("button", { name: "Start clicking", exact: true })
    .click()
  await expect(page.getByText("Completed 4 click(s).")).toBeVisible()
  await page.getByRole("radio", { name: "Date & time", exact: true }).click()
  await expect(page.getByLabel("Start date", { exact: true })).toBeVisible()
  await page.getByRole("radio", { name: "End date", exact: true }).click()
  await expect(page.getByLabel("End time", { exact: true })).toBeVisible()
  const downloadEvent = page.waitForEvent("download")
  await page.getByRole("button", { name: "Save", exact: true }).click()
  const download = await downloadEvent
  const path = testInfo.outputPath("pattern.json")
  await download.saveAs(path)
  const saved = JSON.parse(await readFile(path, "utf8"))
  expect(saved.steps).toHaveLength(2)
  await page.getByRole("button", { name: "Edit step 1" }).click()
  await dialog.getByLabel("X position").fill("50")
  await dialog.getByRole("button", { name: "Save step" }).click()
  await expect(page.getByRole("row").nth(1)).toContainText("50, 40")
  await page.getByRole("button", { name: "Remove step 2" }).click()
  await page.locator("input[type=file]").setInputFiles(path)
  await expect(page.getByRole("row")).toHaveCount(3)
  await page.getByRole("radio", { name: "After a delay", exact: true }).click()
  await page.getByRole("radio", { name: "By count", exact: true }).click()
  await page.getByLabel("Start delay, in seconds").fill("10")
  await page
    .getByRole("button", { name: "Start clicking", exact: true })
    .click()
  await expect(page.getByText("Running", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: /Stop/ }).click()
  await expect(page.getByText("Cancelled. 0 click(s) completed.")).toBeVisible()
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth
  )
  expect(overflow).toBe(false)
  expect(errors).toEqual([])
  await page.getByRole("button", { name: "Quit app", exact: true }).click()
  await expect(page.getByRole("heading", { name: "App closed" })).toBeVisible()
})
