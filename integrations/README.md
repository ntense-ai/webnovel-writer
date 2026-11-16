# Codex and Antigravity adapters

These project-local skills reuse the same English engine as Claude Code. They are
an initial **portable skills integration**, not native plugin or hook parity.
Claude Code's existing installation remains unchanged.

## Install from the English branch

```bash
git clone --branch ntense --single-branch https://github.com/ezhomelabs/webnovel-writer.git
cd webnovel-writer
python3 integrations/install.py --host codex --workspace /absolute/path/to/writing-workspace --dry-run
python3 integrations/install.py --host codex --workspace /absolute/path/to/writing-workspace
```

For Antigravity substitute `--host antigravity`. Both current hosts discover
`.agents/skills`; install **once**, not once per host, when sharing a workspace.
For an older Antigravity build requiring `.agent/skills`, add
`--legacy-antigravity` instead. Use the Python environment and dependencies
specified in the repository setup instructions. The installer itself uses only
the Python standard library and does not install software or modify host settings.

Open that workspace in your host. Select `$webnovel-init` in Codex, or ask
Antigravity to use `webnovel-init`. There are eight skills: init, plan, write,
review, query, learn, doctor, and dashboard. Workflow names are not a promise
that every host exposes matching slash commands.

The installer copies a snapshot into `.webnovel-writer-engine/` and adds eight
small skill wrappers. It refuses existing destinations, including symlinks, so
it cannot silently replace your custom skills. Source updates do not update the
snapshot automatically. To upgrade, first back up the installed engine and
wrappers, move those exact installation paths aside, then rerun the installer.
Do not remove book directories or `.webnovel`/`.story-system` data. Keep both the
installed wrappers and engine together when relocating a workspace.

## Capability boundaries

File and shell access plus Python dependencies are needed for runtime commands.
Writing/review workflows also require real subagent support for independent
roles. When unavailable, the adapter stops the gated workflow rather than
pretending that review happened. It does not install Claude lifecycle hooks,
change security settings, or create background services. Explicit preflight and
write gates remain mandatory. Full native host sessions and model-generated
chapter quality must be validated separately; installer tests are not proof of
end-to-end host parity.

## Design references

The requested [Antigravity fork](https://github.com/ezhomelabs/antigravity-webnovel-writer/)
was reviewed at `f7f593266db3407b3d9d460c8234c0bb97c28ddc`. Its workspace skill/engine
layout informed this adapter. We did not import its alternate engine, assume its
agent names are native tools, or duplicate its two engine copies.

Discovery and frontmatter follow [Codex skills documentation](https://developers.openai.com/codex/skills/)
and [Antigravity skills documentation](https://antigravity.google/docs/skills).
