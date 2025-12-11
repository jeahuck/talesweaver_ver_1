$ws = New-Object System.Net.HttpListener
$ws.Prefixes.Add("http://localhost:5000/")
$ws.Start()
Write-Host "OCR Server started on http://localhost:5000"

while ($true) {
    $context = $ws.GetContext()
    $request = $context.Request
    $response = $context.Response

    $reader = New-Object System.IO.StreamReader($request.InputStream)
    $json = $reader.ReadToEnd() | ConvertFrom-Json

    $imgPath = $json.path

    # PowerToys OCR API 대신 Windows OCR 있으면 사용
    Add-Type -AssemblyName Windows.Win32
    $ocr = [Windows.Win32.System.Ocr.OcrEngine]::TryCreateFromLanguage("ko-KR")

    $bitmap = [Windows.Win32.System.Imaging.SoftwareBitmap]::LoadFromFileAsync($imgPath).GetAwaiter().GetResult()
    $result = $ocr.RecognizeAsync($bitmap).GetAwaiter().GetResult()

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($result.Text)
    $response.ContentLength64 = $bytes.Length
    $response.OutputStream.Write($bytes, 0, $bytes.Length)
    $response.OutputStream.Close()
}