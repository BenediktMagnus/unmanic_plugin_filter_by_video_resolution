#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import ffmpeg

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger('Unmanic.Plugin.filter_by_video_resolution')

class Settings(PluginSettings):
    settings = {
        'every_condition_must_be_true': True, # TODO: Change this to a select box.
        'min_width': 0,
        'min_height': 0,
        'max_width': 0,
        'max_height': 0,
    }
    form_settings = {
        'every_condition_must_be_true': {
            'label': 'If set, only files that respect all limits are processed, otherwise a single limit is enough.',
        },
        'min_width': {
            'label': 'Minimum width (zero disables the minimum)',
        },
        'min_height': {
            'label': 'Minimum height (zero disables the minimum)',
        },
        'max_width': {
            'label': 'Maximum width (zero disables the maximum)',
        },
        'max_height': {
            'label': 'Maximum height (zero disables the maximum)',
        },
    }

def resolution_is_within_limits(settings: Settings, width: int, height: int) -> bool:
    min_width = int(settings.get_setting('min_width')) # type: ignore
    min_height = int(settings.get_setting('min_height')) # type: ignore
    max_width = int(settings.get_setting('max_width')) # type: ignore
    max_height = int(settings.get_setting('max_height')) # type: ignore

    every_condition_must_be_true: bool|None = settings.get_setting('every_condition_must_be_true') # type: ignore
    if every_condition_must_be_true is None:
        every_condition_must_be_true = True

    if every_condition_must_be_true:
        if min_width > 0 and width < min_width:
            return False
        if min_height > 0 and height < min_height:
            return False
        if max_width > 0 and width > max_width:
            return False
        if max_height > 0 and height > max_height:
            return False
        # If no condition is false, the resolution is within the limits:
        return True
    else:
        if min_width > 0 and width >= min_width:
            return True
        if min_height > 0 and height >= min_height:
            return True
        if max_width > 0 and width <= max_width:
            return True
        if max_height > 0 and height <= max_height:
            return True
        # If no condition is true, the result is only false if there has been any condition:
        return min_width == min_height == max_width == max_height == 0

def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.
        priority_score                  - Integer, an additional score that can be added to set the position of the new task in the task queue.
        shared_info                     - Dictionary, information provided by previous plugin runners. This can be appended to for subsequent runners.

    :param data:
    :return:

    """

    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    file_path = data.get('path')

    try:
        resolution = ffmpeg.probe(file_path, select_streams='v:0', show_entries='stream=width,height')

        width: int = resolution['streams'][0]['width']
        height: int = resolution['streams'][0]['height']
    except (ffmpeg.Error, AttributeError, IndexError):
        # Not a video file
        return

    if not resolution_is_within_limits(settings, width, height):
        data['add_file_to_pending_tasks'] = False
        data['issues'].append(
            {
                'id': 'Limit library search by video resolution',
                'message': f'Video resolution of file "{file_path}" is outside the limit of "{width}x{height}".',
            }
        )

    return data
