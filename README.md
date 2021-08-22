# ESXi VMControl for Boofuzz
Uses vim-cmd that is shipped with ESXi to control VMs and snapshots

## Why
I wanted to use Boofuzz on my ESXi but the VMControl that comes with Boofuzz only supported VMWare and VirtualBox on Windows. I ported it for use on ESXi.

## Usage

    USAGE: vmcontrol.py
    <-x|--vm_id ID> path to VMX to control or name of VirtualBox image
    <-s|--snap_id ID>    path to vmrun.exe or VBoxManage
    [-l|--log_level LEVEL]   log level (default 1), increase for more verbosity
    [--port PORT]            TCP port to bind this agent to

1. Open port 26003 (or any of your choosing) for vmcontrol's pedrpc
2. Enable SSH on ESXi
3. SCP the files over to ESXi
4. Run vmcontrol (For vm id of 20, snap shot id of 1, on port 26003)

    python vmcontrol.py --vm_id 20 --snap_id 1 --port 26003

