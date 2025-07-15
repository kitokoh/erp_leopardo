; --- Inno Setup Script for Leopardo AI ---
; This script is used to create a Windows installer for the Leopardo AI application.

; --- Application Information ---
#define MyAppName "Leopardo AI"
#define MyAppVersion "1.9.0"
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
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

; --- Tasks Section ---
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon"; Description: "{cm:CreateStartMenuIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "allusers"; Description: "Install for all users"; GroupDescription: "Installation Type:"; Flags: exclusive
Name: "currentuser"; Description: "Install for current user only"; GroupDescription: "Installation Type:"; Flags: exclusive unchecked
Name: "installPython"; Description: "Install Python 3.11"; GroupDescription: "Optional Components";
Name: "installGit"; Description: "Install Git 2.42"; GroupDescription: "Optional Components";

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
    ComponentsPage: TNewCheckListBox;
    ProgressBar: TProgressBar;

procedure DownloadAndInstall(URL: String; FileName: String);
var
    ResultCode: Integer;
begin
    if not DownloadFile(URL, FileName, ProgressBar) then
    begin
        MsgBox('Failed to download ' + FileName, mbError, MB_OK);
        exit;
    end;

    if not Exec(FileName, '/quiet', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
    begin
        MsgBox('Failed to install ' + FileName, mbError, MB_OK);
        exit;
    end;
end;

function IsDependencyInstalled(command: String; version: String): Boolean;
var
    ResultCode: Integer;
    VersionOutput: String;
    VersionFile: String;
    FileContents: TStringList;
begin
    VersionFile := ExpandConstant('{tmp}\version.txt');
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
            Result := False;
    end
    else
        Result := False;
end;

procedure InitializeWizard();
begin
    ComponentsPage := TNewCheckListBox.Create(WizardForm);
    ComponentsPage.Parent := WizardForm.SelectComponentsPage;
    ComponentsPage.Top := 0;
    ComponentsPage.Left := 0;
    ComponentsPage.Width := WizardForm.SelectComponentsPage.ClientWidth;
    ComponentsPage.Height := WizardForm.SelectComponentsPage.ClientHeight;
    ComponentsPage.AddCheckBox('Install Python 3.11', '', 0, True, True, False, True, nil);
    ComponentsPage.AddCheckBox('Install Git 2.42', '', 0, True, True, False, True, nil);

    ProgressBar := TProgressBar.Create(WizardForm);
    ProgressBar.Parent := WizardForm;
    ProgressBar.Top := WizardForm.ClientHeight - 50;
    ProgressBar.Left := 10;
    ProgressBar.Width := WizardForm.ClientWidth - 20;
    ProgressBar.Height := 15;
    ProgressBar.Visible := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
    PythonInstalled: Boolean;
    GitInstalled: Boolean;
begin
    if CurPageID = wpReady then
    begin
        PythonInstalled := IsDependencyInstalled('python --version', '3.11');
        GitInstalled := IsDependencyInstalled('git --version', '2.42');

        if ComponentsPage.Checked[0] and not PythonInstalled then
        begin
            ProgressBar.Visible := True;
            DownloadAndInstall(PythonURL, 'python_installer.exe');
            ProgressBar.Visible := False;
        end;

        if ComponentsPage.Checked[1] and not GitInstalled then
        begin
            ProgressBar.Visible := True;
            DownloadAndInstall(GitURL, 'git_installer.exe');
            ProgressBar.Visible := False;
        end;
    end;
    Result := True;
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
