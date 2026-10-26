==========================================
Subsystem Inventory and Health Definitions
==========================================

Track 2 — robot-diagnostics. Closes the work described in issue #1.

.. note::

   **Status.** The hardware list below has been **confirmed against the robots
   in the lab**. What remains open is software configuration — publish rates,
   timeouts, watchdogs — and it is collected under
   :ref:`subsystem-open-questions`. Every threshold tagged **[MEASURE]** is
   still a placeholder until a real baseline is captured from a healthy robot.

.. _subsystem-why:

Why this document exists
========================

You cannot report status until you have written down what good looks like.
Every later piece of this track depends on this list:

- **#8 (health status schema)** needs the subsystem IDs and state names defined
  here.
- **#2 (spike: reading live status from ROS)** needs to know which topics and
  fields to go looking for.
- **#3 (ADR: web app vs status server vs physical indicator)** needs to know how
  many things there are to display and how fast they change.
- **#4 (mock up the interface)** needs something concrete to put on the screen.

If a definition below is wrong, that is fine and expected — but fix it *here*,
because three other issues read from this file.

.. _subsystem-three-states:

The three states
================

States are defined by **observable signal, not root cause**. "The lidar cable
is loose" is a cause; "no ``/scan`` message for 2 seconds" is a state. The
interface can only ever see the second one.

.. list-table::
   :header-rows: 1
   :widths: 14 46 40

   * - State
     - Meaning
     - What the driver should do
   * - **Healthy**
     - Producing correct data at the expected rate, within expected bounds.
     - Drive.
   * - **Degraded**
     - Still usable, but something is wrong that will get worse, or that
       quietly makes the robot behave badly.
     - Keep driving, but know about it. Fix before the next session.
   * - **Failed**
     - Not producing usable data, or unsafe.
     - Do not drive.

**Degraded is the state this whole track exists for.** Healthy and Failed are
already obvious to anyone standing next to the robot — it either drives or it
does not. Degraded is the one that currently costs an hour of lab time to
discover: the battery that is nearly flat, the camera that quietly enumerated
at USB 2.0, the disk that filled up with rosbags, the particle filter that has
silently lost the map. Those are the states worth an interface.

**Rule for every definition below:** it must be decidable by a program from
something it can read — a topic, a message field, a device node, a file, an
exit code. If we cannot write the check, the definition is not finished yet.

.. _subsystem-check-patterns:

Two check patterns cover most of this
=====================================

Nearly every subsystem is checked by one or both of:

1. **Liveness / rate.** Is the topic publishing, and at what Hz against its
   expected rate? Degraded is usually "publishing, but slower than it should"
   or "last message is stale by more than N seconds". This catches most sensor
   and node failures.
2. **Value in range.** Is a numeric field inside expected bounds — voltage,
   temperature, free bytes, particle spread?

Where a subsystem needs something other than these two, it says so explicitly.

A general staleness rule, applied unless overridden: **Degraded** at more than
2x the expected message period without a message; **Failed** at more than 2
seconds. **[MEASURE]**

.. _subsystem-summary:

Subsystem summary
=================

