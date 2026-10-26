Diagnostics Documentation
=========================

.. _diag-top:

System overview: the robot diagnostics dashboard
------------------------------------------------

The robot diagnostics dashboard is a web page hosted on the robot that relays the
robot's system information to anyone on the same Wi-Fi. It collects what the car's
ROS nodes already report (battery, lidar, odometry, the controller) and what ROS
does not know about (temperatures, CPU, memory, Wi-Fi, the camera's USB link),
grades each one green, yellow or red, and shows it in a browser on your own laptop
or phone. It also streams the camera, draws the lidar, and can drive the car.

Once it is running, open ``http://<robot ip>:8000/dashboard.html`` from any device
on the robot's Wi-Fi, for example ``http://192.168.1.202:8000/dashboard.html`` for
robot #2 (see :ref:`Opening the dashboard <diag-opening>`).

This document is for whoever works on the dashboard next: how it works, why it is
built the way it is, how to run it, and which file to edit to change any part of
it.

- :ref:`How it works <diag-how-it-works>`
- :ref:`Why it is built this way <diag-why>`
- :ref:`Running it <diag-running>`
- :ref:`How each check works, and how to change it <diag-checks>`
  (starts with :ref:`Ranges at a glance <diag-ranges>`)
- :ref:`What was already on the robot, and what this project added <diag-added>`
- :ref:`Reference: the files <diag-files>`

Every green / yellow / red range, and why it was chosen, is in this document: all
of them in :ref:`Ranges at a glance <diag-ranges>`, and each one again under its
check. For history only: ``instructor-interview.md`` is the
record of the interview where the professor signed off on the ranges, and
``ros-status-spike-notes.md`` and
``ros-status-spike-summary.md`` hold the raw
measurements. This document does not need them to be read.

.. _diag-how-it-works:

How it works
~~~~~~~~~~~~

In short: ROS nodes on the robot publish the car's data and health. rosbridge
relays that data to the browser over a websocket. A small web server on the robot
hands the browser the page itself. The camera is streamed separately, outside
ROS. The page grades everything and shows it.

.. code-block:: text

   ROBOT (Jetson)                                              YOUR LAPTOP / PHONE

    drive nodes -------------> /scan, /sensors/core, /odom, /joy ...
    urg_node, ackermann_mux --> /diagnostics  (their own health)
    system_diagnostics -------> /diagnostics  (system: CPU, Thermal, Network ...)
                                      |
                                      v
    rosbridge + rosapi        ws://<robot>:9090  <--- websocket ---  the page: data in,
                                                                     drive commands and
                                                                     button presses out
    web server                http://<robot>:8000 <-- loads the page once
    camera (/dev/video4)
      -> GStreamer -> TCP :8081
      -> camera_http.py       http://<robot>:8082 <-- camera picture and frame rate

What runs on the robot
^^^^^^^^^^^^^^^^^^^^^^

**The drive stack's ROS nodes.** These are the car's own nodes, started by
``bringup``, and they were there before this project. The dashboard only reads what
they already publish:

.. list-table::
   :header-rows: 1
   :widths: 20 35 45

   * - Node
     - Publishes
     - Used by the dashboard for
   * - ``vesc_driver_node``
     - ``/sensors/core`` (about 50 Hz)
     - battery voltage, motor controller (VESC) temperature, fault codes
   * - ``vesc_to_odom_node``
     - ``/odom``, ``/tf``
     - speed
   * - ``urg_node``
     - ``/scan`` (40 Hz), and its own health on ``/diagnostics``
     - the lidar picture, the lidar's scan rate and hardware status
   * - ``joy``
     - ``/joy``
     - whether the controller is sending, and which buttons are held
   * - ``ackermann_mux``
     - ``/ackermann_cmd``, and its own status on ``/diagnostics``
     - who is in control (nobody, the controller, or ``/drive``)
   * - ``joy_teleop``, ``ackermann_to_vesc_node``
     - ``/teleop``, ``/commands/motor/speed``, ``/commands/servo/position``
     - whether they are running; their topics are listed on the Advanced tab
   * - ``static_baselink_to_laser``
     - ``/tf_static``
     - whether it is running

**system_diagnostics, the one ROS node this project added.** Much of what makes
a car unhealthy is not in ROS at all: the board's temperature, CPU load, memory,
disk space, Wi-Fi signal, whether the lidar answers on its network cable, whether
the camera is on a fast USB port, whether the controller is paired over
Bluetooth. This node reads all of that from Linux (``/proc``, ``/sys``, ``ping``, ``iw``,
``bluetoothctl``, ``tegrastats``) and publishes it once a second on ``/diagnostics``,
as statuses named ``system: Thermal``, ``system: CPU``, ``system: Network``, and so on.
The node also provides the services behind the page's buttons (emergency stop,
release, joystick check, disconnect controller) and runs the drive watchdog.

**rosbridge and rosapi.** rosbridge (port 9090) is a standard ROS package that
relays topics and services to and from a websocket as JSON. It is what lets a web
page talk to ROS. rosapi comes with it and answers questions about the ROS graph,
such as which nodes are running.

**A web server.** Python's built-in ``http.server`` on port 8000. It only hands the
browser the page's files (``dashboard.html``, ``css/``, ``js/``); after that, all live
data goes over the websocket.

**The camera stream.** GStreamer reads the RealSense's colour camera at
``/dev/video4`` (640x480, 30 fps), compresses each frame to JPEG and sends the
frames on TCP port 8081. ``camera_http.py`` relays that as a normal web stream at
``http://<robot>:8082/camera.mjpg``, which the page shows in an ordinary ``<img>``,
and reports the frame rate at ``http://<robot>:8082/stats``. It sends each viewer
the newest frame rather than every frame in order, so a slow Wi-Fi link lowers the
frame rate instead of making the picture fall seconds behind. The picture never
goes through ROS.

The /diagnostics topic
^^^^^^^^^^^^^^^^^^^^^^

``/diagnostics`` is ROS's standard topic for health reports
(``diagnostic_msgs/DiagnosticArray``). Each report has a name, a level (OK, warning,
error, or stale meaning not measured yet), a message, and a list of key / value
readings. Three nodes publish to it: ``urg_node`` and ``ackermann_mux`` (their own
reports, already there) and ``system_diagnostics`` (the ``system: ...`` reports).

Each message carries one publisher's reports only, so the page subscribes to every
message, with no throttling, and keeps the latest report for each name. Because it
is the standard topic, ROS's own tools (``rqt_robot_monitor``, ``ros2 topic echo
/diagnostics``) show the same reports the page does.

What the page does
^^^^^^^^^^^^^^^^^^

1. The browser loads the page from port 8000.
2. The page opens a websocket to rosbridge on port 9090, on the same machine it was
   loaded from.
3. It subscribes through rosbridge to the topics it watches (the list is ``TOPICS``
   in ``js/config.js``), each at most 5 times a second, plus ``/diagnostics`` on every
   message. Every 5 seconds it asks rosapi which nodes and topics exist.
4. Twice a second it grades everything and redraws: the headline, the tiles, the
   subsystems, the lidar plot.
5. It shows the camera from port 8082, and reads the frame rate from ``/stats``
   every 2 seconds.
6. In the other direction, it publishes drive commands on ``/drive`` and calls
   ``system_diagnostics``' services when you press Emergency stop, Release, Run
   joystick check or Disconnect controller.

Where each thing on the page comes from
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - On the page
     - Comes from
     - Through
   * - Battery, VESC temperature, fault codes
     - ``/sensors/core``, from ``vesc_driver_node``
     - rosbridge
   * - Speed
     - ``/odom``, from ``vesc_to_odom_node``
     - rosbridge
   * - LiDAR plot and distances
     - ``/scan``, from ``urg_node``
     - rosbridge
   * - LiDAR scan rate and status
     - ``urg_node``'s reports on ``/diagnostics``
     - rosbridge
   * - Lidar cable and ping
     - ``system: Network``, from ``system_diagnostics``
     - rosbridge
   * - Temperatures, CPU, RAM, GPU, disk
     - ``system: Thermal``, ``CPU``, ``Memory``, ``GPU``, ``Storage``
     - rosbridge
   * - Wi-Fi signal, loss, round trip
     - ``system: Network``
     - rosbridge
   * - Controller
     - ``/joy`` from ``joy``, and ``system: Gamepad``
     - rosbridge
   * - Who is in control
     - ``ackermann_mux``'s report on ``/diagnostics``
     - rosbridge
   * - Nodes running, topics present
     - rosapi
     - rosbridge
   * - Camera picture and frame rate
     - GStreamer and ``camera_http.py``
     - port 8082, not ROS

Each check is explained in full, from where its value comes from to the setting
that changes it, under
:ref:`How each check works <diag-checks>`.

The page works out the robot's address from where it was loaded: opened from
``http://192.168.1.206:8000``, it connects to ``ws://192.168.1.206:9090`` and loads the
camera from ``192.168.1.206:8082``. Nothing is hard-coded.

.. _diag-why:

Why it is built this way
~~~~~~~~~~~~~~~~~~~~~~~~

Each choice below says what was picked, what it was picked over, and why. Most of
the reasons were measured on robots #2 and #6; the details are in the spike notes.
If you change one of these, the reason is what you are giving up.

A web page served by the robot, viewed on your own device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: a desktop tool such as ``rqt_robot_monitor``, or a browser on the
robot over NoMachine.

``rqt`` needs a full ROS install on the viewing machine, which is the barrier the
project exists to remove. The Jetson's own browser does not run: every snap app
fails to start on it, and Chromium is a snap. A page served by the robot works on
any laptop or phone on the Wi-Fi with nothing installed.

rosbridge, instead of ROS on the laptop or our own server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: running ROS on each laptop, or writing a custom web backend that
reads ROS and serves JSON.

ROS on a laptop needs the same ROS version, the same ``ROS_DOMAIN_ID`` (202), and the
car's custom message packages; without ``vesc_msgs``, ``/sensors/core``, which carries
the battery voltage, cannot be decoded at all. rosbridge runs on the robot, where
every message package already exists, so the browser gets plain JSON. It is a
maintained package, so there is no backend of ours to keep alive, and one
connection carries data in both directions.

