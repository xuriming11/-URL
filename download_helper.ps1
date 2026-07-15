# Resumable download script (HTTP Range requests)
param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$OutFile
)

$tempFile = "$OutFile.part"
$startTime = Get-Date

Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromSeconds(60)

$maxRetries = 50
$attempt = 0

while ($attempt -lt $maxRetries) {
    $existingBytes = 0
    if (Test-Path $tempFile) {
        $existingBytes = (Get-Item $tempFile).Length
    }

    $attempt++
    Write-Host "Attempt #$attempt  starting from byte $existingBytes..."

    try {
        $request = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::Get, $Url)
        if ($existingBytes -gt 0) {
            $request.Headers.Add("Range", "bytes=$existingBytes-")
        }

        $response = $client.SendAsync($request, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).Result

        $totalBytes = 0
        if ($response.Content.Headers.ContentRange -ne $null) {
            $totalBytes = $response.Content.Headers.ContentRange.Length.Value
        } elseif ($existingBytes -eq 0 -and $response.Content.Headers.ContentLength -ne $null) {
            $totalBytes = $response.Content.Headers.ContentLength.Value
        }

        $stream = $response.Content.ReadAsStreamAsync().Result
        $fileStream = [System.IO.File]::Open($tempFile, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
        $buffer = New-Object byte[] 262144
        $lastReport = 0

        while ($true) {
            $read = $stream.Read($buffer, 0, $buffer.Length)
            if ($read -le 0) { break }
            $fileStream.Write($buffer, 0, $read)
            $existingBytes += $read
            if (($existingBytes - $lastReport) -gt 10485760) {
                $pct = if ($totalBytes -gt 0) { [math]::Round($existingBytes / $totalBytes * 100, 1) } else { 0 }
                Write-Host "  Downloaded $([math]::Round($existingBytes/1MB,1)) MB / $([math]::Round($totalBytes/1MB,1)) MB ($pct%)"
                $lastReport = $existingBytes
            }
        }

        $fileStream.Close()
        $stream.Close()
        $response.Dispose()

        if (Test-Path $OutFile) { Remove-Item $OutFile }
        Rename-Item -Path $tempFile -NewName $OutFile -Force
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        Write-Host "DONE! Size: $([math]::Round((Get-Item $OutFile).Length/1MB,1)) MB, Time: $([math]::Round($elapsed,1)) s"
        exit 0
    }
    catch {
        Write-Host "  Interrupted: $($_.Exception.Message)"
        if (Test-Path $tempFile) {
            Write-Host "  Saved $([math]::Round((Get-Item $tempFile).Length/1MB,1)) MB, will retry..."
        }
        Start-Sleep -Seconds 2
    }
}

Write-Host "FAILED: max retries reached"
exit 1
