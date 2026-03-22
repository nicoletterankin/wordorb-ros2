"""
word_orb.launch.py — Launch the Word Orb ROS2 node with parameters.

Usage:
  ros2 launch wordorb_ros2 word_orb.launch.py
  ros2 launch wordorb_ros2 word_orb.launch.py api_key:=wo_your_key_here
  ros2 launch wordorb_ros2 word_orb.launch.py default_language:=es publish_interval:=3600.0
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('wordorb_ros2')
    default_params = os.path.join(pkg_share, 'config', 'word_orb_params.yaml')

    return LaunchDescription([
        # Launch arguments (override params from CLI)
        DeclareLaunchArgument(
            'api_key',
            default_value='',
            description='Word Orb API key (empty for free tier, 500 calls/day)',
        ),
        DeclareLaunchArgument(
            'default_language',
            default_value='en',
            description='Default language code for lookups',
        ),
        DeclareLaunchArgument(
            'publish_interval',
            default_value='86400.0',
            description='Seconds between daily content publishes',
        ),
        DeclareLaunchArgument(
            'daily_word',
            default_value='courage',
            description='Word to publish on /word_orb/word_of_the_day',
        ),

        # The node
        Node(
            package='wordorb_ros2',
            executable='word_orb_node',
            name='word_orb_node',
            output='screen',
            parameters=[
                default_params,
                {
                    'api_key': LaunchConfiguration('api_key'),
                    'default_language': LaunchConfiguration('default_language'),
                    'publish_interval': LaunchConfiguration('publish_interval'),
                    'daily_word': LaunchConfiguration('daily_word'),
                },
            ],
        ),
    ])
