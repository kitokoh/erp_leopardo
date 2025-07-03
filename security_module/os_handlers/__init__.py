# This file makes 'os_handlers' a package
# security_module/os_handlers/__init__.py

# You can selectively import handler classes here if you want to make them
# available like: from security_module.os_handlers import WindowsBiometricHandler
# However, biometric_auth.py will likely import them directly.

# For now, just marking it as a package.
from . import windows_handler
from . import macos_handler
from . import local_voice_handler
