# Volatility3 / Sleuth Kit Command Reference

## Volatility3 — Windows plugins (`vol -f <image> windows.<plugin>`)

| Plugin | Answers |
|---|---|
| `windows.info` | OS build, architecture — run first, always |
| `windows.pslist` | Process list via pool scanning (finds unlinked/hidden processes) |
| `windows.psscan` | Process list via a different scan method — cross-check against `pslist` |
| `windows.pstree` | Parent/child process hierarchy |
| `windows.cmdline` | Command line each process was launched with |
| `windows.dlllist` | DLLs loaded per process |
| `windows.handles` | Open handles (files, registry keys, mutexes) per process |
| `windows.netscan` | TCP/UDP endpoints (active and recently closed), with owning PID |
| `windows.netstat` | Alternative network-connection view |
| `windows.malfind` | Scans process memory for injected/hidden executable regions |
| `windows.hollowprocesses` | Process-hollowing detection (if present in your Volatility3 version) |
| `windows.filescan` | File objects resident in memory |
| `windows.dumpfiles` | Extract a file object to disk (`-o <dir> --pid <PID>`) |
| `windows.registry.hivelist` | Registry hives present in the image |
| `windows.registry.printkey` | Dump one registry key (`--key "path"`) |
| `windows.svcscan` | Windows services |
| `windows.envars` | Environment variables per process |

## Volatility3 — Linux plugins (`vol -f <image> linux.<plugin>`)

| Plugin | Answers |
|---|---|
| `linux.info` | Kernel version/build — run first |
| `linux.pslist` | Process list |
| `linux.psaux` | Process list with full command lines (like `ps aux`) |
| `linux.pstree` | Parent/child hierarchy |
| `linux.bash` | Recovered bash command history from memory |
| `linux.netstat` | Network connections |
| `linux.malfind` | Injected/hidden executable memory regions |
| `linux.lsof` | Open file descriptors per process |
| `linux.proc_maps` | Memory mappings per process |
| `linux.check_modules` | Loaded kernel modules — compare against `lsmod`-equivalent baseline for hidden/rootkit modules |

## Volatility3 — macOS plugins (`vol -f <image> mac.<plugin>`)

| Plugin | Answers |
|---|---|
| `mac.pslist` | Process list |
| `mac.pstree` | Parent/child hierarchy |
| `mac.netstat` | Network connections |
| `mac.malfind` | Injected/hidden executable memory regions |
| `mac.bash` | Recovered bash history |
| `mac.lsof` | Open file descriptors |

## The Sleuth Kit — commands

All commands take `-o <sector>` (the partition's start sector from `mmls`) except `mmls` itself.

| Command | Answers |
|---|---|
| `mmls <image>` | Partition table — start sector of each partition (run first) |
| `fsstat -o <sector> <image>` | Filesystem type and general stats for one partition |
| `fls -r -o <sector> <image>` | Recursive file listing; `*`-prefixed entries are deleted |
| `fls -r -d -o <sector> <image>` | Deleted entries only |
| `istat -o <sector> <image> <inode>` | MAC(B) timestamps, allocation status, block list for one inode |
| `icat -o <sector> <image> <inode> > out` | Extract one file's content by inode |
| `tsk_recover -o <sector> <image> <dir>` | Bulk-recover every recoverable file (allocated + deleted) into `<dir>` |
| `blkls -o <sector> <image> > unalloc.img` | Extract unallocated space — for carving deleted file fragments |
| `blkcat -o <sector> <image> <block>` | Dump raw content of one block by block number |
| `img_stat <image>` | Basic info about the image file itself (format, sector size) |

## Timestamp Reading (MAC(B))

- **M**odified — content last changed
- **A**ccessed — last read (often disabled/coarse on modern filesystems — don't over-index on it)
- **C**hanged — metadata (permissions, owner) last changed
- **B**irth — file creation time (not present on all filesystems)

A file whose Modified time predates its Birth time is a strong anomaly
signal — it usually means the file's timestamps were deliberately
manipulated (timestomping) or it was copied from another filesystem
that preserved a different Modified time than its actual creation on
this one.