What it costs: rosbridge has no login, so anyone who can reach port 9090 can
publish to the robot, including drive commands. It also serves at most 10 clients
at once; an 11th connects and receives nothing, which looks like a dead robot.
The page shows ``clients N / 10`` and an orange banner when it is starved. Putting
rosbridge behind a proxy with a login is a possible later change.

OS health as a ROS node, on the standard /diagnostics topic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: a separate web endpoint for CPU, temperatures and the rest.

ROS already has a standard health message (``diagnostic_msgs/DiagnosticArray`` on
``/diagnostics``), and ``urg_node`` and ``ackermann_mux`` already use it. Publishing
the OS checks the same way meant no second connection, no second port, and that
the standard ROS tools (``rqt_robot_monitor``, ``diagnostic_aggregator``) see the same
data as the page.

Inside the node, cheap file reads run every second, and anything that starts
another program (``ping``, ``iw``, ``bluetoothctl``, ``tegrastats``,
``joy_enumerate_devices``) runs every 10 seconds on its own thread with a timeout,
so one hung command cannot freeze the node. Until a check has run, it reports
unknown, never a made-up OK.

The robot grades some values, the page grades others
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The node grades what only the robot can measure (temperatures, CPU, memory, disk,
GPU, camera link, controller), so ``rqt`` and the page agree on the colour. The page
grades values that come from ROS topics (battery, VESC temperature, lidar rate,
nodes, topics) and Wi-Fi, because it has the raw numbers and can smooth them. The
entries under :ref:`How each check works <diag-checks>`
say which side grades each one.

Every topic has a class that says when silence is a fault
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: one rule for all topics ("no message for 2 seconds means broken").

Applied to every topic on a healthy car, that rule flagged 16 of 23 topics as
broken. ``/joy`` is silent when nobody touches the controller, ``/drive`` has no
publisher unless something is driving, and ``/tf_static`` publishes once. Each topic
in ``TOPICS`` (``js/config.js``) has a class (``continuous``, ``event``, ``latched`` or
``input``), and with those classes the same healthy car showed 0 problems. A page
that shows red on a healthy car teaches people to ignore it.

The lidar is graded by its own driver's rate report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: measuring the ``/scan`` rate in the page.

Rates measured over Wi-Fi read low (about 30 Hz for a 40 Hz topic), because the
page receives throttled copies. ``urg_node`` measures its own rate on the robot and
reports it with its acceptable range (38 to 42 Hz), so the page uses that.

The node list comes from rosapi
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: ``ros2 node list``.

``ros2 node list`` was wrong in both directions during testing: its background
daemon once listed a single node while the others were clearly running, and
``--no-daemon`` missed slow nodes.
rosbridge's ``rosapi/nodes`` was correct every time.

The camera does not go through ROS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: the ``realsense2_camera`` ROS node and a compressed image topic.

At the camera's default resolution (1280x720) one raw colour frame is about
2.7 MB, so 30 frames a second is far more than Wi-Fi and rosbridge can carry.
Compressed to JPEG at 640x480 it is about 50 KB a frame. GStreamer compresses
on the robot, and ``camera_http.py`` exists because GStreamer's TCP output is not a
web stream a browser can show. The professor asked for the camera to stream on
every bringup, so it starts with everything else.

The battery is judged on a 5 second median, with lines from a run-down test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Under throttle the voltage swings about 0.2 V within a second. Judged reading by
reading, a pack near a line would flicker between colours. The lines (yellow below
11.6 V, red below 11.1 V) were set after a run-down test: from 10.4 V the robot
lost power about five minutes later at 8.8 V or below, so the earlier red line of
10.5 V was too late.

The drive watchdog lives on the robot
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the page loses Wi-Fi while driving, it cannot send a stop, and the mux sends no
stop of its own when an input goes quiet, so the motor would keep its last
command. Only something on the robot can notice the silence, so
``system_diagnostics`` watches ``/drive`` and sends zero speed when it goes quiet
mid-drive. It waits 0.3 s, longer than the mux's own 0.2 s cut-off for a quiet
input (``mux.yaml``), so it can never interrupt a publisher that is still working.

The emergency stop freezes one node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: publishing stop commands.

The physical controller has the highest priority in the mux, so a stop sent from
the page would lose to someone holding the controller. Every input reaches the
motor through ``ackermann_to_vesc_node``, so freezing that one process stops all of
them, and the node then holds the motor at speed 0 itself.

It starts with bringup, inside f1tenth_system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Picked over: a separate repo or package that each car installs by hand.

Every car already pulls ``f1tenth_system``. With the dashboard inside it, updating a
car is ``git pull`` and a rebuild, with nothing copied by hand. The camera
pipeline and the web server are not ROS nodes, so the launch file starts them as
plain commands (``ExecuteProcess``).

Plain HTML, CSS and JavaScript, no build step
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Anyone on the team can edit a file and reload. The robot serves the folder as it
is, with Python's built-in web server.

.. _diag-running:

Running it
~~~~~~~~~~

.. _diag-opening:

Opening the dashboard
^^^^^^^^^^^^^^^^^^^^^

Once the dashboard is running (either way below), open this from a laptop or
phone on the same Wi-Fi as the robot:

.. code-block:: text

   http://<robot ip>:8000/dashboard.html

The address is different for each robot:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Robot
     - Address
   * - #2
     - ``http://192.168.1.202:8000/dashboard.html``
   * - #6
     - ``http://192.168.1.206:8000/dashboard.html``

So far each robot's address has been 192.168.1.20 followed by its number. To be
sure for another car, run ``hostname -I`` on the robot; the address that starts
with ``192.168.1.`` is the one to use (the ``192.168.0.`` one is the robot's own cable
to the lidar).

You do not need to type the robot's address anywhere else: the page connects to
rosbridge and the camera on the same machine it was loaded from. If the page looks
out of date after an update, hard-refresh with Ctrl+Shift+R.

Two ways to start it
^^^^^^^^^^^^^^^^^^^^

There are two ways to start the same code. The dashboard looks and behaves the
same either way; only the setup is different. Use the first on the cars; use the
second while developing.

.. list-table::
   :header-rows: 1
   :widths: 18 41 41

   * -
     - On a robot (normal use)
     - For development and testing
   * - Code lives in
     - ``f1tenth_system``, package ``f1tenth_stack``
     - this repo, ``prototype/``
   * - Start
     - ``ros2 launch f1tenth_stack bringup_launch.py`` (the ``bringup`` alias)
     - ``./start_diagnostics.sh``
   * - Stop
     - Ctrl+C
     - Ctrl+C, or ``./start_diagnostics.sh --stop``
   * - Leave a part out
     - ``use_camera:=false``, ``use_diagnostics:=false``, ``use_lidar:=false``
     - ``--no-camera``, ``--no-sysdiag``, ``--no-bridge``, ``--no-server``, ``--no-bringup``
   * - Other options
     - ``dashboard_port:=8000``, ``camera_device:=/dev/video4``
     - ``--port 8000``, ``--camera-device /dev/video4``
   * - See what is running
     - ``ros2 node list``
     - ``./start_diagnostics.sh --status``
   * - Update a car
     - ``git pull``, ``colcon build``, restart bringup
     - copy the files over again

On a robot
^^^^^^^^^^

``bringup`` starts the eight drive nodes plus ``system_diagnostics``, rosbridge, the
web server, the camera pipeline and ``camera_http``.

This version exists on robot #6 only for now; it has not been merged into
``Weber-AGV/f1tenth_system``, so other cars still use the development way.

The robot runs the built copy in ``~/f1tenth_ws/install/``, not the files in
``~/f1tenth_ws/src/``. A change in ``src/`` does nothing until you rebuild:

.. code-block:: bash

   cd ~/f1tenth_ws
   colcon build --packages-select f1tenth_stack
   # then stop bringup (Ctrl+C) and start it again

To update a car to the latest version:

.. code-block:: bash

   cd ~/f1tenth_ws/src/f1tenth_system
   git pull
   git submodule update --init --recursive
   cd ~/f1tenth_ws
   colcon build --packages-select f1tenth_stack
   # restart bringup

