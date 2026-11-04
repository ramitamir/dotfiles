---
name: dispatch
description: Use when an overlord session hands a Linear ticket to a new implementor Claude session on this machine, needs to find or message its own implementors, or cleans up a ticket's worktree after the PR merged. Replaces the supacode dispatch flow.
---

# Dispatching a ticket

A dispatch is a git worktree on the ticket's branch plus a background Claude
session running in it. The overlord talks to it with SendMessage. A human
can watch or attach from `claude agents`. Nothing here needs supacode.

## The one rule first

**One dispatcher per ticket.** Announce the dispatch before running it (the
user may be dispatching the same ticket). On a collision, brief exactly one
session and stand the other down.

## Steps

1. Collect: repo root, the ticket's branch name from Linear (gitBranchName),
   the model from the dispatch decision (`opus` or `fable`), and your own
   session name (first line of ListAgents).

2. From the repo root:

   ```
   claude -w ten-NNN --bg -n <repo>-ten-NNN --model <model> '<kickoff>'
   ```

   - `-w ten-NNN` creates `<repo>/.claude/worktrees/ten-NNN` on a branch
     named `worktree-ten-NNN`, based on origin's default branch.
   - `-n <repo>-ten-NNN` is the session name. ListAgents shows names only,
     so the repo prefix is how an overlord tells its implementors from
     another overlord's. Never skip it.
   - It prints an id: `backgrounded · 9275f7d0 · camp4-ten-999`. Record
     ticket, id and your overlord name in the ticket's task note. A
     replacement overlord needs the id for cleanup.

3. Kickoff text, in the quotes above:

   > You are the implementor for Linear ticket TEN-NNN (repo X, worktree
   > `<repo>/.claude/worktrees/ten-NNN`). First run
   > `git branch -m <ticket-branch>`. Read the ticket in full. The X
   > overlord session (`<overlord name>`) will send your brief. Wait for it
   > before designing.

4. ListAgents shows `<repo>-ten-NNN · bg`. Send the full brief with
   SendMessage: ticket contract, spec pointers, TDD, stop at PR plus a done
   report. The brief must say: open the PR as a draft (`gh pr create
   --draft`, a draft runs no CI), mark it ready (`gh pr ready <n>`) only
   when the work is done, and go back to draft before a rework
   (`gh pr ready <n> --undo`), since every push after ready restarts CI.

## Finding your implementors

- ListAgents: peers named `<repo>-ten-*` are yours. Other prefixes belong
  to other overlords. Peers with an auto name (`camp4-3`) were not
  dispatched by this skill; treat them as not yours.
- Scripts: `claude agents --cwd <repo-root> --json` gives id, name,
  status and worktree path for every session under that repo.
- Humans: `claude agents` in a terminal lists them and attaches.

## Cleanup after merge

Nothing removes a worktree on its own. Once the PR is merged, the overlord
runs, from the repo root:

```
claude rm <id>
git worktree list | grep ten-NNN      # usually empty now
```

`claude rm` drops the session and removes the worktree and its local branch
when git allows. It refuses while the branch has commits that are neither
pushed nor merged into local main; that refusal is the safety, do not run
it twice to force it.

If the worktree is still listed, it holds a populated submodule. Git will
not remove such a worktree without force, and `claude rm` prints "removed"
anyway. Finish by hand:

```
git worktree remove --force <repo>/.claude/worktrees/ten-NNN
git branch -D <ticket-branch>         # -d fails when local main is behind origin
```

The merged PR is the proof the branch is safe to delete, not local main.

## Overlord restart: reconcile first

Background sessions outlive the overlord. A new overlord does this before
taking any ticket, and again for the one ticket about to be dispatched.

1. List ticket worktrees: `git worktree list | grep '.claude/worktrees/ten-'`.
2. List sessions: `claude agents --cwd <repo-root> --json`.
3. For each worktree, check the PR: `gh pr list --head <branch> --state all`.

The PR state decides. A finished implementor still shows as `background
idle`, the same as one waiting for a brief, so session status alone says
nothing about whether the ticket is done.

- **PR merged.** Orphan. Run the cleanup above.
- **PR open or none, session listed.** Work with nobody driving it. Do not
  delete. Send it a message (an idle background session wakes up and
  answers), resend the brief if it was in flight, carry on.
- **PR open or none, no session.** Re-dispatch and point the new
  implementor at the existing branch and worktree.

A worktree that already exists for the ticket being dispatched is a
collision with an earlier attempt: the one-dispatcher rule applies.

Messages sent to the dead overlord are gone; ask the implementor for status
rather than guessing. No timer is needed: an idle worktree costs disk only.

## Worktree setup

- A fresh worktree has no `.venv`. `uv run` inside a component builds one in
  the worktree. The old supacode scar (venv shebangs pointing at the primary
  tree) came from supacode copying `.venv`; it cannot happen here.
- If the repo has submodules (`.gitmodules` exists), their paths start
  empty in a fresh worktree. Do not init them by default: git will not
  remove a worktree with a populated submodule, so `claude rm` leaves it
  behind. An implementor that needs one runs `git submodule update --init`
  and says so in the done report, and the overlord uses the force cleanup
  above.

## Not a dispatch

In-process subagents (the Agent tool, including `isolation: "worktree"`)
die with the parent and never appear in `claude agents`. Use them for
side-quests, not for tickets.

Dispatch remains the user's decision (what, when, which model). This skill
is the mechanics, run on their word.
