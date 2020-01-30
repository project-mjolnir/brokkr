# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 00:53:56 2020

@author: C. A. M. Gerlach
"""

# Local imports
import brokkr.config.handlers


# Unit config dict
UNIT_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_UNIT
UNIT_CONFIGS = UNIT_CONFIG_HANDLER.read_configs()
UNIT_CONFIG = UNIT_CONFIG_HANDLER.render_config(UNIT_CONFIGS)


# Logging config dict
LOG_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_LOG
LOG_CONFIGS = LOG_CONFIG_HANDLER.read_configs()
LOG_CONFIG = LOG_CONFIG_HANDLER.render_config(LOG_CONFIGS)


# Metadata config dict
METADATA_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_METADATA
METADATA_CONFIGS = METADATA_CONFIG_HANDLER.read_configs()
METADATA_CONFIG = METADATA_CONFIG_HANDLER.render_config(METADATA_CONFIGS)