.. list-table::
   :header-rows: 1
   :widths: 8 28 14 10 40

   * - ID
     - Subsystem
     - Group
     - Priority
     - Primary check source
   * - S-01
     - Drive battery (LiPo)
     - Power
     - **1**
     - ``/sensors/core`` → ``state.voltage_input``
   * - S-02
     - Compute power rail
     - Power
     - 2
     - Orin undervoltage / throttle flags
   * - S-03
     - Emergency stop (controller deadman)
     - Power
     - **1**
     - ``/joy`` L1/R1 deadman + link health
   * - S-04
     - Orin CPU / GPU load
     - Compute
     - **1**
     - ``/proc/loadavg``, ``tegrastats``
   * - S-05
     - Orin thermals
     - Compute
     - **1**
     - ``/sys/devices/virtual/thermal/thermal_zone*/temp``
   * - S-06
     - Storage
     - Compute
     - 2
     - ``statvfs`` on ``/`` and the bag directory
   * - S-07
     - Memory
     - Compute
     - 2
     - ``/proc/meminfo``
   * - S-08
     - Clock sync
     - Compute
     - 2
     - ``timedatectl`` / ``chronyc tracking``
   * - S-09
     - VESC link
     - Drivetrain
     - 2
     - ``/sensors/core`` liveness
   * - S-10
     - Brushless motor
     - Drivetrain
     - **1**
     - ``/sensors/core`` → current, ERPM, temperature
   * - S-11
     - Steering servo
     - Drivetrain
     - **1**
     - Command vs. observed yaw rate
   * - S-12
     - LiDAR
     - Sensors
     - **1**
     - ``/scan`` rate + content
   * - S-13
     - IMU
     - Sensors
     - 2
     - ``/sensors/imu`` rate + bias
   * - S-14
     - Depth camera
     - Sensors
     - **1**
     - ``/camera/...`` rate + USB link speed
   * - S-15
     - Wheel odometry
     - Sensors
     - 2
     - ``/odom`` vs. commanded speed
   * - S-17
     - LiDAR Ethernet link
     - Connectivity
     - **1**
     - Interface carrier + ping
   * - S-18
     - Gamepad (PS4 controller)
     - Connectivity
     - **1**
     - ``/joy`` liveness, BT link, controller battery
   * - S-19
     - ROS 2 node set
     - Software
     - **1**
     - Expected-node roll call
   * - S-20
     - TF tree
     - Software
     - 2
     - Transform lookup + age
   * - S-21
     - Localization
     - Software
     - 2
     - Particle spread, pose jumps
   * - S-22
     - Command mux
     - Software
     - 2
     - ``/drive`` output vs. inputs
   * - S-23
     - Drive command freshness
     - Software
     - 2
     - ``/drive`` staleness

S-16 (WiFi / SSH reachability) was dropped — see the note under cross-cutting
finding 3. IDs are not renumbered when something is dropped, because three
other issues reference them.

.. _subsystem-build-priority:

Build priority
==============

Twenty-two subsystems is not a first release. **Tier 1** is what the interface
has to show to be worth opening at all; **tier 2** is worth having and should
shape the schema in #8 but not the first build.

**Tier 1 (11):** S-01 drive battery · S-03 deadman · S-04 CPU/GPU load · S-05
thermals · S-10 brushless motor · S-11 steering servo · S-12 LiDAR · S-14 depth
camera · S-17 LiDAR Ethernet · S-18 gamepad · S-19 ROS 2 node set

**Tier 2 (11):** S-02 compute rail · S-06 storage · S-07 memory · S-08 clock
sync · S-09 VESC link · S-13 IMU · S-15 wheel odometry · S-20 TF tree · S-21
localization · S-22 command mux · S-23 drive command freshness

**Three tier-2 items are pulled in by tier 1 regardless.** In each case the
underlying *check* is needed even though the *display* can wait, which is a
distinction #8's schema should be able to express:

- **S-09 (VESC link)** is the shared dependency of S-01 and S-10, both tier 1.
  If the VESC drops, both fail in the same instant, and without S-09 the
  interface shows two unrelated red lights instead of one cause. The check
  itself is a single topic-rate test that S-01 and S-10 already have to
  perform.
- **S-13 (IMU) or S-15 (wheel odometry)** is required by S-11. The steering
  check has no position feedback to read, so it infers servo health by
  comparing the command against yaw rate — which has to come from one of those
  two. Pick one to read as part of building S-11.
- **S-23 (drive command freshness)** is the e-stop's backstop. Its threshold is
  the stale-command watchdog timeout, already the highest-priority open
  question in this document. Answering that question is tier 1 work even if the
  readout is not.

Tier 1 also happens to cover the three failures this track was started for: the
flat pack (S-01), the camera silently at USB 2.0 (S-14), and the stack that did
not fully come up (S-19).

.. _subsystem-power:

1. Power
========

S-01 — Drive battery (LiPo)
---------------------------

3S LiPo, 11.1 V nominal. Confirmed. Powers the motor and, through a regulator,
the compute.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Pack voltage at or above 11.1 V under load (3.7 V/cell).
   * - Degraded
     - 10.5–11.1 V. Still drives, but performance is falling off and the pack
       should be swapped soon.
   * - Failed
     - Below 10.5 V (3.5 V/cell). Stop driving. Below roughly 9.9 V a LiPo
       takes permanent damage. **[MEASURE — confirm the cutoff configured on
       our VESCs]**

