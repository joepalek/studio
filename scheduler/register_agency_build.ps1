$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-03-31T00:00:00</Date>
    <Author>BDCL991\jpalek</Author>
    <Description>Agency character batch builder -- promotes passing specs into full character folders. Runs after spec grader completes.</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-03-31T05:30:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
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
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c "G:\My Drive\Projects\_studio\scheduler\overnight-agency-build.bat"</Arguments>
      <WorkingDirectory>G:\My Drive\Projects\_studio\agency\</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$tmpXml = [System.IO.Path]::Combine($env:TEMP, "agency_build.xml")
[System.IO.File]::WriteAllText($tmpXml, $xml, [System.Text.Encoding]::Unicode)
$result = schtasks /Create /XML "$tmpXml" /TN "\Studio\AgencyCharacterBuild" /F 2>&1
Write-Host $result
Remove-Item $tmpXml -ErrorAction SilentlyContinue
Write-Host "Done"
