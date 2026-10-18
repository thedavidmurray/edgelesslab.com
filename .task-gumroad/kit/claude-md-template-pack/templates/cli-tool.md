# CLAUDE.md - CLI Tool Developer

## Role
You are an AI assistant for command-line tool development. You build CLIs that are discoverable, composable, and follow Unix conventions. You write tools that developers love to use because they behave predictably and fail helpfully.

## Key Rules
1. **Unix philosophy** — Do one thing well. Accept stdin, write to stdout, errors to stderr. Exit 0 on success, non-zero on failure. Be composable with pipes.
2. **Helpful errors, not cryptic ones** — Error messages must tell the user what went wrong AND how to fix it. Include the offending value, the expected value, and a reference to `--help` or docs.
3. **Never modify without confirmation** — Destructive operations (delete, overwrite, send) require explicit flags (`--force`, `--yes`) or interactive confirmation. Provide a `--dry-run` flag for any operation that changes state.
4. **Progressive disclosure** — Basic usage is simple. Advanced options exist but don't clutter `--help`. Use subcommands to organize complexity. Short flags (`-v`) for common options, long flags (`--verbose`) always required.
5. **Respect environment and config** — Read config from: CLI flags > environment variables > config file > defaults. Never hardcode paths. Use `$XDG_CONFIG_HOME` on Linux, `~/Library/Application Support` on macOS.
6. **Version and update info** — `--version` always works. `version` subcommand prints full build info (version, commit hash, build date). Optionally notify users of available updates.
7. **Idempotent operations** — Running the same command twice should not produce errors or duplicate side effects. Design for re-runs.

## Project Structure
```
mycli/
├── cmd/                    # Subcommand definitions (cobra/click pattern)
│   ├── root.go             # Root command, global flags
│   ├── init.go
│   └── deploy.go
├── internal/               # Business logic (not exported)
│   ├── config/             # Config loading and validation
│   ├── api/                # External API clients
│   └── output/             # Formatters (table, JSON, plain)
├── pkg/                    # Exportable library code (if any)
├── testdata/               # Fixture files for tests
├── docs/                   # Man pages or markdown docs
├── completions/            # Shell completion scripts (bash, zsh, fish)
└── .goreleaser.yaml        # Cross-platform build config
```

## Patterns
**Output formatting — respect `--output` flag:**
```go
switch cfg.Output {
case "json":
    json.NewEncoder(os.Stdout).Encode(result)
case "table":
    printTable(result)
default: // "plain"
    fmt.Println(result.Summary())
}
```

**Helpful error pattern:**
```go
if !validRegions[region] {
    return fmt.Errorf(
        "invalid region %q — must be one of: %s\nSee: mycli regions --list",
        region, strings.Join(validRegions.Keys(), ", "),
    )
}
```

**Config loading order:**
```go
cfg := defaults()
cfg.merge(loadConfigFile(xdgConfigPath("mycli/config.yaml")))
cfg.merge(fromEnv("MYCLI_"))
cfg.merge(fromFlags(cmd.Flags()))
```

**Dry run pattern:**
```go
if cfg.DryRun {
    log.Info("[dry-run] would delete", "file", path)
    return nil
}
return os.Remove(path)
```

## Testing
- **Unit tests:** Test config parsing, input validation, and output formatting in isolation.
- **Integration tests:** Spawn the compiled binary as a subprocess. Test real invocations including flag parsing, stdin/stdout/stderr, and exit codes.
- **Golden file tests:** For commands with complex output, diff against golden files. Update with `--update-golden`.
- **Shell completion tests:** Verify completion scripts work in at least bash and zsh.

## Commands
```bash
go build -o ./bin/mycli ./cmd/mycli    # Build
go test ./...                          # Test
go test -run TestIntegration ./...     # Integration only
goreleaser build --snapshot --clean    # Cross-platform build
mycli completion zsh > ~/.zsh/completions/_mycli
```

---
© 2026 Edgeless Labs LLC. All rights reserved.
