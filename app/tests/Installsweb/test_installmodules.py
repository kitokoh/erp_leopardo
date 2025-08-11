from app.addons.widgets import AddonsPage

def test_installer_dialog_instantiation():
    """Test that InstallerDialog can be instantiated."""
    # This is a very basic test that only checks if the class can be instantiated
    # without a QApplication instance. This is not a good test, but it's a start
    # to debug the CI environment.
    dialog = AddonsPage()
    assert dialog is not None