**Check:** subscribe to ``/sensors/core`` (``vesc_msgs/VescStateStamped``), read
``state.voltage_input``. Available at ~50 Hz with no extra hardware. Apply a
rolling median over ~1 s — instantaneous voltage sags hard under acceleration
and will produce false alarms if read raw.

**Note.** This is almost certainly the single highest-value signal in the whole
system. A flat pack presents as "the robot is behaving strangely", and it
should be the first thing visible on any interface we build.

S-02 — Compute power rail
-------------------------

The Orin is fed from the same pack through a regulator/UBEC. Confirmed — there
is no separate compute battery.

**That couples S-01 and S-02.** A pack flat enough to sag hard under load takes
the Orin down with it, which means the diagnostics stack dies at precisely the
moment it would be most useful. It is a further argument for S-01 being the
headline number on any interface, and for #9's physical indicator having its
own power source if that is practical.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - No undervoltage or throttling flags set.
   * - Degraded
     - Soft throttling reported, or input voltage below the regulator's rated
       minimum.
   * - Failed
     - Compute browns out and reboots mid-run.

**Check:** Jetson throttle/undervoltage flags via ``tegrastats`` or the sysfs
power nodes. A brownout is detectable after the fact from uptime resetting — if
``/proc/uptime`` is smaller than it was on the previous poll, the compute
rebooted. Worth surfacing loudly, because an unexplained mid-run reboot is
otherwise very hard to diagnose.

S-03 — Emergency stop (controller deadman)
------------------------------------------

There is no inline kill switch. The e-stop is the **deadman trigger on the PS4
controller** — teleop only forwards drive commands while the trigger is held,
and releasing it stops the robot. That is a *software* deadman carried over a
*wireless* link, which changes what this check has to do.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/joy`` live, deadman buttons readable, and their state agrees with
       whether the robot is being commanded.
   * - Degraded
     - ``/joy`` intermittent, or controller battery low. The deadman may
       release on its own — or, worse, fail to release.
   * - Failed
     - No ``/joy``. There is no working e-stop at all, whatever the robot is
       currently doing.

**Check:** read the deadman buttons straight out of ``/joy``, together with
``/joy`` liveness (S-18). There are **two**: **L1 is the manual-drive deadman,
R1 is the autonomous deadman.** The operator holds L1 to drive by hand and R1
to hand control to the stack. Read the exact button indices off the
``joy_teleop`` config rather than hardcoding them — the usual DS4 mapping under
``joydev`` puts L1 at ``buttons[4]`` and R1 at ``buttons[5]``, but that belongs
in the same config file as the expected-node list (S-19), not in the checker.

Unlike the wired kill switch this document originally assumed, the deadman is
directly observable in software, so no inference from motor current is needed.
And because L1 and R1 are distinct, the interface can show **three** states
rather than two: nothing held (stopped), manual, or autonomous. Which button is
held is the operator's *intended* mode, and that turns out to be exactly what
S-22 has been missing.

**The failure direction is the thing to get right.** A physical kill switch
fails safe: cut the wire, the motor stops. A software deadman over a wireless
link fails **open** — if ``/joy`` goes silent while the trigger is held, the
release never reaches the robot, and it keeps the last command it was given
until something else times out. So the real question for this subsystem is not
"can we read the trigger" but **"what stops the robot when the link drops"**,
and the answer lives elsewhere:

- whatever stale-input timeout the teleop node and ``ackermann_mux`` apply
  (S-23) **[CONFIRM]**,
- and the VESC's own command timeout, which cuts the motor if no command
  arrives for roughly a second **[CONFIRM — the value actually configured on
  our VESCs]**.

Those two *are* the e-stop. They should be measured rather than assumed: put
the robot on blocks, kill the controller mid-command, and time how long the
wheels keep turning. That number is worth knowing and worth displaying.

This also redirects #9 (physical indicator spike). There is no kill-switch
wiring to add a readback to, so the indicator's job here is to show deadman
state and link health — which, on a robot whose only stop is wireless, is a
stronger case for a physical indicator than the original framing was, not a
weaker one.

.. _subsystem-compute:

2. Compute
==========

