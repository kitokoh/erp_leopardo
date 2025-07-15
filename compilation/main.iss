; --- Inno Setup Script for Leopardo AI ---
; This script is used to create a Windows installer for the Leopardo AI application.

; --- Application Information ---
#define MyAppName "Leopardo AI"
#define MyAppVersion "1.9"
#define MyAppPublisher "Leopardo, Inc."
#define MyAppURL "https://www.leopardo.com/"
#define MyAppExeName "main.exe"
#define MyAppDataDir "saadiya"

; --- File Associations ---
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".myp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

; --- Paths ---
#define ResourcesDir "resources"
#define OutputDir "LeopardoAI-Installer"
#define LicenseFile "compil\licence.txt"
#define BeforeInstallFile "compil\beforinstall.txt"
#define AfterInstallFile "compil\afterinstall.txt"

; --- Setup Section ---
[Setup]
; Unique App ID
AppId={{6DE0F7C2-28A6-4695-941A-5D96CD9555CD}}
; Application Name and Version
AppName={#MyAppName}
AppVersion={#MyAppVersion}
; Publisher Information
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Installation Directory
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName=
; Architecture
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64 arm64
; Other Settings
ChangesAssociations=yes
DisableProgramGroupPage=yes
LicenseFile={#LicenseFile}
InfoBeforeFile={#BeforeInstallFile}
InfoAfterFile={#AfterInstallFile}
OutputBaseFilename=Leopardo-ai
SetupIconFile=resources\icons\robot-icons-30504-Windows.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
AppCopyright=Copyright © 2025 {#MyAppPublisher}. All rights reserved.
MinVersion=10.0.0
AlwaysShowDirOnReadyPage=yes
PrivilegesRequired=admin
OutputManifestFile=setup.log
UninstallDisplayIcon=resources\robot-icons-30504-Windows.ico
OutputDir={#OutputDir}
UninstallDisplayName={#MyAppName} v{#MyAppVersion} Uninstall
; Custom window images
WizardImageFile=resources\icons\robot-icons-30504.bmp
WizardSmallImageFile=resources\icons\robot-icons-30504.bmp

; --- Messages Section ---
[Messages]
BeveledLabel=Leopardo: Simplify your marketing with AI!
WelcomeLabel=Welcome to the Leopardo AI v{#MyAppVersion} Setup.
StatusInstalling=Installing...
StatusDownloaded=Download completed for %s
ButtonInstall=Start Installation
ButtonFinish=Finish and Launch Leopardo AI

; --- Languages Section ---
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "armenian"; MessagesFile: "compiler:Languages\Armenian.isl"
Name: "bulgarian"; MessagesFile: "compiler:Languages\Bulgarian.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "corsican"; MessagesFile: "compiler:Languages\Corsican.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "icelandic"; MessagesFile: "compiler:Languages\Icelandic.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "slovak"; MessagesFile: "compiler:Languages\Slovak.isl"
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

; --- Tasks Section ---
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon"; Description: "{cm:CreateStartMenuIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "allusers"; Description: "Install for all users"; GroupDescription: "Installation Type:"; Flags: exclusive
Name: "currentuser"; Description: "Install for current user only"; GroupDescription: "Installation Type:"; Flags: exclusive unchecked

; --- Files Section ---
[Files]
; Application executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Application resources
Source: "{#ResourcesDir}\*"; DestDir: "{app}\{#ResourcesDir}"; Flags: ignoreversion recursesubdirs createallsubdirs
; User data
Source: "{#ResourcesDir}\data\*"; DestDir: "{userappdata}\{#MyAppDataDir}\resources\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ResourcesDir}\demoData\*"; DestDir: "{userappdata}\{#MyAppDataDir}\resources\demoData"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "lesClesNova360\icons\exeCle\*"; DestDir: "{userappdata}\{#MyAppDataDir}\resources\tools"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ResourcesDir}\wademoData\*"; DestDir: "{userappdata}\{#MyAppDataDir}\resources\wademoData"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ResourcesDir}\key.key"; DestDir: "{userappdata}\{#MyAppDataDir}\resources\"; Flags: ignoreversion
Source: "{#ResourcesDir}\settings.json"; DestDir: "{userappdata}\{#MyAppDataDir}\resources"; Flags: ignoreversion
Source: "{#ResourcesDir}\lang\*"; DestDir: "{userappdata}\{#MyAppDataDir}\resources\lang"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ResourcesDir}\lang.json"; DestDir: "{userappdata}\{#MyAppDataDir}\resources"; Flags: ignoreversion
Source: "nova360.ico"; DestDir: "{app}"; Flags: ignoreversion

; --- Code Section ---
[Code]
const
    PythonURL = 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe';
    GitURL = 'https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.1/Git-2.42.0-64-bit.exe';

var
    TempDir: String;

function IsDependencyInstalled(command: String; version: String): Boolean;
var
    ResultCode: Integer;
    VersionOutput: String;
    VersionFile: String;
    FileContents: TStringList;
begin
    if not DirExists(TempDir) then
        ForceDirectories(TempDir);

    VersionFile := TempDir + '\version.txt';

    if Exec('cmd.exe', '/C ' + command + ' > "' + VersionFile + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
        if FileExists(VersionFile) then
        begin
            FileContents := TStringList.Create;
            try
                FileContents.LoadFromFile(VersionFile);
                VersionOutput := FileContents.Text;
                Result := Pos(version, VersionOutput) > 0;
            finally
                FileContents.Free;
            end;
        end
        else
        begin
            Log('Error: Version file does not exist.');
            Result := False;
        end;
    end
    else
    begin
        Log('Error: Could not execute command: ' + command);
        Result := False;
    end;
end;

procedure InitializeWizard();
begin
    TempDir := ExpandConstant('{tmp}') + '\InstallDependencies';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
    if CurPageID = wpReady then
    begin
        if not IsDependencyInstalled('python --version', '3.11') then
        begin
            MsgBox('Python 3.11 is not installed. Please install it before continuing.', mbError, MB_OK);
            Result := False;
        end
        else if not IsDependencyInstalled('git --version', '2.42') then
        begin
            MsgBox('Git 2.42 is not installed. Please install it before continuing.', mbError, MB_OK);
            Result := False;
        end
        else
        begin
            Result := True;
        end;
    end
    else
    begin
        Result := True;
    end;
end;


; --- Registry Section ---
[Registry]
; File Association
Root: HKLM; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKLM; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKLM; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKLM; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".myp"; ValueData: ""
; Application Settings
Root: HKLM; Subkey: "Software\MyApp"; ValueType: string; ValueName: "Config"; ValueData: "Data"; Tasks: allusers
Root: HKLM; Subkey: "Software\{#MyAppName}\AutoUpdate"; ValueType: string; ValueName: "Enabled"; ValueData: "True"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Language"; ValueData: "fr"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppName}\UsageStats"; ValueType: dword; ValueName: "LaunchCount"; ValueData: "0"; Flags: uninsdeletekey

; --- Icons Section ---
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; --- Run Section ---
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

; --- UninstallDelete Section ---
[UninstallDelete]
Type: files; Name: "{app}\temp\*.*"

; --- CustomMessages Section ---
[CustomMessages]
CreateShortcutsMsg=Would you like to create desktop and start menu shortcuts?
EnableLogAnalysis=Do you want to enable installation log analysis?
ControlCenterIntegration=Integrate with the remote control center for easier management?
SelectLogLocation=Please choose a location to save the installation logs.
EnableAPIAccess=Enable API access for third-party integrations?
AdditionalComponents=Would you like to install additional components for extended functionality?
EnableAutoUpdate=Do you want to enable automatic updates for future versions?
CompatWarning=This software may not be fully compatible with Windows versions older than 10.
CustomizeAppearance=Would you like to customize the application's appearance after installation?
