// Preserve dependency notices alongside the compiled interface in release packages.
import { copyFile, mkdir, readFile, readdir, writeFile } from 'node:fs/promises'
import { dirname, join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const lock = JSON.parse(await readFile(join(root, 'package-lock.json'), 'utf8'))
const output = join(root, 'dist', 'assets', 'licenses')
await mkdir(output, { recursive: true })
const manifest = []
for (const [location, pkg] of Object.entries(lock.packages)) {
  if (!location.startsWith('node_modules/') || pkg.dev) continue
  const directory = resolve(root, location)
  if (!directory.startsWith(join(root, 'node_modules') + sep)) {
    throw new Error('Unexpected dependency directory')
  }
  const name = location.replaceAll('node_modules/', '').replaceAll('/', '--')
  let entries
  try { entries = await readdir(directory, { withFileTypes: true }) }
  catch (error) { if (pkg.optional && error.code === 'ENOENT') continue; throw error }
  const files = entries.filter(entry =>
    entry.isFile() && /^(licen[cs]e|copying|copyright|notice|ofl)([.\-_]|$)/i.test(entry.name))
  for (const file of files) {
    await mkdir(join(output, name), { recursive: true })
    await copyFile(join(directory, file.name), join(output, name, file.name))
  }
  manifest.push({ package: name, version: pkg.version, license: pkg.license, notices: files.map(file => `${name}/${file.name}`) })
}
await writeFile(join(output, 'index.json'), JSON.stringify(manifest, null, 2) + '\n')
