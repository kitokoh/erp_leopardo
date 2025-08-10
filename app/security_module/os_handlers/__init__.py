# This file makes 'os_handlers' a package
# security_module/os_handlers/__init__.py

# You can selectively import handler classes here if you want to make them
# available like: from security_module.os_handlers import WindowsBiometricHandler
# However, biometric_auth.py will likely import them directly.

# For now, just marking it as a package.
# The individual OS handler modules (windows_handler, macos_handler)
# should be imported conditionally by the module that uses them (e.g., biometric_auth.py),
# not unconditionally here, to avoid cross-platform import errors.

# from . import windows_handler # Not strictly necessary here
# from . import macos_handler # This causes ModuleNotFoundError for 'objc' on Windows
# from . import local_voice_handler # Can be imported if it has no OS-specific deps itself
