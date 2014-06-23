from ddtp.settings import *

DEBUG=True
TEMPLATE_DEBUG=DEBUG

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
#    'debug_toolbar.panels.sql.SQLPanel',
#    'debug_toolbar.panels.signals.SignalPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
)

