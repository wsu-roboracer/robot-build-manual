.. _doc_setup_nav2:

SETUP - Nav2
==================================

Install Nav2 (Navigation Stack)
---------------------------------

1️⃣ **Install the Nav2 packages**

.. code-block:: console

   sudo apt update
   sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup

``ros-humble-navigation2`` provides the core Nav2 nodes (planner, controller, bt_navigator) and ``ros-humble-nav2-bringup`` provides the launch files.


Create the Parameters File
---------------------------

Nav2 requires a parameters file that configures the planner, controller, and costmaps for the F1TENTH Ackermann platform.

2️⃣ **Create the file on the robot**

Open the file in VS Code:

.. code-block:: bash

   code ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/config/nav2_params.yaml

Paste the following contents and save (``Ctrl+S``):

.. code-block:: yaml

   # =============================================================================
   # Nav2 Parameters — F1TENTH RoboRacer
   # =============================================================================
   # Minimal configuration tuned for the F1TENTH Ackermann platform.
   # Place this file at:
   #   ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/config/nav2_params.yaml
   # =============================================================================

   map_server:
     ros__parameters:
       use_sim_time: False
       yaml_filename: ""

   amcl:
     ros__parameters:
       use_sim_time: False
       alpha1: 0.2
       alpha2: 0.2
       alpha3: 0.2
       alpha4: 0.2
       alpha5: 0.2
       base_frame_id: "base_link"
       global_frame_id: "map"
       odom_frame_id: "odom"
       robot_model_type: "nav2_amcl::DifferentialMotionModel"
       scan_topic: /scan
       max_particles: 2000
       min_particles: 500
       laser_model_type: "likelihood_field"
       laser_max_range: 10.0
       laser_min_range: -1.0
       max_beams: 60
       z_hit: 0.5
       z_rand: 0.5
       z_short: 0.05
       z_max: 0.05
       sigma_hit: 0.2
       lambda_short: 0.1
       laser_likelihood_max_dist: 2.0
       update_min_d: 0.25
       update_min_a: 0.2
       resample_interval: 1
       transform_tolerance: 1.0
       recovery_alpha_fast: 0.0
       recovery_alpha_slow: 0.0
       tf_broadcast: true
       set_initial_pose: false

   bt_navigator:
     ros__parameters:
       use_sim_time: False
       global_frame: map
       robot_base_frame: base_link
       odom_topic: /odom
       bt_loop_duration: 10
       default_server_timeout: 20
       navigators: ["navigate_to_pose", "navigate_through_poses"]
       navigate_to_pose:
         plugin: "nav2_bt_navigator/NavigateToPoseNavigator"
       navigate_through_poses:
         plugin: "nav2_bt_navigator/NavigateThroughPosesNavigator"

   controller_server:
     ros__parameters:
       use_sim_time: False
       controller_frequency: 20.0
       min_x_velocity_threshold: 0.001
       min_y_velocity_threshold: 0.5
       min_theta_velocity_threshold: 0.001
       progress_checker_plugins: ["progress_checker"]
       goal_checker_plugins: ["general_goal_checker"]
       controller_plugins: ["FollowPath"]

       progress_checker:
         plugin: "nav2_controller::SimpleProgressChecker"
         required_movement_radius: 0.5
         movement_time_allowance: 10.0

       general_goal_checker:
         stateful: True
         plugin: "nav2_controller::SimpleGoalChecker"
         xy_goal_tolerance: 0.25
         yaw_goal_tolerance: 0.25

       FollowPath:
         plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
         desired_linear_vel: 1.0
         lookahead_dist: 1.0
         min_lookahead_dist: 0.5
         max_lookahead_dist: 2.0
         lookahead_time: 1.5
         rotate_to_heading_angular_vel: 1.0
         transform_tolerance: 0.1
         use_velocity_scaled_lookahead_dist: True
         min_approach_linear_velocity: 0.3
         approach_velocity_scaling_dist: 1.0
         use_collision_detection: True
         max_allowed_time_to_collision_up_to_carrot: 1.0
         use_regulated_linear_velocity_scaling: True
         use_cost_regulated_linear_velocity_scaling: False
         regulated_linear_scaling_min_radius: 0.9
         regulated_linear_scaling_min_speed: 0.3
         max_angular_accel: 3.2
         allow_reversing: False

   planner_server:
     ros__parameters:
       use_sim_time: False
       expected_planner_frequency: 20.0
       planner_plugins: ["GridBased"]
       GridBased:
         plugin: "nav2_navfn_planner/NavfnPlanner"
         tolerance: 0.5
         use_astar: True
         allow_unknown: True

   local_costmap:
     local_costmap:
       ros__parameters:
         use_sim_time: False
         update_frequency: 5.0
         publish_frequency: 2.0
         global_frame: odom
         robot_base_frame: base_link
         rolling_window: True
         width: 3
         height: 3
         resolution: 0.05
         robot_radius: 0.18
         plugins: ["obstacle_layer", "inflation_layer"]
         obstacle_layer:
           plugin: "nav2_costmap_2d::ObstacleLayer"
           enabled: True
           observation_sources: scan
           scan:
             topic: /scan
             max_obstacle_height: 2.0
             clearing: True
             marking: True
             data_type: "LaserScan"
             raytrace_max_range: 10.0
             raytrace_min_range: 0.0
             obstacle_max_range: 8.0
             obstacle_min_range: 0.0
         inflation_layer:
           plugin: "nav2_costmap_2d::InflationLayer"
           cost_scaling_factor: 3.0
           inflation_radius: 0.30

   global_costmap:
     global_costmap:
       ros__parameters:
         use_sim_time: False
         update_frequency: 1.0
         publish_frequency: 1.0
         global_frame: map
         robot_base_frame: base_link
         robot_radius: 0.18
         resolution: 0.05
         track_unknown_space: True
         plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
         static_layer:
           plugin: "nav2_costmap_2d::StaticLayer"
           map_subscribe_transient_local: True
         obstacle_layer:
           plugin: "nav2_costmap_2d::ObstacleLayer"
           enabled: True
           observation_sources: scan
           scan:
             topic: /scan
             max_obstacle_height: 2.0
             clearing: True
             marking: True
             data_type: "LaserScan"
             raytrace_max_range: 10.0
             raytrace_min_range: 0.0
             obstacle_max_range: 8.0
             obstacle_min_range: 0.0
         inflation_layer:
           plugin: "nav2_costmap_2d::InflationLayer"
           cost_scaling_factor: 3.0
           inflation_radius: 0.30

   behavior_server:
     ros__parameters:
       use_sim_time: False
       costmap_topic: local_costmap/costmap_raw
       footprint_topic: local_costmap/published_footprint
       cycle_frequency: 10.0
       behavior_plugins: ["spin", "backup", "wait"]
       spin:
         plugin: "nav2_behaviors/Spin"
       backup:
         plugin: "nav2_behaviors/BackUp"
       wait:
         plugin: "nav2_behaviors/Wait"

   lifecycle_manager:
     ros__parameters:
       use_sim_time: False
       autostart: True
       node_names:
         - map_server
         - amcl
         - controller_server
         - planner_server
         - behavior_server
         - bt_navigator

