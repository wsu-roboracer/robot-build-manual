.. _doc_appendix_a:

Appendix A: Shared Folders between Host and VM
==============================================

If you don’t have a host computer running Ubuntu, you may do most of the above using a Virtual Machine (VM). If so, it is useful to set up a shared folder between the host (your default OS on your laptop) and the guest (Ubuntu running in the VM).

The following steps are for an Ubuntu 16.04 guest on VirtualBox, with the host a Mac OS X El Capitan (other Mac OSes should work too).

We assume you have already installed VirtualBox on your host, and installed Ubuntu 16.04 on it. More detailed instructions exist online, this is one way of doing it.

#. On your host, create the folder you wish to share. We’ll call it sfVM and assume it lives at ``~/sfVM``.
#. Start VirtualBox. Make sure the VM is not on (shut it down if it is).
#. Select the Ubuntu VM.
#. Click *Settings* -> *Shared Folders* -> click the ‘+’ sign -> browse to sfVM, which you created above, and check **Auto-mount** and **Make permanent**.
#. Start the VM.
#. Install the Guest Additions: in the VirtualBox menu, click *Devices* -> *Install Guest Additions* -> ... -> *Run Software*.
#. Mount the shared folder manually by running:

   .. code:: bash

      $ mkdir ~/guest_sfVM  # or whatever you want to call it
      $ id
      uid=1000(houssam) gid=1000(houssam)
      $ sudo mount -t vboxsf -o uid=1000,gid=1000 sfVM ~/guest_sfVM

#. To check that this was successful, put a file in the shared folder ``~/sfVM`` on your host. Then in your guest, you should see that file appear in ``~/guest_sfVM``.