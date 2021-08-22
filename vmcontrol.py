#!/usr/bin/python
#!c:\\python\\python.exe  # noqa: E265
from __future__ import print_function

import getopt
import os
import sys
import time

import pedrpc

PORT = 26003


def err(msg):
    return sys.stderr.write("ERR> " + msg + "\n") or sys.exit(1)


USAGE = (
    "USAGE: vmcontrol.py"
    "\n    <-x|--vm_id ID> path to VMX to control or name of VirtualBox image"
    "\n    <-s|--snap_id ID>    path to vmrun.exe or VBoxManage"
    "\n    [-l|--log_level LEVEL]   log level (default 1), increase for more verbosity"
    "\n    [--port PORT]            TCP port to bind this agent to"
)

class ESXiControlPedrpcServer(pedrpc.Server):
    def __init__(self, host, port, vm_id, snap_id, log_level=1):
        """
        @type  host:         str
        @param host:         Hostname or IP address to bind server to
        @type  port:         int
        @param port:         Port to bind server to
        @type  vm_id:        int
        @param vm_id:        Id of virtual machine
        @type  snap_id:      int
        @param snap_id:      Id of snapshot
        @type  log_level:    int
        @param log_level:    (Optional, def=1) Log output level, increase for more verbosity
        """

        # initialize the PED-RPC server.
        pedrpc.Server.__init__(self, host, port)

        self.host = host
        self.port = port

        self.vm_id = vm_id
        self.snap_id = snap_id

        self.log_level = log_level

        self.log("VMControl PED-RPC server initialized:")
        self.log("\t vm id: %d" % self.vm_id)
        self.log("\t snap id: %d" % self.snap_id)
        self.log("\t log level: %d" % self.log_level)
        self.log("Awaiting requests...")

    # noinspection PyMethodMayBeStatic
    def alive(self):
        """
        Returns True. Useful for PED-RPC clients who want to see if the PED-RPC connection is still alive.
        """
        return True

    def log(self, msg="", level=1):
        """
        If the supplied message falls under the current log level, print the specified message to screen.

        @type  msg: str
        @param msg: Message to log
        """

        if self.log_level >= level:
            print("[%s] %s" % (time.strftime("%I:%M.%S"), msg))

    def vmcommand(self, command):
        """
        Execute the specified command, keep trying in the event of a failure.

        @type  command: str
        @param command: VMRun command to execute
        """
        out = None

        while 1:
            self.log("executing: %s" % command, 5)

            pipe = os.popen(command)
            out = pipe.readlines()

            try:
                pipe.close()
            except IOError:
                self.log("IOError trying to close pipe")

            if not out:
                break
            elif not out[0].lower().startswith("close failed"):
                break

            self.log("failed executing command '%s' (%s). will try again." % (command, out))
            time.sleep(1)

        return "".join(out)

    def delete_snapshot(self, snap_id=None):
        if not snap_id:
            snap_id = self.snap_id

        self.log("deleting snapshot: %d" % snap_id, 2)

        command = "vim-cmd vmsvc/snapshot.remove " + str(self.vmx) + " " + str(snap_id) + " 0"
        return self.vmcommand(command)

    def list(self):
        self.log("listing running images", 2)
        
        command = "vim-cmd vmsvc/getallvms"
        return self.vmcommand(command)

    def list_snapshots(self):
        self.log("listing snapshots", 2)

        command = "vim-cmd vmsvc/snapshot.get " + str(self.vm_id)
        return self.vmcommand(command)

    def reset(self):
        self.log("resetting image", 2)

        command = "vim-cmd vmsvc/power.reset " + str(self.vm_id)
        return self.vmcommand(command)

    def revert_to_snapshot(self, snap_id=None):
        if not snap_id:
            snap_id = self.snap_id

        self.log("reverting to snapshot: %d" % snap_id, 2)

        command = "vim-cmd vmsvc/snapshot.revert " + str(self.vm_id) + " " + str(snap_id) + " 0"
        return self.vmcommand(command)

    def snapshot(self, snap_name):
        self.log("taking snapshot: %s" % snap_name, 2)

        command = "vim-cmd vmsvc/snapshot.create " + str(self.vm_id) + " '" + snap_name + "' Description 1"
        return self.vmcommand(command)

    def start(self):
        self.log("starting image", 2)

        command = "vim-cmd vmsvc/power.on " + str(self.vm_id)
        return self.vmcommand(command)

    def stop(self):
        self.log("stopping image", 2)

        command = "vim-cmd vmsvc/power.shutdown " + str(self.vm_id)
        return self.vmcommand(command)

    def suspend(self):
        self.log("suspending image", 2)

        command = "vim-cmd vmsvc/power.suspend " + str(self.vm_id)
        return self.vmcommand(command)

    def restart_target(self):
        self.log("restarting virtual machine...")

        # revert to the specified snapshot and start the image.
        self.revert_to_snapshot()
        
        #automatically started with revert
        #self.start()

        # wait for the snapshot to come alive.
        self.wait()

    def is_target_running(self):
        # sometimes vmrun reports that the VM is up while it's still reverting.
        # TODO: Possibly check by having agent on VM ping out?
        time.sleep(10)
        return True

    def wait(self):
        self.log("waiting for vm to come up: %d" % self.vm_id)
        while 1:
            if self.is_target_running():
                break


if __name__ == "__main__":
    opts = None

    vm_id_arg = None
    snap_id_arg = None
    log_level_arg = 1
    port_arg = None

    # parse command line options.
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "x:s:l", ["vm_id=", "snap_id=", "log_level=", "port="]
        )
    except getopt.GetoptError:
        err(USAGE)

    for opt, arg in opts:
        if opt in ("-x", "--vm_id"):
            vm_id_arg = int(arg)
        if opt in ("-s", "--snap_id"):
            snap_id_arg = int(arg)
        if opt in ("-l", "--log_level"):
            log_level_arg = int(arg)
        if opt in ("-p", "--port"):
            port_arg = int(arg)

    if (not vm_id_arg or not snap_id_arg):
        err(USAGE)

    servlet = ESXiControlPedrpcServer(
        "0.0.0.0", port_arg, vm_id_arg, snap_id_arg, log_level_arg
    )

    servlet.serve_forever()