$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-04-01T00:00:00</Date>
    <Author>BDCL991\jpalek</Author>
    <Description>Monthly job source discovery - rebuilds job-source-registry.json from all boards and CDX. Runs 1st of each month at 2 AM.</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-04-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <DaysOfMonth>
          <Day>1</Day>
        </DaysOfMonth>
        <Months>
          <January />
          <February />
          <March />
          <April />
          <May />
          <June />
          <July />
          <August />
          <September />
          <October />
          <November />
          <December />
        </Months>
      </ScheduleByMonth>
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
    <ExecutionTimeLimit>PT4H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c "G:\My Drive\Projects\_studio\scheduler\monthly-job-discovery.bat"</Arguments>
      <WorkingDirectory>G:\My Drive\Projects\job-match\</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$tmpXml = [System.IO.Path]::Combine($env:TEMP, "monthly_job_discovery.xml")
[System.IO.File]::WriteAllText($tmpXml, $xml, [System.Text.Encoding]::Unicode)
Write-Host "XML written to $tmpXml"
$result = schtasks /Create /XML "$tmpXml" /TN "\Studio\MonthlyJobDiscovery" /F 2>&1
Write-Host $result
Remove-Item $tmpXml -ErrorAction SilentlyContinue
Write-Host "Done"
