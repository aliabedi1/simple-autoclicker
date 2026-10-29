
# ======================================
# Scheduled Mouse Clicker
# ======================================

# Settings
$hour = 4
$minute = 49
$x = 1426
$y = 978

# Load Windows mouse API
if (-not ("Mouse" -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public class Mouse {
    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(
        uint f, uint x, uint y, uint d, UIntPtr e);

    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint f);
}
'@
}

# Calculate next scheduled time
$target = (Get-Date).Date.AddHours($hour).AddMinutes($minute)

if ($target -le (Get-Date)) {
    $target = $target.AddDays(1)
}

# Prevent automatic sleep and display shutdown
[Mouse]::SetThreadExecutionState([uint32]2147483651) | Out-Null

Write-Host "================================="
Write-Host "Scheduled Mouse Clicker"
Write-Host "================================="
Write-Host "Target: $target"
Write-Host "Position: X=$x, Y=$y"
Write-Host "Action: Single Left Click"
Write-Host "Press Ctrl+C to cancel"
Write-Host "================================="

try {
    # Wait until target time
    while ((Get-Date) -lt $target) {
        Start-Sleep -Milliseconds 50
    }

    # Move mouse
    if (-not [Mouse]::SetCursorPos($x, $y)) {
        throw "Could not move the cursor."
    }

    Start-Sleep -Milliseconds 50

    # Left mouse button DOWN
    [Mouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)

    Start-Sleep -Milliseconds 80

    # Left mouse button UP
    [Mouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)

    Write-Host "Click completed at $(Get-Date)"
}
finally {
    # Restore normal power behavior
    [Mouse]::SetThreadExecutionState([uint32]2147483648) | Out-Null
}
