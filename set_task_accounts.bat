@echo off
echo Updating task user accounts - run this as Administrator
echo Replace PASSWORD with your Windows login password
echo.

schtasks /Change /TN "\Studio\WhiteboardAgent"    /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\WhiteboardScorer"   /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\SkillImprover"      /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\PeerReview"         /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\MonthlyJobDiscovery" /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\CheckDrift"         /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\Janitor"            /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\AIIntel"            /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\VectorReindex"      /RU "jpalek" /RP "PASSWORD"
schtasks /Change /TN "\Studio\SidebarBridge"      /RU "jpalek" /RP "PASSWORD"

echo.
echo Done. Check Task Scheduler for status.
pause
