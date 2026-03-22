from setuptools import setup, find_packages

package_name = 'wordorb_ros2'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/word_orb.launch.py']),
        ('share/' + package_name + '/config', ['config/word_orb_params.yaml']),
    ],
    install_requires=['setuptools', 'requests'],
    zip_safe=True,
    maintainer='Nicolette Rankin',
    maintainer_email='nicolette@lotdpbc.com',
    description='ROS2 interface to the Word Orb vocabulary and lesson API',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'word_orb_node = wordorb_ros2.word_orb_node:main',
        ],
    },
)
