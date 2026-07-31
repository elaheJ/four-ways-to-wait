@echo off
REM ============================================================
REM  Four Ways to Wait -- SMT measurement on a 2-core/4-thread PC
REM  Nothing to install. Double-click this file.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   SMT measurement -- Intel Core i5-7300U
echo ============================================================
echo.

if not exist scaling.exe (
  echo ERROR: scaling.exe is missing from this folder.
  echo.
  echo If you cloned this from GitHub, the binaries are not kept in
  echo the source tree. Download scaling.exe and probe.exe from:
  echo   https://github.com/elaheJ/four-ways-to-wait/releases
  echo and put them in this folder. Or build them -- see
  echo instructor\windows-smt-measurement.md
  pause
  exit /b 1
)

REM ---- 0. house-keeping reminders ----------------------------
echo BEFORE YOU CONTINUE:
echo   - laptop plugged in, battery above 80%%
echo   - power plan set to High performance
echo   - Dropbox sync PAUSED  (it is syncing this very folder)
echo   - close other applications
echo.
echo This takes about 5 minutes and the machine will be busy.
pause
echo.

if not exist results mkdir results

REM ---- 1. topology -------------------------------------------
echo [1/5] Recording CPU topology...
powershell -NoProfile -c "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | Format-List" > results\topology.txt 2>&1
powershell -NoProfile -c "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | Format-List"

REM ---- 2. the SMT measurement --------------------------------
echo.
echo [2/5] SMT test: 2 threads on two cores vs 2 threads on one core...
for %%R in (1 2 3) do (
  echo    pass %%R of 3
  start /affinity 5 /b /wait cmd /c "scaling.exe 2 > results\smt_maskA_diffcores_run%%R.csv"
  start /affinity 3 /b /wait cmd /c "scaling.exe 2 > results\smt_maskB_samecore_run%%R.csv"
)

REM ---- 3. full scaling sweep ---------------------------------
echo.
echo [3/5] Full scaling sweep, 1 to 8 threads, 3 passes...
for %%R in (1 2 3) do (
  echo    pass %%R of 3
  scaling.exe 8 > results\scaling_run%%R.csv
)

REM ---- 4. per-core probe -------------------------------------
echo.
echo [4/5] Probing each physical core...
start /affinity 1 /b /wait cmd /c "probe.exe > results\probe_cpu0.csv"
start /affinity 4 /b /wait cmd /c "probe.exe > results\probe_cpu2.csv"

REM ---- 5. summary --------------------------------------------
echo.
echo [5/5] Summary
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File summarize.ps1

echo.
echo ============================================================
echo  DONE. Raw files are in the 'results' folder next to this
echo  script. They will sync back via Dropbox on their own --
echo  remember to UN-pause Dropbox.
echo ============================================================
pause
