#!/usr/bin/env bun
import { Command } from "commander"
import { spawn } from "bun"

const program = new Command()

function addDeviceOptions(cmd: Command) {
  return cmd
    .requiredOption("--ip <ip>", "Device IP or comma-separated IPs")
    .option("--password <password>", "Device communication password", "")
    .option("--model <model>", "Device model", "ZK100")
}

function buildEnv(ip: string, password: string, model: string) {
  return {
    ...process.env,
    PYZKACCESS_CONNECT_CONNSTR:
      `protocol=TCP,ipaddress=${ip},port=4370,timeout=4000,passwd=${password}`,
    PYZKACCESS_CONNECT_MODEL: model,
  }
}

async function run(ip: string, args: string[], env: any) {
  const proc = spawn({
    cmd: ["./pyzkaccess.exe", "connect", "ENV", ...args],
    env,
    stdout: "pipe",
    stderr: "pipe",
  })

  const out = await new Response(proc.stdout).text()
  const err = await new Response(proc.stderr).text()

  if (err) {
    console.error(`[${ip}] ERROR:\n${err}`)
    return null
  }

  return out
}

async function handleMultiIP(
  ips: string,
  password: string,
  model: string,
  handler: (ip: string) => Promise<void>
) {
  for (const ip of ips.split(",").map(x => x.trim())) {
    await handler(ip)
  }
}

/* ==========================
   get_events
========================== */

const getEvents = addDeviceOptions(
  program.command("get_events").description("Fetch events")
)

/* -------- unread (realtime poll) -------- */

getEvents
  .command("unread")
  .description("Realtime event stream")
  .action(async (_, cmd) => {
    const opts = cmd.parent!.opts()

    await handleMultiIP(opts.ip, opts.password, opts.model, async (ip) => {
      const env = buildEnv(ip, opts.password, opts.model)
      await run(ip, ["events", "poll"], env)
    })
  })

/* -------- all -------- */

getEvents
  .command("all")
  .description("Fetch all stored events")
  .action(async (_, cmd) => {
    const opts = cmd.parent!.opts()

    await handleMultiIP(opts.ip, opts.password, opts.model, async (ip) => {
      const env = buildEnv(ip, opts.password, opts.model)
      const out = await run(ip, ["table", "Event"], env)
      if (out) console.log(`[${ip}] RESULT:\n${out}`)
    })
  })

/* -------- last -------- */

getEvents
  .command("last")
  .requiredOption("--count <number>", "Number of last events")
  .description("Fetch last N events (client-side slice)")
  .action(async (subOpts, cmd) => {
    const opts = cmd.parent!.opts()
    const count = Number(subOpts.count)

    await handleMultiIP(opts.ip, opts.password, opts.model, async (ip) => {
      const env = buildEnv(ip, opts.password, opts.model)
      const out = await run(ip, ["table", "Transaction"], env)

      if (!out) return

      const lines = out.trim().split("\n")

      // naive slice (adjust if using CSV/json format)
      const header = lines.slice(0, 3)
      const rows = lines.slice(3)

      const lastRows = rows.slice(-count)

      console.log(`[${ip}] LAST ${count} EVENTS:\n`)
      console.log([...header, ...lastRows].join("\n"))
    })
  })

/* -------- search -------- */

getEvents
  .command("search")
  .requiredOption("--from <date>", "Start date YYYY-MM-DD")
  .requiredOption("--to <date>", "End date YYYY-MM-DD")
  .description("Search events by date range")
  .action(async (subOpts, cmd) => {
    const opts = cmd.parent!.opts()

    await handleMultiIP(opts.ip, opts.password, opts.model, async (ip) => {
      const env = buildEnv(ip, opts.password, opts.model)

      const whereClause = `--time>=${subOpts.from} --time<=${subOpts.to}`

      const args = [
        "table",
        "Event",
        "where",
        `--time>=${subOpts.from}`,
        `--time<=${subOpts.to}`
      ]

      const out = await run(ip, args, env)
      if (out) console.log(`[${ip}] RESULT:\n${out}`)
    })
  })

program.parse()