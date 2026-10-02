# Run from the repository root. Windows System.Speech + wav2wem v0.1.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$dialogue = Get-Content src/dialogue.json -Raw | ConvertFrom-Json
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speech.SelectVoice('Microsoft Mark')
    $speech.Rate = -1
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $speech.SetOutputToWaveFile((Join-Path $PWD 'src/audio/reed_reassurance.wav'), $format)
    $speech.Speak($dialogue.lines.'1281')
} finally {
    $speech.Dispose()
}
& .tools/wav2wem.exe src/audio/reed_reassurance.wav -o src/audio/reed_reassurance.wem
if ($LASTEXITCODE -ne 0) { throw 'WEM conversion failed' }
