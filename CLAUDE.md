# work/ — collaboration instructions

## Co-editing remote-run scripts

Use the `coedit` tool. Its canonical spec lives next to it:
**`../tools/coedit/README.md`** (both repos sit side by side under `ClaudeRoot/`).
Do not duplicate it here.

In short: the git working tree is a file under `work/<PROJECT>/`; an external
staging file (written by MobaX/VS Code Remote-SSH/sshfs/scp/… — any remote-access
tool) is the conduit to the remote. `coedit bind` associates the pair, then
`coedit export` sends my edit out and `coedit import` pulls the user's edit in.
Claude commits when asked; **the user pushes.**