S-04 — Orin CPU / GPU load
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - 1-minute load average below the core count; no ROS callback starvation.
   * - Degraded
     - Load average above core count, or any node publishing below ~80% of its
       expected rate while its inputs are fine.
   * - Failed
     - System unresponsive to SSH within a timeout.

**Check:** ``/proc/loadavg`` plus the per-node rate checks already being done
for S-19. Load average alone is a weak signal; **load average plus a topic that
has slowed down** is a strong one. Report the pair, not the number on its own.

S-05 — Orin thermals
--------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Junction temperature below 70 °C. **[MEASURE]**
   * - Degraded
     - 70–85 °C, or the fan is not spinning while temperature climbs. Clock
       throttling begins here and presents as everything getting slightly
       slower at once.
   * - Failed
     - Above roughly 90 °C, or thermal shutdown.

**Check:** read ``/sys/devices/virtual/thermal/thermal_zone*/temp``
(millidegrees C), or parse ``tegrastats``. Thresholds must be baselined against
a real robot after a 20-minute run — the numbers above are Orin-family
defaults, not measurements from our hardware.

S-06 — Storage
--------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - More than 20% free on ``/`` and on the bag partition.
   * - Degraded
     - 5–20% free. Recording will fail soon.
   * - Failed
     - Below 5% free, or the filesystem has gone read-only.

**Check:** ``statvfs`` on ``/`` and on the rosbag output directory. **This one
is not theoretical** — rosbag recording at full lidar and camera rate fills a
disk in a surprisingly small number of minutes, and the failure mode is a
half-written bag plus a robot that starts behaving oddly for unrelated-looking
reasons. If the interface shows one number here, "minutes of recording left at
current rate" is more useful than "GB free".

S-07 — Memory
-------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - More than 25% available.
   * - Degraded
     - 10–25% available, or swap in active use.
   * - Failed
     - OOM killer has fired — a node dies with no error of its own.

**Check:** ``/proc/meminfo`` (``MemAvailable``, ``SwapFree``), plus a scan of
the kernel log for ``Out of memory``. The OOM case is worth calling out
explicitly, because from the user's side it looks exactly like "the node
crashed for no reason".

S-08 — Clock sync
-----------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Offset from reference below 50 ms.
   * - Degraded
     - 50 ms to 1 s offset, or no sync source reachable but drift still small.
   * - Failed
     - Offset above 1 s, or the clock jumped backwards.

**Check:** ``timedatectl show`` / ``chronyc tracking``. This matters more than
it looks: ROS 2 message timestamps drive the TF tree and every staleness check
in this document. A robot with a bad clock reports *everything* as stale, so
this check should be evaluated first, and if it fails the interface should say
so rather than lighting up twenty other alarms.

.. _subsystem-drivetrain:

3. Drivetrain
=============

S-09 — VESC link
----------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/sensors/core`` publishing at its configured rate (~50 Hz
       **[CONFIRM]**).
   * - Degraded
     - Publishing below 80% of expected rate, or intermittent gaps — usually a
       marginal USB connection.
   * - Failed
     - No ``/sensors/core`` for more than 2 s, or the serial device has
       disappeared from ``/dev``.

**Check:** topic rate on ``/sensors/core``, plus existence of the VESC serial
device node. Losing the VESC takes S-01, S-10 and S-15 with it, so the
interface should show it as the *cause* rather than as four simultaneous
unrelated failures. Dependency handling like this is worth building into the
schema in #8.

S-10 — Brushless motor
----------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Current draw and ERPM track the commanded speed.
   * - Degraded
     - Sustained current above the continuous rating, or controller
       temperature elevated — a dragging drivetrain or a binding wheel shows up
       here first.
   * - Failed
     - Commanded non-zero speed with ERPM at approximately zero (stalled,
       disconnected, or e-stopped), or a VESC fault code set.

**Check:** ``/sensors/core`` → ``state.current_motor``, ``state.speed`` (ERPM),
``state.temperature_pcb``, and the fault field, compared against
``/commands/motor/speed``. Thresholds **[MEASURE]** — capture a baseline of
normal current draw on a healthy robot on the actual track surface, since
carpet and tile differ noticeably.

