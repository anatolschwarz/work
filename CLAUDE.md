# work/ — collaboration instructions

## MobaX ⇄ git association — co-editing remote-run scripts

**Topology**
- Scripts are git-tracked and checked out under `ClaudeRoot/work/<PROJECT>/`. This local
  clone is the working tree — **all commits/pushes happen here**.
- The live, running copy is on the **remote** (SSH box). MobaXterm opens a remote file,
  downloads it to a temp copy under `Downloads\MobaXterm\...`, and **auto-scp's it back to
  the remote whenever that temp file changes — but only while the file is open/monitored
  in MobaX.**
- Claude never touches the remote (no SSH/sshfs). MobaX's scp is the only path to the remote.

**To associate a file (do this per session — paths are re-told each time):**
User provides two paths:
- gitted path: `ClaudeRoot/work/<PROJECT>/<file>`
- current MobaX temp path: `Downloads\MobaXterm\...\<file>`

Keep the file open in MobaX so its file-monitor stays active.

**Forward sync (Claude's edits):** Claude edits the gitted file, then copies it over the
MobaX temp path. MobaX detects the change → scp's to the remote.

**Reverse sync (user's edits):** While Claude is running a Monitor, it watches the temp
file's hash; on change it copies the temp file back into the gitted file and shows the diff.
Outside a monitored window, the user retells the change.

**Guardrails**
- File must be open in MobaX or the forward overwrite won't upload.
- Echo guard: hash-compare before reverse-pulling so Claude's own forward write doesn't
  clobber-loop.
- Don't edit the same file in MobaX and via Claude at the same moment.
- CRLF: keep a `.gitattributes` forcing LF (`* text=auto`, `*.sh eol=lf`) so a Windows-side
  checkout doesn't inject `\r` into scripts on the Linux remote. Claude writes LF.
- Association is per-session and non-persistent — re-establish both paths each session.

**Commit & push**
- Claude commits when asked (may be several commits). **The user pushes.**
