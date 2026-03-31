$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Bakes JSON data into sidebar-agent.html so it works without a server</Description></RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-03-31T06:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>BDCL991\jpalek</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c "G:\My Drive\Projects\_studio\scheduler\overnight-sidebar-inject.bat"</Arguments>
    </Exec>
  </Actions>
</Task>
"@
$tmp = [System.IO.Path]::Combine($env:TEMP, "sidebar_inject.xml")
[System.IO.File]::WriteAllText($tmp, $xml, [System.Text.Encoding]::Unicode)
$r = schtasks /Create /XML "$tmp" /TN "\Studio\SidebarInject" /F 2>&1
Write-Host $r
Remove-Item $tmp -ErrorAction SilentlyContinue