S-11 — Steering servo
---------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Commanded steering angle produces the expected yaw rate.
   * - Degraded
     - Consistent offset between commanded and observed yaw rate — the classic
       "it drifts to one side" complaint, usually servo trim or a linkage
       issue.
   * - Failed
     - No yaw response to a steering command while the robot is moving.

**Check:** harder than the others, because the servo has **no position
feedback**. Confirmed — so it has to be inferred: compare
``/commands/servo/position`` against the yaw rate reported by the IMU (S-13) or
by ``/odom`` (S-15), while the robot is moving above some minimum speed. This
only works during motion, so the check must report ``unknown`` rather than
``healthy`` when the robot is stationary.

**This forces a fourth state.** S-11 is the first subsystem that needs
``unknown``, and it is not the last — several checks are only meaningful while
driving. Recommend #8 define ``unknown`` alongside healthy/degraded/failed
rather than lying about a check that could not run. Showing grey is honest;
showing green is not.

.. _subsystem-sensors:

4. Sensors
==========

S-12 — LiDAR
------------

Hokuyo UST-10LX over Ethernet. Confirmed.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/scan`` at ~40 Hz (the UST-10LX scan period is 25 ms), with a
       plausible fraction of finite range returns.
   * - Degraded
     - Rate below 80% of expected, an unusually high proportion of ``inf``/NaN
       returns, or a fixed angular sector permanently blocked — something
       bolted in front of the sensor, or a dirty window.
   * - Failed
     - No ``/scan`` for more than 2 s, or every return invalid.

**Check:** rate on ``/scan``, plus content analysis of the ``ranges`` array —
fraction finite, and a persistent-blocked-sector test comparing sectors over a
rolling window. The blocked sector case is worth the extra work: it is
invisible in RViz at a glance, it wrecks both localization and gap-following,
and students lose real time to it.

S-13 — IMU
----------

VESC 6 onboard IMU. Confirmed.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/sensors/imu`` publishing at expected rate; gyro bias near zero when
       stationary.
   * - Degraded
     - Gyro bias drifting beyond threshold when stationary, or accelerometer
       magnitude not near 1 g at rest — needs recalibration.
   * - Failed
     - No messages, or all-zero / NaN values.

**Check:** rate, plus a stationary-bias test. The stationary test is only valid
when the robot actually is stationary, which can be established from ``/odom``
— another ``unknown`` case.

S-14 — Depth camera
-------------------

Intel RealSense D435i. Confirmed.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Color and depth streams at configured rate, device enumerated at USB
       3.0.
   * - Degraded
     - **Enumerated at USB 2.0** — the stream still works, at a fraction of the
       frame rate, and nothing announces it. Also: frame rate below configured,
       or a large fraction of invalid depth pixels.
   * - Failed
     - Device absent from the USB tree, or no frames for more than 2 s.

