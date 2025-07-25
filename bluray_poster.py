"""
Copyright (C) 2025 whitebrise

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version
"""

import logging
import os
import importlib
import time
from logging.handlers import TimedRotatingFileHandler
from configuration import Configuration
from abstract_classes import *


def setup_logging(log_level_str):
    """
    建立日志，滚动日志，每天一个日志文件，保留最近7天
    :return:
    """
    log_directory = 'logs'
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    logger = logging.getLogger()
    log_level = getattr(logging, log_level_str.upper(), logging.DEBUG)
    logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)


def dynamic_import(module_name, class_name):
    """
    动态导入
    :param module_name:
    :param class_name:
    :return:
    """
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise ImportError(f"Error importing module {module_name}: {e}")
    try:
        cls = getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Error importing class {class_name} from module {module_name}: {e}")
    return cls


def initialize_component(component_key, config, exception_class):
    """
    初始化指定组件
    :param component_key:
    :param config:
    :param exception_class:
    :return:
    """
    component_config = config.get(component_key)
    if component_config and "Executor" in component_config:
        try:
            module_name, class_name = component_config["Executor"].rsplit('.', 1)
            cls = dynamic_import(module_name, class_name)
            return cls(component_config)
        except Exception as e:
            logging.error(f"Error importing {component_key}: {e}")
    return None


def initialize_components(config):
    """
    初始化所有组件
    :param config:
    :return:
    """
    try:
        player = initialize_component("Player", config, PlayerException)
        tv = initialize_component("TV", config, TVException)
        av = initialize_component("AV", config, AVException)

        media_instances = []
        
        # Find all Media sections (Media, Media2, Media3, etc.)
        media_sections = []
        for key in config._config.keys():
            if key.startswith("Media"):
                media_sections.append(key)
        
        # Sort to ensure Media comes first, then Media2, Media3, etc.
        media_sections.sort()
        
        for section_name in media_sections:
            media_config = config.get(section_name)
            if media_config and "Executor" in media_config:
                try:
                    module_name, class_name = media_config["Executor"].rsplit('.', 1)
                    media_class = dynamic_import(module_name, class_name)
                    media = media_class(player, tv, av, media_config)
                    media_instances.append(media)
                    logging.info(f"{section_name} Media executor initialized successfully: {media_config['Executor']}")
                except Exception as e:
                    logging.error(f"Error initializing {section_name} Media executor ({media_config.get('Executor', 'Unknown')}): {e}")
            else:
                logging.warning(f"{section_name} Media executor is missing Executor field, skipping")
        
        if not media_instances:
            raise MediaException("Error initializing Media: No valid Media executors found.")
        
        logging.info(f"Successfully initialized {len(media_instances)} Media executor(s)")
        return media_instances

    except (PlayerException, TVException, AVException, MediaException) as e:
        logging.error(f"Initialization error: {e.message}")
        return None


if __name__ == "__main__":
    try:
        config_dir = os.getenv('CONFIG_DIR', 'config') + "/config.yaml"
        my_config = Configuration(path=config_dir)
        if my_config.initialize():
            setup_logging(my_config.get("LogLevel"))
            my_logger = logging.getLogger(__name__)
            my_logger.info("Starting the main application")
            
            media_instances = initialize_components(my_config)
            if media_instances is None:
                print("Failed to initialize Media components")
                exit(1)
            
            # Initialize all media instances
            for i, media in enumerate(media_instances):
                try:
                    media.start_before()
                    my_logger.info(f"Media executor {i+1} start_before() completed")
                except Exception as e:
                    my_logger.error(f"Error in Media executor {i+1} start_before(): {e}")
            
            # Start all media instances
            for i, media in enumerate(media_instances):
                try:
                    media.start()
                    my_logger.info(f"Media executor {i+1} start() completed")
                except Exception as e:
                    my_logger.error(f"Error in Media executor {i+1} start(): {e}")
            
            # Main loop - keep all media instances running
            my_logger.info(f"Main application running with {len(media_instances)} Media executor(s)")
            while True:
                time.sleep(100)
        else:
            print("Failed to initialize configuration")
    except Exception as ee:
        print("Failed to start program, ex: {}".format(ee))
