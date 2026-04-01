@echo off
:: MASTER TASK FIXER
:: Run this as Administrator
:: Replace PASSWORD with your Windows login password

set STUDIO=G:\My Drive\Projects\_studio
set SCHED=%STUDIO%\scheduler
set USER=jpalek
set PASS=!Vagrancy1

echo ==========================================
echo STEP 1 — Fix /RU account on existing tasks
echo ==========================================

schtasks /Change /TN "\Studio\AIIntel"             /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\CheckDrift"           /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\GitCommitNightly"     /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\Janitor"              /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\NightlyRollup"        /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\ProductArchaeology"   /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\SupervisorBriefing"   /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\VectorReindex"        /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\SupervisorCheck"      /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\SidebarBridge"        /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\AgentNightlyRollup"          /RU "%USER%" /RP "%PASS%"

echo.
echo ==========================================
echo STEP 2 — Update task command lines
echo ==========================================

schtasks /Change /TN "\Studio\VectorReindex" /TR "cmd /c \"%SCHED%\overnight-vector-reindex.bat\""
schtasks /Change /TN "\Studio\CheckDrift"    /TR "cmd /c \"%SCHED%\overnight-check-drift.bat\""
schtasks /Change /TN "\Studio\Janitor"       /TR "cmd /c \"%SCHED%\overnight-janitor.bat\""
schtasks /Change /TN "\Studio\GitCommitNightly" /TR "cmd /c \"%SCHED%\nightly-commit.bat\""
schtasks /Change /TN "\Studio\ProductArchaeology" /TR "cmd /c \"%SCHED%\overnight-product-archaeology.bat\""

echo.
echo ==========================================
echo STEP 3 — Re-enable disabled tasks
echo ==========================================

schtasks /Change /TN "\Studio\WhiteboardScorer"    /Enable /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\MonthlyJobDiscovery"  /Enable /RU "%USER%" /RP "%PASS%"
schtasks /Change /TN "\Studio\SidebarBridge"        /Enable /RU "%USER%" /RP "%PASS%"

echo.
echo ==========================================
echo STEP 4 — Park low-value Claude-dependent tasks
echo ==========================================

schtasks /Change /TN "\Studio\HeartbeatCheck"       /Disable
schtasks /Change /TN "\Studio\GitScout"             /Disable
schtasks /Change /TN "\Studio\WorkflowIntelligence" /Disable
schtasks /Change /TN "\Studio\IntelFeed"            /Disable
schtasks /Change /TN "\Studio\VedicScan"            /Disable
schtasks /Change /TN "\Studio\SupervisorBriefing"   /Disable
schtasks /Change /TN "\Studio\MirofishTest"         /Disable

echo.
echo ==========================================
echo STEP 5 — Keep intentionally parked
echo ==========================================
echo CommonCrawlTrigger - parked intentionally
echo WhiteboardAgent    - waiting on Agency characters
echo SkillImprover      - waiting on Agency characters
echo PeerReview         - waiting on Agency characters

echo.
echo Done. Run Task Scheduler to verify.
pause
