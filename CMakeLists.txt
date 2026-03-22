cmake_minimum_required(VERSION 3.8)
project(wordorb_ros2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

# Generate interfaces (messages and services)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/WordData.msg"
  "msg/LessonData.msg"
  "srv/WordEnrich.srv"
  "srv/WordEthics.srv"
  "srv/LessonGet.srv"
  DEPENDENCIES std_msgs
)

# Install Python package
ament_python_install_package(${PROJECT_NAME})

# Install Python nodes
install(PROGRAMS
  wordorb_ros2/word_orb_node.py
  wordorb_ros2/word_orb_client.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install config files
install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}/
)

# Install resource index marker
install(FILES
  resource/${PROJECT_NAME}
  DESTINATION share/ament_index/resource_index/packages
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_word_orb_client test/test_word_orb_client.py)
endif()

ament_package()
