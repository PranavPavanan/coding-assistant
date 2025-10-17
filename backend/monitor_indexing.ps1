# PowerShell script to monitor indexing progress with visual progress bar
param(
    [Parameter(Mandatory=$true)]
    [string]$TaskId,
    [string]$BaseUrl = "http://localhost:8000"
)

function Show-ProgressBar {
    param(
        [int]$Percentage,
        [int]$Width = 50
    )
    
    $filled = [math]::Floor($Width * $Percentage / 100)
    $bar = "█" * $filled + "░" * ($Width - $filled)
    return "[$bar] $($Percentage.ToString('F1'))%"
}

function Format-Time {
    param([double]$Seconds)
    
    if ($Seconds -eq $null) { return "Unknown" }
    
    if ($Seconds -lt 60) {
        return "$($Seconds.ToString('F1'))s"
    } elseif ($Seconds -lt 3600) {
        return "$(($Seconds/60).ToString('F1'))m"
    } else {
        return "$(($Seconds/3600).ToString('F1'))h"
    }
}

function Clear-Screen {
    Clear-Host
}

Write-Host "🔍 Monitoring indexing task: $TaskId" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

$statusUrl = "$BaseUrl/api/index/status/$TaskId"
$startTime = Get-Date

try {
    while ($true) {
        try {
            $response = Invoke-RestMethod -Uri $statusUrl -Method Get -TimeoutSec 5
            $status = $response
            
            # Clear screen and show header
            Clear-Screen
            Write-Host "🔍 Indexing Monitor - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
            Write-Host "=" * 60 -ForegroundColor Gray
            Write-Host "Task ID: $TaskId" -ForegroundColor White
            Write-Host "Repository: $($status.repository_url)" -ForegroundColor White
            Write-Host "Status: $($status.status.ToUpper())" -ForegroundColor $(if ($status.status -eq 'completed') { 'Green' } elseif ($status.status -eq 'failed') { 'Red' } else { 'Yellow' })
            Write-Host ""
            
            # Show progress information
            if ($status.progress) {
                $progress = $status.progress
                $filesProcessed = $progress.files_processed
                $totalFiles = $progress.total_files
                $percentage = $progress.percentage
                $currentFile = $progress.current_file
                $bytesProcessed = $progress.bytes_processed
                $elapsedTime = $progress.elapsed_time
                $estimatedRemaining = $progress.estimated_remaining
                
                # Progress bar
                Write-Host "📊 Progress:" -ForegroundColor Cyan
                Write-Host "  $(Show-ProgressBar -Percentage $percentage)" -ForegroundColor Green
                Write-Host ""
                
                # File processing info
                if ($totalFiles -gt 0) {
                    Write-Host "📁 Files: $filesProcessed/$totalFiles" -ForegroundColor White
                    if ($currentFile) {
                        Write-Host "📄 Current: $currentFile" -ForegroundColor Gray
                    }
                    Write-Host "💾 Bytes: $($bytesProcessed.ToString('N0'))" -ForegroundColor White
                    Write-Host ""
                }
                
                # Time information
                if ($elapsedTime -ne $null) {
                    Write-Host "⏱️  Elapsed: $(Format-Time -Seconds $elapsedTime)" -ForegroundColor White
                    if ($estimatedRemaining -ne $null) {
                        Write-Host "⏳ Remaining: $(Format-Time -Seconds $estimatedRemaining)" -ForegroundColor White
                    }
                    Write-Host ""
                }
            }
            
            # Show message
            if ($status.message) {
                Write-Host "💬 $($status.message)" -ForegroundColor Cyan
                Write-Host ""
            }
            
            # Check if completed or failed
            $statusType = $status.status
            if ($statusType -eq 'completed') {
                Write-Host "✅ INDEXING COMPLETED SUCCESSFULLY!" -ForegroundColor Green
                if ($status.result) {
                    $result = $status.result
                    Write-Host "   Files processed: $($result.files_processed)" -ForegroundColor White
                    Write-Host "   Total bytes: $($result.total_bytes.ToString('N0'))" -ForegroundColor White
                    Write-Host "   Processing time: $(Format-Time -Seconds $result.processing_time)" -ForegroundColor White
                }
                break
            } elseif ($statusType -eq 'failed') {
                Write-Host "❌ INDEXING FAILED!" -ForegroundColor Red
                $error = $status.error
                if ($error) {
                    Write-Host "   Error: $error" -ForegroundColor Red
                }
                break
            }
            
            # Show last update time
            Write-Host "🔄 Last update: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
            Write-Host "   Press Ctrl+C to stop monitoring" -ForegroundColor Gray
            
            Start-Sleep -Seconds 1  # Update every second
            
        } catch {
            Write-Host "❌ Error fetching status: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "   Retrying in 5 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }
} catch {
    Write-Host "❌ Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

