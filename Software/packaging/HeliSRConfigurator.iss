; HeliSR Configurator installer (Inno Setup 6). Built by build-release.ps1,
; which passes the defines below:
;   AppVersion   e.g. 1.0.0
;   StageDir     the deployed app: exe, Qt DLLs, firmware, avrdude, licences
;   SourceDir    the repo's Software folder (for the icon)
;   OutputDir    where the installer goes
;   OutputName   its file name, without .exe
; Based on FreeJoyConfiguratorQt's Inno Setup script.

#ifndef AppVersion
  #error Build with build-release.ps1 (AppVersion isn't defined)
#endif

#define MyAppName "HeliSR Configurator"
#define MyAppExeName "HeliSRConfigurator.exe"
#define MyAppURL "https://github.com/genbean/UH1-Collective"

[Setup]
; HeliSR's own AppId (FreeJoy's installer has a different one, so the two never mix)
AppId={{1DA595D7-6408-4F15-A574-691EFF97C1FA}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} {#AppVersion}
AppPublisher=HeliSR contributors
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; installs for the current user without admin rights; an admin can choose all users
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile={#StageDir}\licenses\GPL-3.0.txt
OutputDir={#OutputDir}
OutputBaseFilename={#OutputName}
SetupIconFile={#SourceDir}\configurator\src\Images\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Qt 6 needs 64-bit Windows 10 or later
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; an update replaces the whole Qt deployment, so no stale plugins are left behind
Type: filesandordirs; Name: "{app}\platforms"
Type: filesandordirs; Name: "{app}\styles"
Type: filesandordirs; Name: "{app}\imageformats"
Type: filesandordirs; Name: "{app}\iconengines"
Type: filesandordirs; Name: "{app}\firmware"
Type: filesandordirs; Name: "{app}\profiles"

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
