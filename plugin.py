#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import ffmpeg

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger('Unmanic.Plugin.filter_by_video_resolution')

class Settings(PluginSettings):
    settings = {
        'min_width': 0,
        'min_height': 0,
        'max_width': 0,
        'max_height': 0,
    }
    form_settings = {
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

def resolution_is_within_limits(width: int, height: int) -> bool:
    settings = Settings()

    min_width: int = settings.get_setting('min_width') or 0 # type: ignore
    min_height: int = settings.get_setting('min_height') or 0 # type: ignore
    max_width: int = settings.get_setting('max_width') or 0 # type: ignore
    max_height: int = settings.get_setting('max_height') or 0 # type: ignore

    if 0 < width < min_width:
        return False
    if 0 < height < min_height:
        return False
    if width > max_width > 0:
        return False
    if height > max_height > 0:
        return False

    return True


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

    file_path = data.get('path')

    try:
        resolution = ffmpeg.probe(file_path, select_streams='v:0', show_entries='stream=width,height')

        width: int = resolution['streams'][0]['width']
        height: int = resolution['streams'][0]['height']
    except (ffmpeg.Error, AttributeError, IndexError):
        # Not a video file
        return

    if not resolution_is_within_limits(width, height):
        data['add_file_to_pending_tasks'] = False
        data['issues'].append(
            {
                'id': 'Limit library search by video resolution',
                'message': f'Video resolution of file "{file_path}" is outside the limit of "{width}x{height}".',
            }
        )

    return
