; Uygulama tanımlamaları
#define MyAppName "Bilist co. OtoForm"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Bilist Yazılım"
#define MyAppURL "https://www.bilistco.com"
#define MyAppExeName "Optik Form Editörü.exe"

[Setup]
; Temel kurulum ayarları
AppId={{5F94C7D3-B0F4-4E82-9D7E-6BFA3C3B9F4A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Setup
OutputBaseFilename=OtoForm_Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
; ... diğer dosyalar ...
Source: "client\license_manager.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "client\license_dialog.py"; DestDir: "{app}"; Flags: ignoreversion

[Files]
Source: "license_manager.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "license_dialog.py"; DestDir: "{app}"; Flags: ignoreversion
; ... diğer dosyalar ...

[Code]
// ... diğer kodlar ...

// Deneme sürümü için lisans oluştur
procedure CreateTrialLicense();
var
  LicensePath: string;
begin
  LicensePath := ExpandConstant('{userappdata}\Bilist co. OtoForm\.license');
  if not FileExists(LicensePath) then
  begin
    try
      SaveStringToFile(LicensePath, '{"trial": true}', False);
    except
      // Hata durumunda sessizce devam et
    end;
  end;
end;

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Dirs]
Name: "{userdocs}\Bilist co. OtoForm"; Flags: uninsalwaysuninstall

[UninstallDelete]
Type: filesandordirs; Name: "{userdocs}\Bilist co. OtoForm"

; Dosya kopyalama işlemleri
[Files]
; Ana uygulama dosyaları
Source: "dist\Optik Form Editörü\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Visual C++ Redistributable - doğrudan ana klasörden
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; Kısayol oluşturma
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Kaldır"; Filename: "{uninstallexe}"

; Ek görevler
[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"

; Visual C++ Redistributable kontrolü
[Code]
function VCRedistInstalled(): Boolean;
begin
    Result := RegKeyExists(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64') or
              RegKeyExists(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64');
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  ErrorCode: Integer;
begin
  Result := True;
  
  if not VCRedistInstalled() then
  begin
    if MsgBox('Bu uygulama için Visual C++ 2015-2022 Redistributable gereklidir. Şimdi yüklensin mi?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      ExtractTemporaryFile('vc_redist.x64.exe');
      if not Exec(ExpandConstant('{tmp}\vc_redist.x64.exe'), '/quiet /norestart',
        '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        ErrorCode := DLLGetLastError;
        MsgBox('Visual C++ Redistributable kurulumu başlatılamadı. ' + 
          SysErrorMessage(ErrorCode), mbError, MB_OK);
        Result := False;
      end
      else if not VCRedistInstalled() then
      begin
        MsgBox('Visual C++ Redistributable kurulumu başarısız oldu. ' +
          'Lütfen manuel olarak kurun.', mbError, MB_OK);
        Result := False;
      end;
    end
    else
      Result := False;
  end;
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Programı şimdi başlat"; Flags: nowait postinstall skipifsilent