Create the Velocity Converter
------------------------------

Nav2's controller publishes ``geometry_msgs/Twist`` on ``/cmd_vel``, but the F1TENTH's ackermann mux expects ``AckermannDriveStamped`` on the ``/drive`` topic. A converter node bridges this gap.

3️⃣ **Create the converter node**

Open the file in VS Code:

.. code-block:: bash

   code ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/f1tenth_stack/cmd_vel_to_ackermann.py

Paste the following contents and save (``Ctrl+S``):

.. code-block:: python

   import rclpy
   from rclpy.node import Node
   from geometry_msgs.msg import Twist
   from ackermann_msgs.msg import AckermannDriveStamped
   import math

   class CmdVelToAckermann(Node):
       def __init__(self):
           super().__init__('cmd_vel_to_ackermann')
           self.declare_parameter('wheelbase', 0.25)
           self.wheelbase = self.get_parameter('wheelbase').value

           self.sub = self.create_subscription(Twist, '/cmd_vel', self.callback, 10)
           self.pub = self.create_publisher(AckermannDriveStamped, '/drive', 10)

       def callback(self, msg):
           ack = AckermannDriveStamped()
           ack.header.stamp = self.get_clock().now().to_msg()
           ack.drive.speed = msg.linear.x

           if abs(msg.linear.x) > 0.01:
               ack.drive.steering_angle = math.atan(
                   self.wheelbase * msg.angular.z / msg.linear.x
               )
           else:
               ack.drive.steering_angle = 0.0

           self.pub.publish(ack)

   def main():
       rclpy.init()
       node = CmdVelToAckermann()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()

   if __name__ == '__main__':
       main()

