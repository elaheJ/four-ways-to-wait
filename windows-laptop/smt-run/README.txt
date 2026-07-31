SMT MEASUREMENT -- Intel Core i5-7300U laptop
=============================================

Double-click RUN-ME.bat

That is the whole thing. Nothing needs installing.

If scaling.exe and probe.exe are not in this folder, you cloned
this from GitHub -- binaries are not kept in the source tree.
Download them from the repository's Releases page and drop them
in here:
  https://github.com/elaheJ/four-ways-to-wait/releases
Or build them yourself; see instructor\windows-smt-measurement.md.

Before you do:
  - plug the laptop in, battery above 80%
  - power plan: High performance
  - PAUSE Dropbox sync (it syncs this very folder, and on a
    2-core machine that lands in the measurements)
  - close other applications

Takes about 5 minutes. Results land in the results\ folder and
sync back once you un-pause Dropbox.

If Windows SmartScreen complains about an unrecognised app:
  More info -> Run anyway
or right-click scaling.exe and probe.exe -> Properties -> Unblock.
These were cross-compiled on the Mac in this repo; they did not
come from the internet, but Windows cannot tell the difference.

What it measures
----------------
Whether the second thread on a physical core buys anything --
i.e. what hyperthreading is actually worth on this chip. The
laptop reports 4 threads on 2 real cores, and it is the only
device in the study that has SMT at all, so this run closes a
gap the paper currently defers to future work.

Full explanation:
  instructor\windows-smt-measurement.md
