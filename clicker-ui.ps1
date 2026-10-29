Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

if (-not ('ClickerNative' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ClickerNative {
    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")]
    public static extern void mouse_event(uint flags, uint x, uint y, uint data, UIntPtr extra);
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
}

$script:target = $null
$script:pickAt = $null
$script:clickPoint = $null
$form = New-Object System.Windows.Forms.Form
$form.Text = 'Simple Autoclicker'
$form.ClientSize = New-Object System.Drawing.Size(440, 440)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox = $false
$form.AutoScaleMode = 'Dpi'
$form.BackColor = [System.Drawing.ColorTranslator]::FromHtml('#F3F6FA')
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$form.ForeColor = [System.Drawing.ColorTranslator]::FromHtml('#20334D')

function Add-Label($text, $x, $y, $width, $height) {
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $text
    $label.SetBounds($x, $y, $width, $height)
    $form.Controls.Add($label)
    return $label
}

$title = Add-Label 'One click. Right on time.' 24 22 390 36
$title.Font = New-Object System.Drawing.Font('Segoe UI Semibold', 18)
$null = Add-Label 'Schedule a single left click anywhere on your screen.' 24 65 395 25
$null = Add-Label 'Click time (24-hour)' 24 112 200 24
$time = New-Object System.Windows.Forms.DateTimePicker
$time.Format = 'Custom'
$time.CustomFormat = 'HH:mm:ss'
$time.ShowUpDown = $true
$time.Value = (Get-Date).AddMinutes(1)
$time.SetBounds(24, 140, 180, 30)
$form.Controls.Add($time)
$null = Add-Label 'Screen position' 24 188 300 24
$null = Add-Label 'X' 24 224 22 25
$null = Add-Label 'Y' 222 224 22 25
$xInput = New-Object System.Windows.Forms.NumericUpDown
$yInput = New-Object System.Windows.Forms.NumericUpDown
foreach ($inputBox in @($xInput, $yInput)) {
    $inputBox.Minimum = -100000
    $inputBox.Maximum = 100000
    $inputBox.ThousandsSeparator = $true
    $form.Controls.Add($inputBox)
}
$xInput.SetBounds(50, 220, 154, 30)
$yInput.SetBounds(248, 220, 164, 30)
$xInput.Value = [System.Windows.Forms.Cursor]::Position.X
$yInput.Value = [System.Windows.Forms.Cursor]::Position.Y

$pick = New-Object System.Windows.Forms.Button
$pick.Text = 'Pick position in 3 seconds'
$pick.SetBounds(24, 264, 388, 34)
$form.Controls.Add($pick)
$status = Add-Label 'Ready. Past times are scheduled for tomorrow.' 24 313 388 49
$status.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$start = New-Object System.Windows.Forms.Button
$start.Text = 'Schedule click'
$start.SetBounds(24, 377, 244, 40)
$start.BackColor = [System.Drawing.ColorTranslator]::FromHtml('#245DB5')
$start.ForeColor = [System.Drawing.Color]::White
$start.FlatStyle = 'Flat'
$start.FlatAppearance.BorderSize = 0
$form.Controls.Add($start)
$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = 'Cancel'
$cancel.SetBounds(280, 377, 132, 40)
$cancel.Enabled = $false
$form.Controls.Add($cancel)

function Set-EditingEnabled([bool]$enabled) {
    $time.Enabled = $enabled
    $xInput.Enabled = $enabled
    $yInput.Enabled = $enabled
    $pick.Enabled = $enabled
    $start.Enabled = $enabled
    $cancel.Enabled = -not $enabled
}

function Stop-Schedule {
    $script:target = $null
    $script:pickAt = $null
    [ClickerNative]::SetThreadExecutionState([uint32]2147483648) | Out-Null
    Set-EditingEnabled $true
    $pick.Text = 'Pick position in 3 seconds'
}

$pick.Add_Click({
    $script:pickAt = (Get-Date).AddSeconds(3)
    Set-EditingEnabled $false
    $status.Text = 'Move your pointer to the target. Capturing in 3 seconds...'
})

$start.Add_Click({
    $point = New-Object System.Drawing.Point([int]$xInput.Value, [int]$yInput.Value)
    $onScreen = $false
    foreach ($screen in [System.Windows.Forms.Screen]::AllScreens) {
        if ($screen.Bounds.Contains($point)) { $onScreen = $true }
    }
    if (-not $onScreen) {
        $status.Text = 'That position is outside your screens. Pick a position again.'
        return
    }
    $now = Get-Date
    $script:target = $now.Date.Add($time.Value.TimeOfDay)
    if ($script:target -le $now) { $script:target = $script:target.AddDays(1) }
    $script:clickPoint = $point
    if ([ClickerNative]::SetThreadExecutionState([uint32]2147483651) -eq 0) {
        $script:target = $null
        $status.Text = 'Could not keep the computer awake. Try scheduling again.'
        return
    }
    Set-EditingEnabled $false
    $status.Text = "Scheduled for $($script:target.ToString('ddd, MMM d HH:mm:ss'))."
})

$cancel.Add_Click({
    Stop-Schedule
    $status.Text = 'Cancelled. Ready for a new schedule.'
})

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 50
$timer.Add_Tick({
    $now = Get-Date
    if ($null -ne $script:pickAt) {
        if ($now -ge $script:pickAt) {
            $point = [System.Windows.Forms.Cursor]::Position
            $xInput.Value = $point.X
            $yInput.Value = $point.Y
            Stop-Schedule
            $status.Text = "Position captured: X=$($point.X), Y=$($point.Y)."
        }
        return
    }
    if ($null -eq $script:target) { return }
    if ($now -lt $script:target) {
        $remaining = $script:target - $now
        $status.Text = "Click at $($script:target.ToString('ddd, MMM d HH:mm:ss'))`r`n$($remaining.ToString('hh\:mm\:ss')) remaining - keep this window open."
        return
    }
    # Clear the schedule before clicking so a later tick cannot click twice.
    $script:target = $null
    try {
        if (-not [ClickerNative]::SetCursorPos($script:clickPoint.X, $script:clickPoint.Y)) {
            throw 'Could not move the pointer. Pick a position and try again.'
        }
        [ClickerNative]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
        [ClickerNative]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
        $status.Text = "Click completed at $($now.ToString('HH:mm:ss'))."
    }
    catch { $status.Text = $_.Exception.Message }
    finally { Stop-Schedule }
})
$form.Add_FormClosing({ Stop-Schedule })
$timer.Start()
try { [void]$form.ShowDialog() }
finally {
    $timer.Stop()
    $timer.Dispose()
    Stop-Schedule
    $form.Dispose()
}