For development and testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy ``prototype/`` onto the robot (robot #2 keeps it in ``~/diag/``) and run it there:

.. code-block:: bash

   cd ~/diag
   ./start_diagnostics.sh            # bringup, system_diagnostics, rosbridge, web server, camera
   ./start_diagnostics.sh --status   # what is up
   ./start_diagnostics.sh --stop     # stop a run started earlier, for example over SSH

Logs are in ``/tmp/f1tenth-diag/``. A second run refuses to start while one is
already running.

To work on the page without copying it to the robot each time, serve
``prototype/`` from your laptop and point it at a running robot:

.. code-block:: bash

   cd prototype
   python3 -m http.server 8000
   # open http://localhost:8000/dashboard.html?url=ws://192.168.1.206:9090

The ``ws://`` box and **Connect** button in the page's top bar do the same as
``?url=``. When the robot serves the page, the box fills itself in and you can
ignore it.

.. _diag-checks:

How each check works, and how to change it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every check below follows the same pattern: a short summary, then the detail in
the same order each time.

- **Where it comes from**: the file, command or ROS topic the value is read from.
- **How it is judged**: who decides the colour (the robot or the page) and the rule.
- **Why these lines**: where the green / yellow / red numbers came from.
- **What is sent**: what reaches the page, with the exact names.
- **On the page**: what you see, and where.
- **To change**: the file and setting to edit, with the current value.

The names under "What is sent" are the agreement between the robot side and the
page. If one side renames something, the other side does not fail with an error;
that value just goes blank or grey "unknown". Change both sides together.

.. _diag-ranges:

Ranges at a glance
^^^^^^^^^^^^^^^^^^

The professor signed off on these ranges. They are starting values, not final
ones: most come from hardware limits read off the robot or from common
conventions, not from a class using the cars. Expect them to change once the
professor runs the class and sees how they hold up against the tests students
actually run. When one changes, update the code (the check's "To change" table
says where) and this table together.

**Basis** says where each number comes from. Rows marked *convention* have no
measurement behind them, so they are the first to revisit.

.. list-table::
   :header-rows: 1
   :widths: 16 14 16 16 38

   * - Item
     - Green
     - Yellow
     - Red
     - Basis
   * - :ref:`Battery <diag-battery>` (5 second median)
     - 11.6 V or more
     - 11.1 to 11.6 V
     - below 11.1 V
     - A run-down test on robot #2: from 10.4 V the robot lost power about five minutes later at 8.8 V or below, falling faster below about 10 V. Red at 11.1 V (3.7 V per cell) leaves time to swap the pack. The 11.6 V yellow is a *convention*, a buffer to get a spare ready
   * - :ref:`VESC FET temperature <diag-vesc>`
     - below 65 C
     - 65 to 80 C
     - 80 C or more, or any VESC fault code
     - The VESC's own over-temperature fault trips near 85 C. Idle reads about 31 C. Never measured under a long drive, so treat as provisional
   * - :ref:`Board temperature <diag-board-temp>`
     - below 70 C
     - 70 to 85 C
     - 85 C or more
     - The Jetson's own trip points, read on robot #2: it slows down at 70 C and 99 C and shuts off at 104.5 C. Idle is about 50 C. Never measured under a long drive
   * - :ref:`CPU load <diag-cpu>` (1 minute average)
     - up to the core count (6)
     - above 6
     - above 12
     - More processes waiting than cores means work is queueing. The CPU is capped at 1.51 GHz in the 15 W power mode, so full load with a normal temperature is not a fault
   * - :ref:`RAM available <diag-ram>`
     - 20% or more
     - 10 to 20%
     - below 10%
     - Idle reads 63 to 80% available
   * - :ref:`GPU load <diag-gpu>`
     - below 95%
     - 95% or more for 5 seconds
     - none
     - *Convention.* A busy GPU means a heavy job is running, not a fault. Heat shows up in the board temperature
   * - :ref:`Wi-Fi signal <diag-wifi>`
     - -67 dBm or better
     - below -67 dBm
     - below -75 dBm, or no link
     - *Convention.* Measured -39 to -43 dBm in the lab
   * - :ref:`Wi-Fi packet loss <diag-wifi>` (to the router)
     - under 1%
     - 1% or more
     - 5% or more
     - *Convention.* Measured 0%; past bad sessions lost 90 to 100%
   * - :ref:`Wi-Fi round trip <diag-wifi>`
     - under 30 ms
     - 30 ms or more
     - 100 ms or more
     - *Convention.* Measured 1.4 to 3.2 ms
   * - :ref:`Lidar <diag-lidar>`
     - 38 to 42 Hz
     - scanning, outside that rate
     - no scans, or not running
     - ``urg_node``'s own accepted rate, 40 Hz within 5% (``sensors.yaml``)
   * - :ref:`Camera <diag-camera>`
     - on USB 3 (5000M), 15 fps or more
     - slower USB link, or under 15 fps
     - not found on USB, or no frame for 3 seconds
     - Half the camera's 30 fps. The RealSense is a USB 3 camera, so a slower link means it is in the wrong port or cable
   * - :ref:`Controller <diag-controller>`
     - connected and readable by ROS, or no controller
     - \-
     - connected but ROS cannot read it
     - No controller is normal when nobody is driving. A controller ROS cannot read looks connected but can neither drive nor stop the car
   * - :ref:`Nodes <diag-nodes>`
     - all expected nodes running
     - \-
     - any missing
     - A missing node is a failed bringup, so there is no in-between
   * - :ref:`Topics <diag-topics>`
     - publishing
     - slow
     - stopped or never sent
     - Each topic has a class that says when silence is a fault, so a healthy idle car does not show red

Not part of the sign-off: :ref:`disk <diag-disk>` (yellow above 85% used, red above 95%).

One place the code is gentler than the signed-off ranges: the topic table shows
``STALE`` and not-advertised topics in yellow, where the ranges call them red. The
LiDAR and Odometry rows do go red when their topic stops.

Before you edit
^^^^^^^^^^^^^^^

Every file is in ``prototype/`` when developing, and in ``f1tenth_system/f1tenth_stack/``
on the robots:

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - prototype/
     - f1tenth_stack/
   * - ``dashboard.html``, ``css/``, ``js/``
     - ``dashboard/dashboard.html``, ``dashboard/css/``, ``dashboard/js/``
   * - ``system_diagnostics.py``
     - ``f1tenth_stack/system_diagnostics.py``
   * - ``camera_http.py``
     - ``f1tenth_stack/camera_http.py``
   * - ``start_diagnostics.sh``
     - none; ``launch/bringup_launch.py`` does its job

Make and test changes in ``prototype/``, then copy them into ``f1tenth_stack`` so the
cars get them.

Copying the files to a robot
""""""""""""""""""""""""""""

``rsync`` copies files from your laptop to the robot over SSH, the same connection
``ssh`` uses, so it needs nothing extra on the robot. Unlike a plain copy (``scp``),
it compares each file with the robot's copy and only sends the ones that changed,
so running it again after a small edit is quick. The general form is:

.. code-block:: bash

   rsync -av <files or folders on your laptop> <user>@<robot address>:<folder on the robot>

- ``-a`` (archive) copies folders with everything in them and keeps each file's
  permissions and times. Keeping permissions matters for ``start_diagnostics.sh``,
  which has to stay executable.
- ``-v`` (verbose) lists each file as it is copied, so you can see what was sent.
- ``--delete`` also removes files on the robot that no longer exist on your laptop.
  Without it, a deleted or renamed file stays behind on the robot.
- A folder path on the robot (after the ``:``) without a leading ``/`` is inside the
  login's home folder, so ``diag/`` means ``/home/f1-wsu-2/diag/``.
- A trailing ``/`` on a source folder changes what is copied: ``prototype/js/`` copies
  what is inside ``js``, while ``prototype/js`` copies the folder ``js`` itself. The
  commands below use each form on purpose.
- Add ``-n`` (dry run) to see what would be copied or deleted without changing
  anything, for example ``rsync -avn --delete ...``. Worth doing before any command
  with ``--delete``.

Run these from the root of this repo on your laptop. Each robot's login is
``f1-wsu-<number>`` at its address, for example ``f1-wsu-2@192.168.1.202`` for robot
#2 and ``f1-wsu-6@192.168.1.206`` for robot #6. The password is the robot's login
password.

To the development folder, ``~/diag`` (then start it with ``./start_diagnostics.sh``):

.. code-block:: bash

   ROBOT=f1-wsu-2@192.168.1.202

   rsync -av prototype/dashboard.html prototype/start_diagnostics.sh \
     prototype/system_diagnostics.py prototype/camera_http.py \
     prototype/css prototype/js prototype/tools \
     "$ROBOT":diag/

To ``f1tenth_stack`` on a robot that runs the dashboard from bringup, then rebuild:

.. code-block:: bash

   ROBOT=f1-wsu-6@192.168.1.206
   STACK=f1tenth_ws/src/f1tenth_system/f1tenth_stack   # relative to the robot's home folder

   rsync -av prototype/dashboard.html "$ROBOT:$STACK/dashboard/"
   rsync -av --delete prototype/css/ "$ROBOT:$STACK/dashboard/css/"
   rsync -av --delete prototype/js/  "$ROBOT:$STACK/dashboard/js/"
   rsync -av prototype/system_diagnostics.py prototype/camera_http.py \
     "$ROBOT:$STACK/f1tenth_stack/"

   ssh "$ROBOT" 'source /opt/ros/humble/setup.bash && cd ~/f1tenth_ws && colcon build --packages-select f1tenth_stack'
   # then restart bringup on the robot

``--delete`` makes the robot's ``css/`` and ``js/`` folders match ``prototype/`` exactly, so
a file removed here is removed there too. Those two folders hold only the
dashboard's files, which is why it is safe on them and nowhere else. Leave the
trailing ``/`` on those two lines: ``prototype/js/`` copies the folder's contents, and
``prototype/js`` would make a second ``js`` folder inside it.

Copying into ``src/`` is not enough on its own: the robot runs the built copy in
``install/``, so always run the ``colcon build``.

After editing
"""""""""""""

.. list-table::
   :header-rows: 1
   :widths: 28 36 36

   * - You edited
     - Development copy
     - On a robot
   * - a page file (``dashboard.html``, ``css/``, ``js/``)
     - copy it to the robot, then hard-refresh the browser (Ctrl+Shift+R)
     - ``colcon build --packages-select f1tenth_stack``, then hard-refresh
   * - ``system_diagnostics.py`` or ``camera_http.py``
     - ``./start_diagnostics.sh --stop``, then start it again
     - ``colcon build --packages-select f1tenth_stack``, then restart bringup
   * - ``sensors.yaml`` or ``bringup_launch.py``
     - restart bringup
     - ``colcon build --packages-select f1tenth_stack``, then restart bringup

Before moving a green / yellow / red line, read why it is there in
:ref:`Ranges at a glance <diag-ranges>` and the check's "Why these lines". The
professor signed off on them, and the battery lines came from a test that ran a
pack until the robot lost power.

A note on ``/diagnostics`` reports, which most checks use: each report has a name
(such as ``system: CPU``), a level (0 OK, 1 warning, 2 error, 3 not measured yet), a
one-line message, and key / value pairs. The values are text, such as ``46.1 C``;
the page reads the number out of the text. Every report also appears, with all its
keys, in the Advanced tab's Robot System list.

``system_diagnostics`` builds its reports once a second. Cheap readings (files under
``/proc`` and ``/sys``) are taken every second. Anything that runs another program
(``ping``, ``iw``, ``bluetoothctl``, ``tegrastats``, ``timedatectl``,
``joy_enumerate_devices``) runs on a separate thread every 10 seconds
(``SLOW_PERIOD``), each with a timeout, and the report uses the latest result. Until
that thread's first pass, those reports say "not probed yet" at level 3.

.. _diag-battery:

Battery
^^^^^^^

Shows the main battery's voltage and an estimated charge, and warns before the
pack runs too low.

**Where it comes from.** The motor controller (VESC) measures the battery voltage.
``vesc_driver_node`` publishes it on ``/sensors/core`` about 50 times a second, in
the field ``state.voltage_input``.

**How it is judged.** On the page. Under throttle the voltage swings about 0.2 V
within a second, so the page keeps the last 5 seconds of readings and judges their
median, not the latest reading. Green at 11.6 V or more, yellow from 11.1 to
11.6 V ("low, get a spare pack ready"), red below 11.1 V ("replace the pack
soon"). The percentage is a straight line from 11.1 V (0%) to 12.6 V (100%).

**Why these lines.** A run-down test on robot #2 started at 10.4 V, and the robot
lost power about five minutes later at 8.8 V or below, falling faster below about
10 V. Driving draws far more current than that idle test, so red sits at 11.1 V
(3.7 V per cell) to leave time to swap the pack. Nothing on the car protects the
pack from running too low, so this red is the only warning. Yellow at 11.6 V is a
convention: a buffer to get a spare ready. Signed off by the professor as a
starting value; see :ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** ``/sensors/core``, field ``state.voltage_input``.

**On the page.** The Battery card on the Overview (number, gauge and bar), the
battery in the driving view's top bar, and the headline:
the battery counts toward it even though it has no row in the Subsystems table.
If no reading has arrived and ``/sensors/core`` does not exist, the battery is red
("/sensors/core unavailable").

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting, current value
   * - Yellow line
     - ``js/config.js``
     - ``BATT_WARN = 11.6`` (volts)
   * - Red line, and 0% on the gauge
     - ``js/config.js``
     - ``BATT_ERR = 11.1``
   * - 100% on the gauge
     - ``js/config.js``
     - ``BATT_FULL = 12.6``
   * - Smoothing window
     - ``js/config.js``
     - ``BATT_WINDOW_MS = 5000`` (the median is taken in ``onVesc()`` in ``js/graph-data.js``)
   * - Percentage formula
     - ``js/helpers.js``
     - ``batteryEstimate()``
   * - Card wording and colours
     - ``js/status-panels.js``
     - ``renderBattery()``
   * - Subsystem wording
     - ``js/health.js``
     - the battery part of ``subsystemData()``

.. _diag-vesc:

Motor controller (VESC): temperature and faults
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Shows whether the motor controller is running, its power transistors' (FET)
temperature, and any fault it reports.

**Where it comes from.** ``/sensors/core`` from ``vesc_driver_node``: ``state.temp_fet``
(temperature, in C) and ``state.fault_code`` (0 is no fault). The temperature is
only filled in on cars with the VESC driver patch (robots #2 and #6); without it
the field is always exactly ``0.0``.

**How it is judged.** On the page. The VESC row is red if ``vesc_driver_node`` is
not running or ``fault_code`` is not 0. Otherwise the FET temperature decides:
green below 65 C, yellow from 65 C, red from 80 C. A reading of exactly 0.0 is
treated as "no reading" (the missing patch), not as 0 C.

**Why these lines.** The VESC shuts itself off with an over-temperature fault near
85 C, so red at 80 C comes before that. Idle reads about 31 C. The car has never
been measured on a long drive, so these are provisional. Signed off by the
professor as a starting value; see :ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** ``/sensors/core``, fields ``state.temp_fet`` and ``state.fault_code``;
the node list from rosapi.

**On the page.** The VESC row in Subsystems, and the FET (VESC) row in the
Temperature tile.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting, current value
   * - Temperature lines
     - ``js/config.js``
     - ``FET_WARN = 65``, ``FET_ERR = 80`` (C)
   * - Fault code names
     - ``js/config.js``
     - ``FAULTS``
   * - "No motor sensor" cut-off
     - ``js/config.js``
     - ``MOTOR_ABSENT = -20`` (the motor has no sensor fitted and reads about -74 C)
   * - Row wording
     - ``js/health.js``
     - the VESC part of ``subsystemData()``

VESC USB device
^^^^^^^^^^^^^^^

Catches an unplugged motor controller before its topic even goes quiet.

**Where it comes from.** ``system_diagnostics`` checks that ``/dev/sensors/vesc``
exists. That name is a link the VESC's udev rule creates to the real serial
device (for example ``/dev/ttyACM0``).

**How it is judged.** On the robot: OK if it exists, error if not (the report then
lists any ``/dev/ttyACM*`` devices it did find).

**What is sent.** Report ``system: VESC device``, keys ``path`` and ``resolves to``.

**On the page.** The Robot System list.

**To change.** The path is in ``vesc_device()`` in ``system_diagnostics.py``.

.. _diag-board-temp:

Board temperatures
^^^^^^^^^^^^^^^^^^

Shows how hot the Jetson's chip is. It slows itself down at 70 C and 99 C and
shuts off at 104.5 C (measured on robot #2).

**Where it comes from.** ``system_diagnostics`` reads every Linux thermal zone,
``/sys/devices/virtual/thermal/thermal_zone*/temp`` (thousandths of a degree) with
its name from ``.../type``, once a second. On these Jetsons the zones are
``tj-thermal`` (junction, the hottest point), ``cpu-thermal``, ``gpu-thermal``,
``soc0-thermal`` to ``soc2-thermal``, and ``cv0`` to ``cv2``, which often fail to read; a
zone that fails is skipped for that second and listed as "unreadable this pass".

**How it is judged.** Twice:

- The report's level, on the robot, from ``tj-thermal`` (or the hottest zone on a
  board without one): yellow from 70 C, red from 85 C.
- The Temperature tile's rows, on the page, each graded with the same 70 and
  85 C; the tile takes the worst row, including the VESC's FET row.

**Why these lines.** They come from the Jetson's own trip points, read on robot
#2: it slows itself down at 70 C and 99 C, and shuts off at 104.5 C. Idle is about
50 C. Yellow marks the first slowdown; red leaves about 14 C before the second.
Not measured on a long drive. Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: Thermal``, one key per zone named as the zone
(``tj-thermal``, ``cpu-thermal``, ``gpu-thermal``, ``soc0-thermal``...), values like
``46.1 C``.

**On the page.** The Temperature tile (Junction, CPU, GPU and FET (VESC) rows; the
SoC zones are in the Junction row's hover text), and the driving view's bottom
bar.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting, current value
   * - Report lines
     - ``system_diagnostics.py``
     - ``TJ_WARN, TJ_ERR = 70.0, 85.0`` (C)
   * - Tile row lines
     - ``js/metrics.js``
     - ``gradeValue(t, 70, 85)`` in ``jetsonRow``; keep it the same as the report
   * - Which zones get a row
     - ``js/metrics.js``
     - the ``jetsonRow(...)`` calls in the Temperature part of ``metricTiles()``

.. _diag-cpu:

CPU
^^^

Shows how busy the processor is.

**Where it comes from.** ``system_diagnostics`` reads, once a second:

- ``/proc/loadavg``: the load average over 1, 5 and 15 minutes (how many processes
  were running or waiting to run, on average).
- The number of cores, from Python's ``os.cpu_count()`` (6 on these Jetsons).
- ``/proc/stat``: the CPU's time counters. Comparing them with the previous second
  gives the percent of that second the CPU was busy. Time spent waiting for the
  disk counts as idle, so writing a log file does not look like a busy CPU.

**How it is judged.** On the robot, by the 1 minute load average: yellow when it is
above the number of cores, red above twice the number of cores. The busy percent
is shown but not graded.

**Why these lines.** A load above the core count means work is waiting for a
core. The CPU is capped at 1.51 GHz in the 15 W power mode, so the board can be
slower than expected without being hot or broken. Signed off by the professor as a
starting value; see :ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: CPU``, keys ``cores``, ``load 1m``, ``load 5m``,
``load 15m``, ``usage %``.

**On the page.** The CPU tile: the big number is ``usage %``, the line under it is
``load 1m``, and the colour is the report's level. So the tile can show a low
percentage in yellow if the load average is high. If ``usage %`` is missing, the
tile shows the load average instead.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting
   * - Lines
     - ``system_diagnostics.py``
     - inside ``cpu()``: ``ERROR if l1 > self.ncores * 2 else WARN if l1 > self.ncores``
   * - How busy percent is worked out
     - ``system_diagnostics.py``
     - ``cpu_busy_pct()``
   * - Tile
     - ``js/metrics.js``
     - the CPU part of ``metricTiles()``

.. _diag-ram:

Memory (RAM)
^^^^^^^^^^^^

Shows how much memory is left.

**Where it comes from.** ``system_diagnostics`` reads ``/proc/meminfo`` once a second:
``MemTotal``, ``MemAvailable`` (memory programs can still get, including what Linux
would free from its cache) and swap.

**How it is judged.** On the robot, by the percent available: yellow below 20%,
red below 10%.

**Why these lines.** Idle reads 63 to 80% available, so yellow and red mean
something is using far more than usual. Signed off by the professor as a starting
value; see :ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: Memory``, keys ``total``, ``available``,
``available %``, ``swap used``.

**On the page.** The RAM tile shows the percent used (100 minus ``available %``),
with the free amount under it; the colour is the report's level.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting, current value
   * - Lines
     - ``system_diagnostics.py``
     - ``MEM_WARN, MEM_ERR = 20.0, 10.0`` (percent available)
   * - Tile
     - ``js/metrics.js``
     - the MEMORY part of ``metricTiles()``

.. _diag-disk:

Disk
^^^^

Warns before the robot's disk fills up.

**Where it comes from.** ``system_diagnostics`` asks Python's ``shutil.disk_usage("/")``
for the root filesystem once a second (the NVMe drive, about 1 TB).

**How it is judged.** On the robot, by percent used: yellow above 85%, red above 95%.

**Why these lines.** Common defaults, not part of the professor's sign-off. The
disk is about 1 TB and idle is under 5% used.

**What is sent.** Report ``system: Storage``, keys ``total``, ``used``, ``free``, ``used %``.

**On the page.** The Robot System list. There is no tile.

**To change.** ``DISK_WARN, DISK_ERR = 85.0, 95.0`` in ``system_diagnostics.py``.

.. _diag-gpu:

GPU
^^^

Shows how busy the graphics processor is, which vision and machine learning code
use.

**Where it comes from.** ``system_diagnostics`` reads the GPU driver's ``load`` file
once a second. Its location differs between Jetson models, so the node searches
the paths in ``GPU_LOAD_GLOBS`` at startup (on robot #6:
``/sys/devices/platform/bus@0/17000000.gpu/load``). The file counts in tenths of a
percent (0 to 1000). The clock speed comes from the GPU's ``cur_freq`` file under
``/sys/class/devfreq/``. If the load file does not exist, the node falls back to the
``GR3D_FREQ`` field of ``tegrastats``, read every 10 seconds.

**How it is judged.** On the robot. Yellow once the GPU has been at 95% or more for
5 seconds in a row (5 readings, one a second). There is no red: a busy GPU just
means something is using it.

**Why these lines.** A convention: a busy GPU means a heavy job is running, which
is normal. Heat from it shows up in the board temperature, so there is no red.
Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: GPU``, keys ``usage %``, ``freq``, ``source`` (the file
or ``tegrastats``).

**On the page.** The GPU tile: the percent, with the clock speed and source under
it; the colour is the report's level.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - What
     - File
     - Setting, current value
   * - Warning line
     - ``system_diagnostics.py``
     - ``GPU_WARN = 95.0`` (percent)
   * - How long it must stay high
     - ``system_diagnostics.py``
     - ``GPU_SUSTAIN_S = 5`` (seconds)
   * - Where to look for the load file
     - ``system_diagnostics.py``
     - ``GPU_LOAD_GLOBS``

Power, uptime and reboots
^^^^^^^^^^^^^^^^^^^^^^^^^

Shows how long the robot has been on, and notices when it rebooted, which on these
cars usually means the battery dipped too low.

**Where it comes from.** ``system_diagnostics`` reads ``/proc/uptime`` once a second.
Every 10 seconds it also runs ``tegrastats`` and records the power rails
(``VDD_IN``, ``VDD_CPU_GPU_CV``, ``VDD_SOC``, in milliwatts).

**How it is judged.** On the robot. The node compares each uptime reading with its
own previous one, and if uptime went down it reports an error, "REBOOTED - uptime
went backwards", then stays at least yellow with the time it happened. In practice
this does not catch a real reboot: rebooting the board restarts the node too, so
there is no previous reading to compare with. The useful sign is the uptime itself.
An uptime of a few minutes that nobody expected means the robot restarted, and on
these cars that usually means the battery dipped.

**What is sent.** Report ``system: Power``, keys ``uptime``, ``last reboot detected``,
and one key per power rail.

**On the page.** Uptime in the ROS Graph card; the rest in the Robot System list.

**To change.** ``power()`` in ``system_diagnostics.py``.

.. _diag-wifi:

Wi-Fi
^^^^^

Shows how good the robot's Wi-Fi link is. This link carries the page, so a bad one
makes the page lag or freeze.

**Where it comes from.** ``system_diagnostics``, every 10 seconds:

- Signal strength from ``iw dev <wifi> link``, where ``<wifi>`` is the first network
  interface whose name starts with ``wl`` (``wlP1p1s0`` on these Jetsons).
- Packet loss and round trip time from 5 pings, 0.2 s apart, to the default
  gateway (the router), found with ``ip route show default``. It pings the router,
  not the internet, because the robot does not need the internet.
- Whether the interface has a link, from ``/sys/class/net/<wifi>/carrier``.

**How it is judged.** On the page, each value on its own, and the row takes the
worst:

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * -
     - Green
     - Yellow
     - Red
   * - Signal
     - -67 dBm or better
     - below -67 dBm
     - below -75 dBm
   * - Packet loss
     - under 1%
     - 1% or more
     - 5% or more
   * - Round trip
     - under 30 ms
     - 30 ms or more
     - 100 ms or more

No link at all is red ("down"). A value that has not been measured yet is left out.

**Why these lines.** Common Wi-Fi conventions, not measurements. In the lab the
robots read -39 to -43 dBm, 0% loss and 1.4 to 3.2 ms; bad sessions in the past
lost 90 to 100% of packets. Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: Network``: keys ``wifi signal`` (dBm), ``wifi loss %``,
``wifi rtt ms``, ``wifi gateway``, and a key named after the interface (``wlP1p1s0``)
whose value contains ``carrier=1`` (link up) or ``carrier=0``.

**On the page.** The Wi-Fi row of the Network tile, and the footer.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - What
     - File
     - Setting, current value
   * - Signal lines
     - ``js/config.js``
     - ``WIFI_SIGNAL_WARN = -67``, ``WIFI_SIGNAL_ERR = -75`` (dBm)
   * - Loss lines
     - ``js/config.js``
     - ``WIFI_LOSS_WARN = 1``, ``WIFI_LOSS_ERR = 5`` (percent)
   * - Round trip lines
     - ``js/config.js``
     - ``WIFI_RTT_WARN = 30``, ``WIFI_RTT_ERR = 100`` (ms)
   * - How it is measured
     - ``system_diagnostics.py``
     - the Wi-Fi part of ``_probe_slow()``, and ``parse_wifi()``
   * - The row
     - ``js/metrics.js``
     - ``networkRows()``, shared by the tile and the footer

Bluetooth
^^^^^^^^^

Shows whether the Jetson's Bluetooth radio is on. It must be on for the controller
to connect.

**Where it comes from.** ``bluetoothctl show``, every 10 seconds: ``Powered: yes`` or
``Powered: no``.

**How it is judged.** On the page: on is green; off, or no adapter, is yellow.

**What is sent.** Report ``system: Network``, key ``bluetooth``: ``on``, ``off``,
``no adapter`` or ``unknown``.

**On the page.** The Bluetooth row of the Network tile, and the footer.

**To change.** ``bt_power()`` in ``system_diagnostics.py``; the row in ``networkRows()``
in ``js/metrics.js``.

.. _diag-lidar:

Lidar
^^^^^

Shows whether the lidar is connected and scanning properly, and draws what it
sees.

The lidar is a Hokuyo UST-10LX on its own Ethernet cable at ``192.168.0.10``. It
accepts only one connection at a time. Its driver, ``urg_node``, connects to it and
publishes ``/scan`` 40 times a second: 1081 distances in a 270 degrees fan in front of the
car.

**Where it comes from.** Four separate pieces, because "is the lidar OK" has
several different failures:

1. **The cable.** ``system_diagnostics`` reads ``/sys/class/net/<if>/carrier`` for each
   network interface every 10 seconds. The lidar's interface is the Ethernet one
   (name starting ``en``, ``enP8p1s0`` on these Jetsons).
2. **The lidar answering.** ``system_diagnostics`` pings ``192.168.0.10`` twice every 10
   seconds.
3. **The driver.** Whether ``/urg_node`` is in rosapi's node list, and how many
   publishers ``/scan`` has (rosapi).
4. **The scans.** The page subscribes to ``/scan`` and reads ``ranges``, ``angle_min``,
   ``angle_max``, ``angle_increment``, ``range_min`` and ``range_max``. ``urg_node`` also
   measures its own scan rate and publishes it on ``/diagnostics``, with the range
   it accepts (40 Hz plus or minus 5%, so 38 to 42 Hz, from ``sensors.yaml``).

**How it is judged.** On the page, in this order:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Situation
     - LiDAR row
   * - ``/urg_node`` is not running
     - red: "/urg_node is not running"
   * - ``/scan`` has more than one publisher
     - red: two lidar drivers; one is left over from an earlier run and holds the lidar's only connection. The message gives the fix
   * - scans arriving, rate outside 38 to 42 Hz
     - yellow, with the rate
   * - scans arriving, rate inside
     - green, with the rate
   * - no scans (stale, silent or missing)
     - red; if the lidar still answers ping, the message adds that the driver cannot connect, and gives the fix

The Network tile's Lidar row is judged separately: "unplugged" (no cable link) and
"no reply" (cable in, no ping answer, usually no power) are red, "answering" is
green.

**Why these lines.** The rate range is ``urg_node``'s own, 40 Hz within 5%. No
scans is red because the car cannot see. Signed off by the professor as a starting
value; see :ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** ``/scan`` (fields above); report ``urg_node: Laser Scan topic status``,
keys ``Actual frequency (Hz)``, ``Minimum acceptable frequency (Hz)``,
``Maximum acceptable frequency (Hz)``; report ``system: Network``, the key starting
``lidar `` (``lidar 192.168.0.10``, value ``reachable, 0.25 ms`` or ``NO REPLY``) and the
Ethernet interface's key with ``carrier=``. ``urg_node`` also sends
``urg_node: Hardware Status`` (device status, error counts, serial number), shown as
is in the Robot System list.

**On the page.** The LiDAR row in Subsystems; the Lidar row of the Network tile and
the footer; the LiDAR card (plot, distances ahead / left / right / closest, Select
beams); the driving view's LiDAR pane or floating LiDAR window; and the camera's
edge lights and "Very close" warning.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - What
     - File
     - Setting, current value
   * - Acceptable scan rate
     - ``f1tenth_stack/config/sensors.yaml`` in ``f1tenth_system``
     - ``diagnostics_tolerance: 0.05``. Restart bringup
   * - How the row is judged and worded
     - ``js/health.js``
     - the LiDAR part of ``subsystemData()``
   * - The lidar's address
     - ``system_diagnostics.py``
     - ``LIDAR_IP = "192.168.0.10"``
   * - "Close" and "very close"
     - ``js/metrics.js``
     - ``LIDAR_CLOSE = 1.0``, ``LIDAR_NEAR = 0.5`` (metres); used by the card, the Drive tab and the edge lights
   * - Plot range buttons, Auto range
     - ``js/metrics.js``
     - ``LIDAR_RANGES``, ``AUTO_MIN_RANGE = 2``
   * - Edge light directions
     - ``js/cockpit.js``
     - ``COCKPIT_GLOW_SECTORS``

.. _diag-camera:

Camera
^^^^^^

Streams the front camera, and checks it is connected properly and delivering
frames.

**Where it comes from.** Two separate things:

1. **The stream.** GStreamer opens the RealSense's colour camera at ``/dev/video4``
   (640x480, 30 fps), compresses each frame to JPEG and sends the frames on TCP
   port 8081. ``camera_http.py`` reads that as fast as it arrives and keeps only the
   newest whole frame. Each viewer at ``http://<robot>:8082/camera.mjpg`` is sent the
   newest frame whenever its connection can take one; frames it could not keep up
   with are skipped, so a slow link costs frame rate, never delay. It counts the
   frames actually delivered to each viewer and reports them at
   ``http://<robot>:8082/stats`` as JSON: ``viewers``, ``fps``, ``last_frame_s`` (seconds
   since the last frame). So ``fps`` is what you actually see, not what the camera
   produces.
2. **The USB link.** ``system_diagnostics`` looks through ``/sys/bus/usb/devices/*/``
   every 10 seconds for a device with Intel's vendor ID (``idVendor`` is ``8086``)
   and reads its ``speed``, ``product`` and ``serial``.

**How it is judged.** The USB link on the robot: no Intel device is red, a link
slower than 5000M (USB 3) is yellow. The frame rate on the page, every 2 seconds
while the picture is showing: no frame for more than 3 seconds is red, under 15
fps is yellow. The Camera row takes the worse of the two.

**Why these lines.** 15 fps is half the camera's 30. The RealSense is a USB 3
camera, so a slower link means it is in the wrong port or on the wrong cable.
Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: Camera``, keys ``product``, ``usb serial``,
``usb port``, ``link speed``; and the ``/stats`` JSON, of which the page reads ``fps``
and ``last_frame_s``.

**On the page.** The camera picture (Overview and the driving view), its
status tag (``LIVE - 30 fps``), and the Camera row in Subsystems. The page finds the
camera on port 8082 of the robot rosbridge is connected to, and retries every 3
to 15 seconds while the robot is up and the picture is not. Typing an address
under "Change camera address" switches that off until "Use automatic" is pressed.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - What
     - File
     - Setting, current value
   * - Low frame rate line
     - ``js/config.js``
     - ``CAMERA_MIN_FPS = 15``
   * - No-frame line
     - ``js/config.js``
     - ``CAMERA_NO_FRAME_S = 3`` (seconds)
   * - USB check
     - ``system_diagnostics.py``
     - ``camera()``, and the camera part of ``_probe_slow()``
   * - Picture size, frame rate, device
     - ``launch/bringup_launch.py`` (robot) or ``start_diagnostics.sh`` (development)
     - the ``gst-launch-1.0`` command; ``camera_device`` / ``--camera-device`` (default ``/dev/video4``)
   * - Ports
     - ``camera_http.py``, ``js/camera.js``
     - ``GSTREAMER_PORT = 8081``, ``HTTP_PORT = 8082``; ``CAMERA_PORT = 8082`` in the page
   * - How much a slow viewer may queue
     - ``camera_http.py``
     - ``SEND_BUFFER = 64 * 1024`` (bytes, about two frames)
   * - Retry timing
     - ``js/camera.js``
     - ``CAMERA_RETRY_MIN_MS = 3000``, ``CAMERA_RETRY_MAX_MS = 15000``

Speed and odometry
^^^^^^^^^^^^^^^^^^

Shows how fast the car is going, and whether odometry is working.

**Where it comes from.** ``vesc_to_odom_node`` turns the motor's speed into a
velocity and publishes ``/odom`` and ``/tf``. The page reads ``/odom``, field
``twist.twist.linear.x``, in m/s (negative is reverse).

``vesc_to_odom_node`` publishes nothing until it has seen one steering command. So
after every bringup, ``/odom`` and ``/tf`` are silent on a healthy car until someone
steers.

**How it is judged.** On the page. The Odometry row is red if the node is not
running, or ``/odom`` is stale, silent or missing. Before the first steering command
it is green, "Idle - odometry starts after the first steering command", and
``/odom`` and ``/tf`` show ``IDLE``. The Speed tile goes stale if ``/odom`` stops for 2
seconds.

**What is sent.** ``/odom``, field ``twist.twist.linear.x``.

**On the page.** The Speed tile (MPH and m/s), the Odometry row, and the driving
view's speed readout and speedometer, in the unit chosen in its Settings (m/s,
km/h or mph; ``SPEED_UNITS`` in ``js/cockpit.js``).

**To change.** The Speed tile is ``getSpeedMetric()`` in ``js/metrics.js``; the row is
the odometry part of ``subsystemData()`` in ``js/health.js``; the "waits for a steer"
rule is ``waitsForSteer`` in ``TOPICS`` (``js/config.js``) and ``odomWaitingForSteer()``
in ``js/health.js``.

.. _diag-controller:

Controller
^^^^^^^^^^

Shows whether the PS4 controller is connected and whether ROS can read it. The
physical controller is the car's backup stop, so the page says plainly when there
is none.

**Where it comes from.**

- ``system_diagnostics`` lists ``/dev/input/js*`` every second. That device exists
  only while a controller is attached, so a disconnect shows within a second.
- Every 10 seconds it runs ``bluetoothctl devices`` and ``bluetoothctl info`` to find
  a connected controller and its name.
- While a controller is attached, it also runs ``joy_enumerate_devices`` every 10
  seconds. That lists the controllers ROS's ``joy`` driver can actually open. If the
  controller is attached but not listed, ROS cannot read it, which happens when
  the login user is not in the ``input`` group.
- The page reads ``/joy``, fields ``buttons[4]`` (L1) and ``buttons[5]`` (R1), to know
  whether someone is holding a deadman button.

**How it is judged.** On the robot:

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Situation
     - Level
   * - no controller
     - OK, "no controller connected" (idle is not a fault)
   * - attached and connected over Bluetooth
     - OK, "connected"
   * - attached, no Bluetooth link
     - yellow (also normal for a few seconds after connecting)
   * - attached, but ROS cannot read it
     - red, "add the user to the input group"

**Why these lines.** No controller is normal when nobody is driving. A controller
ROS cannot read looks connected but can neither drive nor stop the car, so it is
red. Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**What is sent.** Report ``system: Gamepad``, keys ``js devices``, ``bluetooth``,
``device``, ``battery %`` (always "not exposed by this driver": the Jetson's kernel
lacks the driver that reports a PS4 controller's charge); ``/joy``, field ``buttons``.

**On the page.** The Controller row in Subsystems, the controller chip in the
driving view's top bar. **Run joystick check** (Advanced tab)
runs the same ``joy_enumerate_devices`` check on demand and explains the result.
**Disconnect controller** (Drive tab) drops the Bluetooth link; the robot refuses
while L1 or R1 is held, unless the emergency stop is on.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - What
     - File
     - Setting
   * - How it is judged
     - ``system_diagnostics.py``
     - ``gamepad()``
   * - What is probed
     - ``system_diagnostics.py``
     - the gamepad part of ``_probe_slow()``
   * - Deadman buttons
     - ``system_diagnostics.py``, ``js/estop.js``
     - ``JOY_DEADMEN = (4, 5)``; ``JOY_L1 = 4``, ``JOY_R1 = 5``. Both must match ``joy_teleop.yaml``
   * - Joystick check wording
     - ``system_diagnostics.py``
     - ``joy_verdict()``

The fix for "ROS cannot read it" is ``sudo usermod -aG input <user>`` on the robot,
then log out and back in.

Who is in control
^^^^^^^^^^^^^^^^^

Shows which input the car is listening to: nobody, the controller, or ``/drive``
(the page or an autonomous stack).

**Where it comes from.** ``ackermann_mux`` chooses between its inputs and publishes
its own status on ``/diagnostics``, including whether each input is ``masked`` (being
ignored) or ``unmasked``. An input that has been quiet for 0.2 s is masked
(``mux.yaml``). Measured on robot #2: with the controller connected and nothing
held, the mux already reports the joystick input as unmasked. So "Joystick" means
the controller is connected and its input is live, not that a deadman is held.

**How it is judged.** On the page: joystick unmasked is "Joystick", otherwise
navigation unmasked is "Navigation / web", otherwise "Idle". All three are green;
only the mux not running is red.

**What is sent.** Report ``ackermann_mux: Ackermann mux status``, keys
``velocity topics.joystick`` and ``velocity topics.navigation``.

**On the page.** "Control" in the status banner, and the Control Mode row in
Subsystems.

**To change.** ``onDiagnostics()`` in ``js/graph-data.js`` reads the keys; the row is
the control mode part of ``subsystemData()`` in ``js/health.js``.

The driving view
^^^^^^^^^^^^^^^^

The Drive tab and full screen are one view, built from panes: Camera, LiDAR and
Controls. This entry is about how that view is laid out; the next one is about the
driving itself.

**Where it lives.** On the Drive tab the view sits in the page, under the safety
warning. Its **Full screen** button makes the same view cover the screen, and
**Exit** (or Esc) puts it back. The Overview's camera buttons open it full screen
directly: **Full screen** with the Camera layout, **Split** with the Watch layout.
Opening it from the Overview does not change the Drive tab's own layout.

**Panes and layouts.** The pane buttons at the top turn Camera, LiDAR and Controls
on or off. Panes sit side by side; drag the bar between two to resize them, and
drag a pane's title onto another to swap them. The layouts menu has Camera, Watch
(camera and LiDAR), Drive (camera and controls), Drive + LiDAR, and LiDAR. Each
layout keeps your own changes in the browser, and Reset puts it back.

**Desktop arrangement.** The controls float over the picture as a see-through card
(drag its title to move it, the x to close it), or dock as a column beside the
pictures (**Dock the controls**). The LiDAR can also float over the camera as a
small window you can move and resize (**A small LiDAR window on the picture**).
The "Very close" warning floats on the picture; drag it or hide it.

**The top bar.** Left: who is driving, Disconnect controller, battery. Right: the
actions, with Emergency stop last. Alerts get their own row only when there is
one. The bar can be hidden (its hide button, or Settings); a corner cluster then
keeps Emergency stop, Arm and Show.

**Settings** holds every "how it looks" option in one panel: the arrangement
switches above, Hide the top bar, Controls only (phones), the edge lights and the
"Very close" warning, the LiDAR view and range, speed units, keep the screen awake,
buzz when something is very close (phones), thumb stick placement, reconnect
camera, and **Reset all view settings**, which clears them all and reloads the
page.

**Phones** (anything touch-first, or 900 px wide or less): one picture at a time,
Camera and LiDAR taking turns (unless the LiDAR floats over the camera). Driving
needs the phone sideways and full screen, so turning Controls on from the Drive
tab opens full screen; the controls are then a steering stick, a throttle stick
and STOP. Turning the phone upright disarms.

**Where it is saved.** All of these settings are kept per browser in
``localStorage``, under the keys listed in ``VIEW_KEYS`` in ``js/cockpit.js``; another
browser or device starts from the defaults.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting
   * - Ready-made layouts
     - ``js/cockpit.js``
     - ``LAYOUTS``
   * - What counts as a phone
     - ``js/cockpit.js``
     - ``COCKPIT_TOUCH_QUERY`` (touch-first, or 900 px wide or less)
   * - Edge light directions
     - ``js/cockpit.js``
     - ``COCKPIT_GLOW_SECTORS``
   * - Speed units
     - ``js/cockpit.js``
     - ``SPEED_UNITS``
   * - Saved settings that Reset clears
     - ``js/cockpit.js``
     - ``VIEW_KEYS``
   * - The look (sizes, colours, the frosted style)
     - ``css/dashboard.css``
     - the ``cockpit`` rules
   * - The markup (buttons, Settings panel)
     - ``dashboard.html``
     - the ``cockpit`` element

Driving from the page
^^^^^^^^^^^^^^^^^^^^^

Drives the car from a browser, through the same input an autonomous stack uses.

**Where it comes from.** The driving view's controls (the pad, the keys, or a
phone's thumb sticks) set what the Drive tab's controller sends. It publishes
``ackermann_msgs/AckermannDriveStamped`` on ``/drive``, the mux's navigation input, 20
times a second while armed and while the pad, a key or a stick is held. The
physical controller has a higher priority in the mux, so holding its deadman
always overrides the page.

**The rules.**

- **Arming** needs a connection, the "area is clear" box ticked, no emergency
  stop, and nobody else sending on ``/drive``.
- **Deadman.** Commands go out only while the pad, a key (W A S D or the arrows)
  or a stick is held. Letting go sends 5 zero-speed commands, which is what stops
  the car: the mux sends no zero of its own when an input goes quiet.
- **Ramping.** Speed rises at most 5 m/s per second (3 m/s in 0.6 s); steering
  changes at most 2.5 rad per second. Stopping is never ramped.
- **Bad values.** Any speed or steering that is not a number is sent as a stop.
- **Limits.** 3 m/s and 19 degrees by default, always shown in the controls. Unlocking
  5 m/s or 23.5 degrees needs a warning dialog, and switches off again when you leave the
  Drive tab.
- **Closing the controls.** On a desktop it does not disarm: the keys keep driving
  (Space stops) as long as the Drive tab is underneath, and a note says so. On a
  phone the sticks and STOP go with the controls, so it disarms.
- **Disarming** happens on STOP, Space or Esc, leaving the Drive tab or the
  driving view, leaving full screen, the window losing focus or going to the
  background, the connection dropping, the emergency stop, arranging the sticks,
  resetting the view settings, and on a phone closing the controls or turning it
  upright.
- **Who is driving.** The page reads ``/drive``'s publishers from rosapi and the
  messages' ``header.frame_id``, so it can tell another page or an autonomous stack
  from itself, and ignore the watchdog's zeros (marked ``"drive_watchdog"``).

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - What
     - File
     - Setting, current value
   * - Default limits
     - ``js/drive.js``
     - ``NORMAL_MAX_SPEED = 3.0`` (m/s), ``NORMAL_MAX_STEER = 0.34`` (rad, 19 degrees)
   * - Unlocked limits
     - ``js/drive.js``
     - ``HIGH_MAX_SPEED = 5.0``, ``FULL_MAX_STEER = 0.41`` (23.5 degrees)
   * - Ramping
     - ``js/drive.js``
     - ``DRIVE_ACCEL = 5.0`` (m/s per second), ``STEER_RATE = 2.5`` (rad per second)
   * - Command rate, stop burst
     - ``js/drive.js``
     - ``DRIVE_HZ = 20``, ``STOP_BURST = 5``
   * - Keys
     - ``js/drive.js``
     - ``KEY_FWD``, ``KEY_BACK``, ``KEY_LEFT``, ``KEY_RIGHT``
   * - When closing the controls disarms
     - ``js/cockpit.js``
     - the start of ``applyPanes()``

Drive watchdog
^^^^^^^^^^^^^^

Stops the car if the page loses its connection while driving.

**Where it comes from.** ``system_diagnostics`` subscribes to ``/drive``. It notes the
time and speed of every command that is not its own.

**How it works.** 20 times a second it checks: if the last command was moving and
nothing has arrived for 0.3 s, it publishes 5 zero-speed commands on ``/drive``,
marked with ``header.frame_id = "drive_watchdog"``. 0.3 s is longer than the mux's
0.2 s, so a publisher that is still working has already been switched away from
before the watchdog would act. Measured on robot #6: zeros 0.31 to 0.51 s after the
stream was cut.

**What is sent.** Zero-speed commands on ``/drive``; report ``system: Drive watchdog``,
yellow for 60 seconds after it has stopped the car ("stopped the car at ...").

**On the page.** The Robot System list.

**To change.**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - What
     - File
     - Setting, current value
   * - Delay
     - ``system_diagnostics.py``
     - ``DRIVE_QUIET_S = 0.3`` (keep it above the 0.2 s in ``mux.yaml``)
   * - Number of zeros
     - ``system_diagnostics.py``
     - ``DRIVE_STOP_COUNT = 5``
   * - Marker
     - ``system_diagnostics.py`` and ``js/config.js``
     - ``DRIVE_WATCHDOG_FRAME = "drive_watchdog"``, in both; they must match

Emergency stop
^^^^^^^^^^^^^^

Stops the car for everyone (the controller, any page, autonomous code) until
someone releases it.

**How it works.** The button calls the service ``/system_diagnostics/emergency_stop``.
On the robot, the node finds ``ackermann_to_vesc_node`` with ``pgrep`` and freezes it
(``SIGSTOP``). Every input reaches the motor through that one node. The node then
publishes speed 0 on ``/commands/motor/speed`` 50 times a second. Release calls
``/system_diagnostics/emergency_release``, which unfreezes the node (``SIGCONT``); it
is refused, on the page and on the robot, while anyone holds L1 or R1, so the car
never resumes into a live command.

**What is sent.** Report ``system: E-stop``: level 2 while on, with keys ``since`` and
``action`` (what the robot did, such as "froze ackermann_to_vesc_node (pid 1234)").

**On the page.** The red Emergency stop banner, on every open page, from that
report.

**To change.** ``emergency_stop()``, ``emergency_release()`` and ``estop_hold()`` in
``system_diagnostics.py``; ``ESTOP_HZ = 50.0`` for the hold rate; the page side is
``js/estop.js``.

.. _diag-nodes:

Nodes
^^^^^

Shows whether every node bringup should start is running.

**Where it comes from.** Every 5 seconds the page asks rosapi (``/rosapi/nodes``) for
the running nodes. This is more reliable than ``ros2 node list``. A node that was
killed stays listed for 16 to 18 seconds, so a node's topics going quiet is the
faster sign of trouble.

**How it is judged.** On the page, against ``EXPECTED_NODES``: the 8 drive nodes plus
``system_diagnostics``, ``rosbridge_websocket``, ``rosapi`` and ``rosapi_params``.

**Why these lines.** A missing node is a failed bringup, so there is no yellow.
Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**On the page.** "Nodes 12 / 12 up" in the banner, the ROS Graph card, and the
Advanced tab's node table.

**To change.** ``EXPECTED_NODES`` in ``js/config.js``, whenever bringup gains or loses a
node; ``GRAPH_POLL_MS = 5000`` for how often.

.. _diag-topics:

Topics
^^^^^^

Shows whether each topic is publishing as it should.

**Where it comes from.** Every 5 seconds the page asks rosapi which topics exist
(``/rosapi/topics``) and who publishes each one (``/rosapi/publishers``). It subscribes
to every topic in ``TOPICS`` at most 5 times a second, just to see messages arrive,
and to ``/diagnostics`` on every message.

**How it is judged.** On the page. Each topic has a class, and the class decides
what silence means:

.. list-table::
   :header-rows: 1
   :widths: 15 40 45

   * - Class
     - Examples
     - Silence means
   * - ``continuous``
     - ``/scan``, ``/odom``, ``/sensors/core``, ``/tf``, ``/diagnostics``
     - a fault
   * - ``event``
     - ``/joy``, ``/teleop``, ``/ackermann_cmd``, ``/commands/*``
     - nothing; they publish only when someone drives
   * - ``latched``
     - ``/tf_static``
     - nothing; sent once at startup
   * - ``input``
     - ``/drive``, ``/commands/motor/brake``
     - nothing; the stack listens to these

A continuous topic with no message for 2 seconds is ``STALE``; one with a publisher
that never sent anything is ``SILENT``. ``STALE``, slow and not-advertised topics are
yellow; ``SILENT``, ``MISSING`` (not in the graph) and no-publisher topics are red.

**Why these lines.** A single "silence is a fault" rule flagged 16 of 23 topics on
a healthy car, so each topic has a class. The signed-off ranges call a stopped
topic red; this table shows ``STALE`` and not-advertised in yellow, while the
LiDAR and Odometry rows go red. Signed off by the professor as a starting value; see
:ref:`Ranges at a glance <diag-ranges>`.

**On the page.** Key topics in the ROS Graph card, and the Advanced tab's topic
table (click a row to see its live message).

**To change.** ``TOPICS`` in ``js/config.js`` (add a topic, set its class);
``STALE_MS = 2000``; ``classifyTopic()`` in ``js/graph-data.js`` for the states.

Subsystems and the headline
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sums everything up at the top of the page.

**How it is judged.** On the page. Seven subsystems (Controller, VESC, LiDAR,
Odometry, Camera, Battery, Control Mode), each judged as described above. The
headline shows the worst: Failed beats Degraded beats unconfirmed beats Healthy.
The line under it names the subsystems at fault. With no rosbridge connection it
says NOT CONNECTED instead, since nothing can be judged.

**On the page.** The status banner and the Subsystems table (problems first; the
battery is in its own card rather than a row).

**To change.** ``subsystemData()`` and ``renderOverall()`` in ``js/health.js``.

Connection warnings
^^^^^^^^^^^^^^^^^^^

Tells you when what you see may be out of date, and why.

**How it works.** On the page, from what arrives over the websocket:

- **Nothing at all for 4 seconds** (``CONNECTION_STALE_MS``): a red bar, the robot
  went quiet.
- **Services answer, but no topic data for 8 seconds** (``PUBLISH_STALE_MS``): an
  orange bar. rosbridge serves only 10 clients, and this page is one too many.
  Close another dashboard tab.
- **More than 10 clients** (``/client_count``, field ``data``): an orange bar saying some
  dashboards receive nothing. ``/client_count`` is only sent when the number changes,
  so a page that joined later may show a dash instead of a number.

**On the page.** The bars at the top, and "Connected: N people" in the banner.

**To change.** ``CONNECTION_STALE_MS``, ``PUBLISH_STALE_MS`` and ``CLIENT_LIMIT`` in
``js/config.js``; ``js/checks.js``.

Robot name and clock
^^^^^^^^^^^^^^^^^^^^

**Where it comes from.** ``system_diagnostics`` reports the robot's login name (for
example ``f1-wsu-6``), from Python's ``getpass.getuser()``; every robot's hostname is
``ubuntu``, so the login is what tells them apart. Every 10 seconds it runs
``timedatectl show`` to check the clock is synchronised.

**How it is judged.** On the robot: synchronised is OK, not synchronised is yellow.

**What is sent.** Report ``system: Clock``, keys ``Robot``, ``NTPSynchronized``,
``Timezone``, ``NTP``.

**On the page.** "Robot: f1-wsu-6" in the footer; the rest in the Robot System list.

**To change.** ``clock()`` in ``system_diagnostics.py``.

ROS warnings and errors
^^^^^^^^^^^^^^^^^^^^^^^

**Where it comes from.** Every ROS node logs to ``/rosout``. The page reads ``level``,
``name`` and ``msg``, and keeps warnings, errors and fatal messages (level 30 and up).

**On the page.** The ROS Warnings / Errors list on the Advanced tab.

**To change.** ``onLog()`` in ``js/graph-data.js``.

Things to avoid
^^^^^^^^^^^^^^^

- **Do not name a new launch argument** ``port``. Launch arguments are shared with
  included launch files, and rosbridge's already declares ``port``. When the
  dashboard's argument was called ``port``, rosbridge took port 8000, lost it to the
  web server, and failed with "Address already in use" while nothing was on 9090.
  That is why it is ``dashboard_port``.
- **Do not run** ``start_diagnostics.sh`` **on a car whose bringup already starts the
  dashboard.** Two bringups fight over the motor controller and the joystick.
- **Every open dashboard tab is one of rosbridge's 10 clients.** Close tabs you are
  not using, especially when several people are testing.

Checking a change without a robot
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd prototype
   node verify_radar.mjs                       # LiDAR plot geometry
   node verify_testing.mjs                     # Select beams index and angle math
   node verify_system.mjs                      # system panel, joystick check, connection banners
   python3 camera_http.py --self-test          # camera frame splitting, newest-frame relay, frame rate
   python3 system_diagnostics.py --self-test   # emergency stop and controller disconnect logic

These check the logic, not the hardware. Ranges and anything that depends on real
sensors still need a run on a car. From any machine,
``python3 tools/rosbridge_check.py <robot ip>`` checks that rosbridge is up and the
main topics are arriving, with nothing to install.

.. _diag-added:

What was already on the robot, and what this project added
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Already there
^^^^^^^^^^^^^

- **The eight drive nodes** that ``bringup`` starts: ``joy``, ``joy_teleop``,
  ``ackermann_mux``, ``ackermann_to_vesc_node``, ``vesc_driver_node``,
  ``vesc_to_odom_node``, ``urg_node`` and ``static_baselink_to_laser``, with their
  topics and config files (``joy_teleop.yaml``, ``mux.yaml``, ``vesc.yaml``,
  ``sensors.yaml``).
- **Health reports from two drivers.** ``urg_node`` already published the lidar's
  rate and hardware status on ``/diagnostics``, and ``ackermann_mux`` published which
  input is in control.
- **rosbridge** was listed as a dependency in ``f1tenth_stack/package.xml``, but
  nothing started it.
- **The RealSense camera** was on the car, with no stream to a browser.
- **The VESC driver** published ``/sensors/core``, but never filled in the two
  temperature fields, which always read 0.

Added: new files
^^^^^^^^^^^^^^^^

These add to the robot and change nothing that was already there.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Added
     - What it is
   * - ``system_diagnostics.py``
     - the one new ROS node: the ``system: ...`` health statuses, the emergency stop, the drive watchdog, the joystick check, the controller disconnect
   * - ``camera_http.py``
     - not a ROS node; turns the camera's TCP stream into a web stream
   * - the GStreamer camera pipeline
     - a command, not a file; started by the launch file or ``start_diagnostics.sh``
   * - ``dashboard.html``, ``css/``, ``js/``
     - the page
   * - ``start_diagnostics.sh``
     - development only; starts everything by hand

Added: changes to existing files in f1tenth_system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On robot #6, not merged yet.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Change
   * - ``f1tenth_stack/launch/bringup_launch.py``
     - new arguments (``use_lidar``, ``use_camera``, ``use_diagnostics``, ``camera_device``, ``dashboard_port``) and new entries that start ``system_diagnostics``, rosbridge, the web server, the camera pipeline and ``camera_http``. ``urg_node`` now starts only if ``use_lidar`` is true, which is the default. The eight drive nodes and their settings are unchanged
   * - ``f1tenth_stack/setup.py``
     - two ``console_scripts`` entries (``system_diagnostics``, ``camera_http``) and three ``data_files`` lines that install the page
   * - ``f1tenth_stack/package.xml``
     - three dependencies the node needs: ``rclpy``, ``diagnostic_msgs``, ``std_srvs``
   * - ``vesc/vesc_driver/src/vesc_driver.cpp``
     - two lines that fill in ``temp_fet`` and ``temp_motor``. On robots #2 and #6 only. ``vesc`` is a submodule, so this needs its own change to ``Weber-AGV/vesc``

Outside any repo, the login user on each car has to be in the ``input`` group (see
:ref:`Controller <diag-controller>`). The setup team is adding this to every car.

What the additions can do to the car
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Almost everything added only reads. The exceptions:

- **Emergency stop** freezes ``ackermann_to_vesc_node`` and holds the motor at
  speed 0 until Release.
- **The drive watchdog** sends zero-speed commands on ``/drive`` when the page's
  commands stop mid-drive.
- **Driving from the page** publishes on ``/drive``, the input an autonomous stack
  would use.
- **Disconnect controller** drops the controller's Bluetooth link. It is refused
  while a deadman button is held.

.. _diag-files:

Reference: the files
~~~~~~~~~~~~~~~~~~~~

The page
^^^^^^^^

``dashboard.html`` is the markup. It loads ``css/dashboard.css`` and the files in
``js/`` in a fixed order; they share one scope, so ``config.js`` must load first and
``main.js`` last.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - What it does
   * - ``js/config.js``
     - thresholds, timings, the expected nodes and the topic classes
   * - ``js/helpers.js``
     - small shared functions
   * - ``js/connection.js``
     - the rosbridge connection, subscriptions and service calls
   * - ``js/graph-data.js``
     - reads nodes, topics, ``/diagnostics`` and the VESC; works out each topic's state
   * - ``js/health.js``
     - grades each subsystem and the overall headline
   * - ``js/metrics.js``
     - the Overview tiles (Speed, CPU, RAM, GPU, Temperature, Network) and the LiDAR plot
   * - ``js/status-panels.js``
     - battery card, uptime, footer, ROS graph panel
   * - ``js/system-tiles.js``
     - the list of everything ``system_diagnostics`` reports
   * - ``js/advanced-panels.js``
     - the Advanced tab's topic and node tables
   * - ``js/checks.js``
     - connection warnings and the Run joystick check button
   * - ``js/camera.js``
     - the camera stream, reconnecting, frame rate
   * - ``js/lidar-select.js``
     - Select beams: pick ``/scan`` indexes for test code
   * - ``js/drive.js``
     - the Drive tab's controls and limits
   * - ``js/estop.js``
     - the Emergency stop button
   * - ``js/cockpit.js``
     - the driving view (Drive tab and full screen): panes, layouts, floating controls and LiDAR, Settings, phone controls
   * - ``js/icons.js``
     - the line icons
   * - ``js/main.js``
     - the render loop, buttons, tabs and startup

On the robot
^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - What it does
   * - ``system_diagnostics.py``
     - the health node, emergency stop, drive watchdog, joystick check and controller disconnect. Services: ``/system_diagnostics/emergency_stop``, ``emergency_release``, ``joystick_check``, ``controller_disconnect``
   * - ``camera_http.py``
     - relays the camera stream from port 8081 to 8082, with ``/stats``
   * - ``start_diagnostics.sh``
     - development only: starts and stops everything
   * - ``launch/bringup_launch.py`` (in ``f1tenth_stack``)
     - starts everything on a robot
   * - ``setup.py`` (in ``f1tenth_stack``)
     - installs the node, the relay and the page when you run ``colcon build``