4️⃣ **Replace setup.py**

Replace the contents of ``setup.py`` with the following (adds the maps data file and converter entry point).

Open the file in VS Code:

.. code-block:: bash

   code ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/setup.py

Replace all contents with the following and save (``Ctrl+S``):

.. code-block:: python

   from setuptools import setup
   import os
   from glob import glob

   package_name = 'f1tenth_stack'

   setup(
       name=package_name,
       version='0.0.1',
       packages=[package_name],
       data_files=[
           ('share/ament_index/resource_index/packages',
               ['resource/' + package_name]),
           ('share/' + package_name, ['package.xml']),
           (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
           (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
           (os.path.join('share', package_name, 'maps'), glob('maps/*')),
       ],
       install_requires=['setuptools'],
       zip_safe=True,
       maintainer='Hongrui Zheng',
       maintainer_email='billyzheng.bz@gmail.com',
       description='Onboard drivers for vesc and sensors for F1TENTH vehicles.',
       license='MIT',
       tests_require=['pytest'],
       entry_points={
           'console_scripts': [
               'throttle_interpolator = f1tenth_stack.throttle_interpolator:main',
               'tf_publisher = f1tenth_stack.tf_publisher:main',
               'cmd_vel_to_ackermann = f1tenth_stack.cmd_vel_to_ackermann:main',
           ],
       },
   )

5️⃣ **Add the Nav2 dependency to package.xml**

.. code-block:: bash

   cd ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack
   sed -i '/<depend>std_msgs<\/depend>/a\  <depend>nav2_bringup<\/depend>' package.xml

Create the Launch File
-----------------------

The Nav2 launch file wraps ``nav2_bringup`` with the correct map, parameters, and the velocity converter for the F1TENTH.

6️⃣ **Create the launch file**

Open the file in VS Code:

.. code-block:: bash

   code ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/launch/nav2_launch.py

Paste the following contents and save (``Ctrl+S``):

.. code-block:: python

   # MIT License

   # Copyright (c) 2025 WSU F1TENTH

   # Permission is hereby granted, free of charge, to any person obtaining a copy
   # of this software and associated documentation files (the "Software"), to deal
   # in the Software without restriction, including without limitation the rights
   # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   # copies of the Software, and to permit persons to whom the Software is
   # furnished to do so, subject to the following conditions:

   # The above copyright notice and this permission notice shall be included in all
   # copies or substantial portions of the Software.

   # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   # SOFTWARE.

   from launch import LaunchDescription
   from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
   from launch.launch_description_sources import PythonLaunchDescriptionSource
   from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
   from launch_ros.actions import Node
   from launch_ros.substitutions import FindPackageShare
   from ament_index_python.packages import get_package_share_directory
   import os


   def generate_launch_description():
       f1tenth_stack_dir = get_package_share_directory('f1tenth_stack')
       nav2_bringup_dir = get_package_share_directory('nav2_bringup')

       map_name_arg = DeclareLaunchArgument(
           'map_name',
           default_value='lab_map',
           description='Map name (without extension) in f1tenth_stack/maps/'
       )

       nav2_params = os.path.join(f1tenth_stack_dir, 'config', 'nav2_params.yaml')
       map_file = PathJoinSubstitution(
           [FindPackageShare('f1tenth_stack'), 'maps', [LaunchConfiguration('map_name'), '.yaml']]
       )

       nav2_bringup = IncludeLaunchDescription(
           PythonLaunchDescriptionSource(
               os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
           ),
           launch_arguments={
               'map': map_file,
               'params_file': nav2_params,
               'use_sim_time': 'False',
               'slam': 'False',     # use AMCL for localization, not slam_toolbox
               'autostart': 'True',
           }.items()
       )

       # Converts nav2 cmd_vel (Twist) → drive (AckermannDriveStamped) for the mux
       cmd_vel_to_ackermann_node = Node(
           package='f1tenth_stack',
           executable='cmd_vel_to_ackermann',
           name='cmd_vel_to_ackermann',
           parameters=[{'wheelbase': 0.25}]
       )

       return LaunchDescription([map_name_arg, nav2_bringup, cmd_vel_to_ackermann_node])

7️⃣ **Rebuild the workspace**

.. code-block:: bash

   cd ~/f1tenth_ws
   colcon build --packages-select f1tenth_stack
   source install/setup.bash

8️⃣ **Verify the files exist**

.. code-block:: bash

   ls ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/config/nav2_params.yaml
   ls ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/f1tenth_stack/cmd_vel_to_ackermann.py
   ls ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/launch/nav2_launch.py

Applying These Changes to Other Robots
---------------------------------------

The Nav2 setup lives in two files within the git-tracked workspace. The fastest way to set up additional robots is to copy and paste the file contents directly.

**nav2_launch.py**

On the other robot, open the launch file and paste the code from Step 6️⃣ above:

.. code-block:: bash

   code ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/launch/nav2_launch.py

**localize_launch.py** (particle filter fix)

On the other robot, open the particle filter launch file:

.. code-block:: bash

   code ~/f1tenth_ws/src/particle_filter/launch/localize_launch.py

Replace the entire contents with:

.. code-block:: python

   # MIT License

   # Copyright (c) 2020 Hongrui Zheng

   # Permission is hereby granted, free of charge, to any person obtaining a copy
   # of this software and associated documentation files (the "Software"), to deal
   # in the Software without restriction, including without limitation the rights
   # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   # copies of the Software, and to permit persons to whom the Software is
   # furnished to do so, subject to the following conditions:

   # The above copyright notice and this permission notice shall be included in all
   # copies or substantial portions of the Software.

   # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   # SOFTWARE.

   from launch import LaunchDescription
   from launch_ros.actions import Node
   from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
   from launch.actions import DeclareLaunchArgument
   from launch_ros.substitutions import FindPackageShare
   from ament_index_python.packages import get_package_share_directory
   import os
   import yaml

   def generate_launch_description():
       # config and args
       localize_config = os.path.join(
           get_package_share_directory('particle_filter'),
           'config',
           'localize.yaml'
       )
       localize_config_dict = yaml.safe_load(open(localize_config, 'r'))
       map_name = localize_config_dict['map_server']['ros__parameters']['map']
       localize_la = DeclareLaunchArgument(
           'localize_config',
           default_value=localize_config,
           description='Localization configs')
       map_name_la = DeclareLaunchArgument(
           'map_name',
           default_value=map_name,
           description='Map name (without extension) in particle_filter/maps/')
       ld = LaunchDescription([localize_la, map_name_la])

       # nodes
       pf_node = Node(
           package='particle_filter',
           executable='particle_filter',
           name='particle_filter',
           parameters=[LaunchConfiguration('localize_config')]
       )
       map_server_node = Node(
           package='nav2_map_server',
           executable='map_server',
           name='map_server',
           parameters=[{'yaml_filename': PathJoinSubstitution(
                            [FindPackageShare('particle_filter'), 'maps',
                             [LaunchConfiguration('map_name'), '.yaml']])},
                       {'topic': 'map'},
                       {'frame_id': 'map'},
                       {'output': 'screen'},
                       {'use_sim_time': True}]
       )
       nav_lifecycle_node = Node(
           package='nav2_lifecycle_manager',
           executable='lifecycle_manager',
           name='lifecycle_manager_localization',
           output='screen',
           parameters=[{'use_sim_time': True},
                       {'autostart': True},
                       {'node_names': ['map_server']}]
       )

       # finalize
       ld.add_action(nav_lifecycle_node)
       ld.add_action(map_server_node)
       ld.add_action(pf_node)

       return ld

**Rebuild and source**

After pasting both files, rebuild and source the workspace:

.. code-block:: bash

   cd ~/f1tenth_ws
   colcon build --packages-select f1tenth_stack particle_filter
   source install/setup.bash
