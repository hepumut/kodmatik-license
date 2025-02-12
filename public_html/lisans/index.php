<?php
$api_url = "https://your-python-app.com"; // Python uygulamanızın çalışacağı adres

// Gelen isteği Python sunucusuna ilet
$endpoint = $_SERVER['REQUEST_URI'];
$method = $_SERVER['REQUEST_METHOD'];
$headers = getallheaders();
$body = file_get_contents('php://input');

// cURL isteği oluştur
$ch = curl_init($api_url . $endpoint);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

// Headers'ları ekle
$curlHeaders = [];
foreach($headers as $key => $value) {
    if($key != 'Host') {
        $curlHeaders[] = "$key: $value";
    }
}
curl_setopt($ch, CURLOPT_HTTPHEADER, $curlHeaders);

// POST/PUT body'sini ekle
if ($method == 'POST' || $method == 'PUT') {
    curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
}

// İsteği gönder ve yanıtı al
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);

// HTTP durum kodunu ayarla
http_response_code($httpCode);

// Content-Type header'ını ayarla
header("Content-Type: $contentType");

// Yanıtı gönder
echo $response;

curl_close($ch);
?> 