**Check:** topic rates on the camera topics, plus USB link speed from sysfs
(``/sys/bus/usb/devices/*/speed``) or ``lsusb -t``. **The USB 2.0 case is
exactly the kind of failure this track exists to catch** — a bad cable or the
wrong port silently halves your frame rate, and the only symptom is that vision
"feels slow". It should be a named, visible state, not something a student
rediscovers every semester.

S-15 — Wheel odometry
---------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/odom`` publishing; reported velocity tracks commanded velocity while
       driving.
   * - Degraded
     - Persistent scale error between commanded and reported speed — wheel
       slip, or a stale ERPM-to-velocity calibration.
   * - Failed
     - No ``/odom``, or velocity stuck at zero while the motor is visibly
       turning.

**Check:** rate on ``/odom``, and a rolling comparison of ``/odom``
``twist.linear.x`` against the commanded speed. Degraded here is a calibration
problem rather than a hardware fault, but it poisons localization, so it is
worth surfacing.

.. _subsystem-connectivity:

5. Connectivity
===============

S-17 — LiDAR Ethernet link
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Interface up, carrier detected, lidar answering at its configured IP.
   * - Degraded
     - Carrier present but packet loss elevated.
   * - Failed
     - No carrier, or no response from the lidar IP.

**Check:** ``/sys/class/net/<iface>/carrier`` and
``/sys/class/net/<iface>/operstate``, plus a ping to the lidar address.
**[CONFIRM — the lidar's configured IP; stock is 192.168.0.10]** This is what
distinguishes "the cable fell out" from "the lidar driver crashed", which S-12
alone cannot do.

S-18 — Gamepad (PS4 controller)
-------------------------------

Sony DualShock 4, paired over Bluetooth. Confirmed — no USB wireless adapter.
**This is safety-relevant hardware, not a convenience:** it carries the deadman
(S-03), so the controller's health *is* the e-stop's health.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/joy`` publishing at its steady rate; controller connected; controller
       battery above threshold.
   * - Degraded
     - Intermittent ``/joy``, controller charge low, or link quality falling —
       out of range, or a charge overdue.
   * - Failed
     - Controller not connected, or no ``/joy`` at all. No manual control and
       no deadman.

**Check:** ``/joy`` liveness, plus the input device node (``/dev/input/js*``)
and the Bluetooth connection state. The DS4 also reports its own charge level
to the kernel at ``/sys/class/power_supply/sony_controller_battery_*/capacity``
**[CONFIRM — exposed by the driver we use]**, and that one belongs on the
screen: a controller that dies mid-run takes the e-stop with it, and a
percentage prevents that outright. It is the cheapest safety-relevant number in
this document.

Note that a gamepad sitting untouched still publishes at a steady rate rather
than going silent, so absence of *messages* is the signal, not absence of
*button presses*.

.. _subsystem-software:

6. Software stack
=================

S-19 — ROS 2 node set
---------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Every node in the expected roll call is present, and each is publishing
       at its expected rate.
   * - Degraded
     - All nodes present, but one or more publishing below 80% of expected
       rate.
   * - Failed
     - A required node is absent.

**Check:** enumerate live nodes and compare against a checked-in expected-node
list, then rate-check each one's primary topic. **That expected-node list
should be a config file in this repo**, not hardcoded — it is the same list a
student needs when the stack does not come up, and it will change as the
platform changes.

Expected node set, confirmed against ``f1tenth_system`` as we actually run it:
``urg_node``, ``vesc_driver``, ``vesc_to_odom``, ``ackermann_to_vesc``,
``ackermann_mux``, ``joy``, ``joy_teleop``, ``robot_state_publisher``,
``particle_filter``, and the RealSense node.

S-20 — TF tree
--------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``map → odom → base_link → sensor frames`` all resolvable, transforms
       fresh.
   * - Degraded
     - A transform resolves but is stale beyond its expected period.
   * - Failed
     - A required transform cannot be looked up — the tree is disconnected.

**Check:** attempt a lookup for each required frame pair and check the
timestamp age of each. A broken TF tree is one of the most common and most
confusing failure modes in ROS, and today it presents as "RViz is empty and I
do not know why".

S-21 — Localization (particle filter)
-------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - Particle spread below threshold; pose continuous; scan matches the map.
   * - Degraded
     - Particle spread elevated — the filter is uncertain and about to lose the
       robot.
   * - Failed
     - Pose jumps discontinuously, spread exceeds threshold, or the filter is
       not publishing.

**Check:** subscribe to the particle filter's pose and particle topics; compute
spread (covariance trace, or particle standard deviation) and frame-to-frame
pose delta against a physically plausible maximum. Thresholds **[MEASURE]** —
they must be baselined from a run known to be good, and they are map-dependent.

**This is the one that most deserves a display.** A localization failure looks,
from the outside, like the robot has simply decided to drive into a wall.

S-22 — Command mux
------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``ackermann_mux`` publishing ``/drive``, and the selected input matches
       the intended mode (teleop vs. autonomous).
   * - Degraded
     - Mux publishing, but the active input is not the one the operator
       believes is active.
   * - Failed
     - No ``/drive`` output despite a live input.

**Check:** ``/drive`` liveness, plus a comparison of the mux output against each
candidate input to work out which source is actually winning. **Showing the
currently active control source is worth doing on its own merits** — "why is it
not responding to the controller" is usually this, and it is invisible today.

**The deadman buttons make this much cheaper than it looks.** S-03 gives the
operator's *intended* mode for free: L1 held means they want manual, R1 means
they want autonomous. Comparing that against which input the mux is actually
forwarding is precisely the Degraded row above, and it is a two-signal
comparison rather than the fiddly output-matching one. Intent from ``/joy``,
reality from the mux, and a mismatch between them is the bug.

S-23 — Drive command freshness
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - State
     - Definition
   * - Healthy
     - ``/drive`` messages arriving within the expected period.
   * - Degraded
     - Period exceeded but still below the safety timeout — control is getting
       choppy.
   * - Failed
     - Beyond the safety timeout; the robot should be coasting to a stop.

**Check:** staleness on ``/drive``. **[CONFIRM — is there a watchdog that stops
the robot on stale commands, and what is its timeout?]** If there is one, this
check should use the same threshold, so that the interface and the robot agree
on what "too old" means. If there is not one, that is a finding in itself and
probably its own issue.

**This is the e-stop's backstop.** Because the deadman (S-03) is a software
button on a wireless controller, the stale-command timeout is what actually
stops the robot when the link drops. That promotes this check from housekeeping
to safety-relevant, and makes the **[CONFIRM]** above the highest-priority open
question in this document.

.. _subsystem-cross-cutting:

Cross-cutting findings
======================

Three things fell out of writing this list that affect other issues:

1. ``unknown`` **is a required fourth state.** Several checks (S-11, S-13,
   parts of S-15) are only meaningful while the robot is moving. Reporting
   ``healthy`` for a check that could not run is a lie, and it is the specific
   kind of lie that destroys trust in a status display. Recommend #8 define
   ``unknown`` explicitly.

2. **Subsystems have dependencies, and the display should respect them.** The
   VESC link (S-09) failing takes out S-01, S-10 and S-15 at the same instant.
   Twenty red lights with one root cause is worse than one red light and three
   greyed-out dependents. The schema in #8 should carry a ``depends_on``
   relationship. The e-stop is the sharpest case: S-03 depends on S-18, which
   depends on the Bluetooth link, so a flat controller battery should read as
   one root cause rather than as "e-stop failed" plus "gamepad failed".

3. **A network-delivered interface cannot report its own network failing.** We
   are not checking the WiFi link as a subsystem — if you are looking at a web
   page served from the robot, the network is evidently up, and if you are not,
   no check we write will reach you. But the structural point survives dropping
   the check: the one status a web app cannot show you is its own transport
   being down, and the failure is silent — a stale page looks exactly like a
   healthy one. Whichever option #3 picks needs an answer for that, most likely
   a visible "last updated" age on the display so a frozen page reads as
   frozen.

4. **The e-stop is software, over a wireless link, and it fails open.** The
   robot's only stop is the controller deadman (S-03), so what actually halts
   the robot when the link drops is a timeout somewhere downstream — and we do
   not currently know whether that timeout exists or what it is set to.
   Establishing the real coast-down time after a controller loss is a half-hour
   bench measurement and should probably be its own issue. It is also a live
   input to #3 and #9: deadman state and controller-link health are the two
   indicators most worth showing, and they are exactly the ones a
   network-delivered display is worst placed to show.

.. _subsystem-open-questions:

Open questions
==============

Hardware is confirmed: 3S LiPo; compute fed from the drive pack through a
regulator; no inline kill switch, the PS4 L1/R1 deadman is the only stop;
Hokuyo UST-10LX; VESC onboard IMU; RealSense D435i; no steering-servo position
feedback; DS4 over Bluetooth; and the node roll call in S-19 matches how we
actually run ``f1tenth_system``.

What is left is configuration, and it is all software-side:

- [ ] **Is there a stale-command watchdog, and what is its timeout?** Highest
  priority — with no inline kill switch, this is the actual e-stop.
- [ ] The VESC's configured command timeout, and the measured coast-down time
  after the controller link is cut. Same reason.
- [ ] ``/sensors/core`` publish rate
- [ ] The lidar's configured IP (stock is 192.168.0.10)
- [ ] Whether the DS4 charge level is exposed under
  ``/sys/class/power_supply/``
- [ ] The ``joy_teleop`` button indices for L1 and R1, read off the config
  rather than assumed

The first two are one bench session with the robot on blocks, and they answer
the only safety-relevant unknown left in this document.

Everything tagged **[MEASURE]** needs a baseline captured from a known-good
robot before the threshold means anything. That baseline capture is arguably
its own issue — it needs hardware, a healthy robot, and a 20-minute run — and
it blocks every check that compares against a number.