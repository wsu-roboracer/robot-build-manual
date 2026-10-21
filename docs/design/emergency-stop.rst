=====================================
Emergency Stop (E-STOP)
=====================================

The red **🛑 E-STOP** button in the dashboard's top bar stops the car **for
everyone**: whoever or whatever is driving it, the car stops and stays stopped
until someone presses **Release**.

This page explains why the button exists, what it does on the robot, and what
it can't do. For the rest of the drive controls, see
:doc:`dashboard-drive-control`.

.. _estop-why:

Why we need it
==============

The Drive tab already has a **STOP** button, but that one only stops *this
page*. It disarms the web controller and sends a short burst of zero-speed
commands. It can't stop anyone else.

The car takes driving commands from three places, and ``ackermann_mux`` picks
which one wins:

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Input
     - Priority in the mux
   * - Physical PS4 controller (deadman L1 held)
     - **Highest**
   * - Dashboard web controller (``/drive``)
     - Lower
   * - Autonomous code
     - Lower

The physical controller has priority, so if someone is driving with it,
**nothing the web page publishes can stop the car**. The same goes for
autonomous code that keeps sending commands. Before E-STOP, the only ways to
stop the car in that situation were to shout at whoever held the controller or
to reach for the power switch.

E-STOP fixes that. Anyone watching the dashboard, on any tab and on a phone,
can stop the car no matter who is driving it.

.. _estop-how-it-works:

How it works
============

The key idea: one node every command passes through
---------------------------------------------------

Every input, whether controller, web or autonomous, reaches the motor through
**one node**: ``ackermann_to_vesc_node``. It turns the mux output into
``/commands/motor/*`` messages for the VESC motor controller.

.. code-block:: text

    PS4 controller ─┐
    Web dashboard  ─┼─► ackermann_mux ─► ackermann_to_vesc_node ─► /commands/motor/* ─► VESC ─► motor
    Autonomous     ─┘                         ▲
                                              │  E-STOP freezes this node (SIGSTOP)
                                              │
                        system_diagnostics.py ┴─► publishes /commands/motor/speed = 0 at 50 Hz

If that one node is frozen, **all** inputs are cut at once, so it doesn't
matter which one is in control.

Pressing E-STOP
---------------

1. **The page stops itself first.** If this dashboard is driving, it disarms
   right away without waiting for the robot.
2. **The page calls the robot.** It calls the ROS service
   ``/system_diagnostics/emergency_stop`` (``std_srvs/Trigger``) on
   ``system_diagnostics.py``.
3. **The robot freezes the drive node.** ``system_diagnostics.py`` finds
   ``ackermann_to_vesc_node`` with ``pgrep`` and sends it ``SIGSTOP``. The
   process is paused, not killed, so it can be resumed later.
4. **The robot holds the motor at zero.** ``system_diagnostics.py`` publishes
   speed ``0`` on ``/commands/motor/speed`` **50 times a second**. This makes
   the VESC actively brake to a stop, and because it keeps getting a command,
   it never falls back on its own firmware timeout.
5. **Every dashboard sees it.** The robot reports ``system: E-stop`` =
   **ERROR** on ``/diagnostics``. Every open dashboard, not just the one that
   pressed the button, shows a red banner on every tab. The *Who's driving*
   card says **Emergency stop is on**, and arming the web controller is
   refused.

There is **no confirmation** when you press E-STOP. It is for emergencies, so
it acts on the first click.

.. note::

   **Why speed 0 and not a brake command?** The controller's own release path
   already sends speed 0, so that path is known to work. Brake current has
   different units (A vs mA) in different ``vesc_driver`` versions, and a wrong
   guess would be 1000× off.

Releasing E-STOP
----------------

The **Release e-stop** button sits in the red banner. Releasing is deliberately
harder than stopping:

- **It asks for confirmation:** "Make sure the area is clear and nobody is
  about to drive."
- **It is refused while someone holds a deadman on the controller** (L1 for
  manual driving or R1 for autonomous). The button reads *Release (controller
  in use)* and is disabled. Otherwise the car would resume straight into a live
  command. The page reads L1 (``buttons[4]``) and R1 (``buttons[5]``) straight
  from ``/joy``. It does not use the mux's "unmasked" flag, because that flag
  is on whenever a controller is connected, even if nobody is touching it.
- On release, the page calls ``/system_diagnostics/emergency_release``. The
  robot sends ``SIGCONT`` to the frozen node, stops the zero-speed hold, and
  reports ``system: E-stop`` = OK. The banner then disappears from every
  dashboard.

.. _estop-fail-safe:

Fail-safe behaviour
===================

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Situation
     - What happens
   * - ``system_diagnostics.py`` exits or crashes while E-STOP is on
     - The drive node **stays frozen** (fail safe). The script prints the
       exact ``kill -CONT <pid>`` command to resume it. Restarting bringup also
       works.
   * - ``ackermann_to_vesc_node`` can't be found or frozen
     - E-STOP still turns on and holds speed 0 at 50 Hz. The banner says
       *"holding speed 0 only, the controller may still fight it"*.
   * - Robot unreachable (no rosbridge connection)
     - The page says *"could not reach the robot"* and tells you to use the
       controller or the power switch.
   * - Robot runs an older ``system_diagnostics.py`` without the service
     - The page says E-STOP isn't available on this robot and points to the
       controller or the power switch.
   * - ``pgrep`` matches ``system_diagnostics.py`` itself
     - Never freezes itself. ``parse_pgrep`` filters out its own PID, and a
       self-test covers this.

.. _estop-limitations:

Limitations
===========

- **It is not a hardware kill switch.** E-STOP needs a working network
  connection to the robot (rosbridge on port 9090) and a running
  ``system_diagnostics.py``. If either is down, use the controller or the car's
  **power switch**.
- **Anything that publishes** ``/commands/motor/*`` **directly**, bypassing
  ``ackermann_to_vesc_node``, is not stopped by the freeze. The 50 Hz zero hold
  still competes with it but may not win.
- **No authentication.** Anyone who can reach rosbridge can press E-STOP or
  Release, the same as any other command on the dashboard.

.. _estop-testing:

Testing it
==========

Do this **on a stand with the wheels off the ground**, with a second person
present:

1. Hold L1 and drive the wheels with the PS4 controller.
2. Press **E-STOP** on the dashboard. The wheels should stop at once and **stay
   stopped while you keep holding L1**.
3. Check that the red banner appears on every open dashboard and that the
   *Release* button is disabled while L1 is held.
4. Let go of L1, press **Release**, confirm, and check that the controller
   drives again.

This is also step 6 of the first-drive checklist in
:ref:`drive-control-before-first-drive`.

.. _estop-code:

Where the code lives
====================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - What it does
   * - ``prototype/js/estop.js``
     - The button and banner. Calls ``emergency_stop`` / ``emergency_release``
       and reads ``system: E-stop`` from ``/diagnostics``
   * - ``prototype/system_diagnostics.py``
     - The robot side: ``emergency_stop``, ``emergency_release``, the 50 Hz
       ``estop_hold``, ``estop_status``, ``parse_pgrep``
   * - ``prototype/dashboard.html``
     - The ``estopBtn`` button in the top bar and the ``estopBar`` banner
   * - ``prototype/js/drive.js``
     - Disarms the web controller and refuses to arm while E-STOP is on, and
       shows it in *Who's driving*
   * - ``prototype/css/topbar.css``
     - Styling: section 2, "Emergency stop button and banner", including
       keeping the button visible on phones