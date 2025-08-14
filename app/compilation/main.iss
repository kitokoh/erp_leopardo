; --- Inno Setup Script for Leopardo AI ---
; This script is modernized to be driven by an external build script.

; --- Dynamic Application Information ---
; These values are expected to be passed by the build script using /DName=Value
#ifndef MyAppName
  #define public MyAppName "Leopardo AI (Dev Build)"
#endif
#ifndef MyAppVersion
  #define public MyAppVersion "0.0.0"
#endif
#ifndef MyAppPublisher
  #define public MyAppPublisher "My Company"
#endif
#ifndef MyAppURL
  #define public MyAppURL "https://example.com"
#endif
#ifndef MyAppExeName
  #define public MyAppExeName "Leopardo AI.exe"
#endif
#ifndef SourceDir
  #define public SourceDir "dist"
#endif
#ifndef InstallerOutputDir
  #define public InstallerOutputDir "dist/installer"
#endif
#ifndef AppIcon
    #define public AppIcon "app/resources/icons/nova360.ico"
#endif

; --- Setup Section ---
[Setup]
AppId={{6DE0F7C2-28A6-4695-941A-5D96CD9555CD}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=Leopardo-AI-{#MyAppVersion}-Setup
OutputDir={#InstallerOutputDir}
SetupIconFile={#AppIcon}
UninstallDisplayIcon={#AppIcon}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

; --- Languages Section ---
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

; --- Tasks Section ---
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; --- Files Section ---
[Files]
; Main application executable and all its bundled contents
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Icons Section ---
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoquicklaunch}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; --- Run Section ---
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
