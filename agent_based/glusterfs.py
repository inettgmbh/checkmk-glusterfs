#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .agent_based_api.v1 import *


def glusterfs_hostlabels(section):
    yield HostLabel('inett/glusterfs', 'server')


register.agent_section(
    name="glusterfs",
    host_label_function=glusterfs_hostlabels,
)


def glusterfs_peer_discovery(section):
    first = True
    gluster_found = False
    gluster_section = None
    for line in section:
        line = " ".join(line).split()
        if first:
            first = False
            gluster_found = line[0].startswith("0")
        elif gluster_found and gluster_section == "pool_list":
            if line[0].startswith("#"):
                gluster_section = None
            elif line == ['UUID', 'Hostname', 'State']:
                continue
            else:
                for i in range(len(line) - 1):
                    if i % 3 == 1:
                        yield Service(item=line[i])
        if gluster_found and gluster_section is None and line == ['#', 'gluster', 'pool', 'list']:
            gluster_section = "pool_list"


def glusterfs_peer_checks(item, section):
    pool_list_section = False
    peer_status_section = False
    peer_status_host_section = False
    pool_list_dropline = False
    ind = 0
    for line in section:
        line = " ".join(line).split()
        if pool_list_section:
            if line.__contains__(item):
                ind = line.index(item)
            if pool_list_section and line[0] == "#":
                pool_list_section = False
                peer_status_section = False
            if pool_list_dropline:
                pool_list_dropline = False
            elif line.__contains__(item):
                yield Result(
                    state=State.OK, summary=("UUID: %s" % line[ind - 1]),
                )
                yield Result(
                    state=State.OK, summary=("Hostname: %s" % line[ind]),
                )
                yield Result(
                    state=(
                        State.OK if line[ind + 1] == "Connected" else State.CRIT
                    ),
                    summary=("State: %s" % line[ind + 1]),
                )
        elif peer_status_section:
            if peer_status_section and peer_status_host_section:
                if line[0] == "State:":
                    stateline = ' '.join(line[1:])
                    state = stateline.split(" (")
                    if state[0] == "Peer in Cluster":
                        r_state = State.OK
                    elif state[0] == "Accepted Peer Request":
                        r_state = State.WARN
                    elif state[0] == "Peer Rejected":
                        r_state = State.CRIT
                    else:
                        r_state = State.UNKNOWN
                    yield Result(state=r_state, summary=state[0] + " (" + item + ")")
            if peer_status_host_section and ' '.join(line).strip() == '':
                peer_status_section = False
                peer_status_host_section = False
            elif line[0] == "Hostname:" and line[1] == item:
                peer_status_host_section = True
        if line == ['#', 'gluster', 'peer', 'status']:
            peer_status_section = True
        elif line == ['#', 'gluster', 'pool', 'list']:
            pool_list_section = True
            pool_list_dropline = True


register.check_plugin(
    name="glusterfs_peer",
    sections=["glusterfs"],
    service_name="GlusterFS peer %s",
    discovery_function=glusterfs_peer_discovery,
    check_function=glusterfs_peer_checks,
)


def glusterfs_volume_discovery(section):
    first = True
    gluster_found = False
    gluster_section = None
    skipFirst = True
    for line in section:
        line = " ".join(line).split()
        if first:
            first = False
            gluster_found = line[0].startswith("0")
        elif gluster_found and gluster_section == "volume_list":
            if line[0].startswith("#") and skipFirst is False:
                gluster_section = None
            elif skipFirst is True:
                skipFirst = False
            elif line[:2] == ["Volume", "Name:"]:
                yield Service(item=line[2])
        elif gluster_found and gluster_section is None and line == ['#', 'gluster', 'volume', 'list']:
            gluster_section = "volume_list"


def glusterfs_volume_checks(item, section):
    skip = 0
    volume_info_section = False
    volume_heal_info_section = False
    volume_heal_info_sbrain_section = False
    volume_rebalance_status_section = False
    brick = None
    total_h = 0
    total_sb = 0
    total_rebalance = [0, 0, 0, 0, 0]

    for line in section:
        line = " ".join(line).split()
        if line[0] == "#":
            volume_info_section = False
            volume_heal_info_section = False
            volume_heal_info_sbrain_section = False
            volume_rebalance_status_section = False
        elif skip > 0:
            skip = skip - 1
            continue
        elif volume_info_section:
            if len(line) >= 2:
                if line[0] == "Status:" and line[1] != "Started":
                    yield Result(state=State.UNKNOWN, summary=f"Status: {line[1]}")
                elif line[0] != "Volume Name:":
                    yield Result(state=State.OK, summary=" ".join(line))
        elif volume_heal_info_section:
            if len(line) == 0:
                continue
            if line[0] == "Brick":
                brick = line[1]
            elif line[0] == "Status:":
                v_line = ' '.join(line)
                if 'Connected' in v_line:
                    yield Result(state=State.OK, summary=brick + ": " + v_line)
                elif 'not Connected' in v_line:
                    yield Result(state=State.CRIT, summary=brick + ": " + v_line)
                else:
                    yield Result(state=State.UNKNOWN, summary=brick + ": " + v_line)
            elif ' '.join(line[:3]) == "Number of entries:":
                if line[3] != "-":
                    total_h += int(line[3])
                    if int(line[3]) > 10:
                        yield Result(state=State.WARN, summary=' '.join(line))
                    if int(line[3]) > 15:
                        yield Result(state=State.CRIT, summary=' '.join(line))
                else:
                    # yield Metric('needs_healing', -1, levels=(10, 15))
                    yield Result(state=State.UNKNOWN, summary=' '.join(line))
        elif volume_heal_info_sbrain_section:
            if line[0] == "Brick":
                brick = line[1]
            if ' '.join(line[:5]) == "Number of entries in split-brain:":
                if line[5] != "-":
                    total_sb += int(line[5])
                    if int(line[5]) > 1:
                        yield Result(
                            state=State.CRIT,
                            summary=('%s entries in split-brain state' % line[5]))
                else:
                    # yield Metric('split_brain', -1, levels=(1, 1))
                    yield Result(
                        state=State.UNKNOWN,
                        summary=('%s entries in split-brain state' % line[5]))
        elif volume_rebalance_status_section:
            if line[0] != "volume":
                if line[1] != "fix-layout":
                    total_rebalance[0] += int(line[1])
                    total_rebalance[1] += int(line[2].replace("Bytes", ""))
                    total_rebalance[2] += int(line[3])
                    total_rebalance[3] += int(line[4])
                    total_rebalance[4] += int(line[5])
                    yield Result(state=State.OK,
                                 summary='# Rebalanced Files for %s: %s' % (line[0], int(line[1])))
                    yield Result(state=State.OK,
                                 summary='size of Rebalanced Files for %s: %s' % (line[0], int(line[2].replace("Bytes", ""))))
                    yield Result(state=State.OK,
                                 summary='# Scanned Files for %s: %s' % (line[0], int(line[3])))
                    yield Result(state=State.OK,
                                 summary='# failures for %s: %s' % (line[0], int(line[4])))
                    yield Result(state=State.OK,
                                 summary='# skipped Files for %s: %s' % (line[0], int(line[5])))
                    time = line[7].split(":")
                    seconds = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])
                    yield Metric('%s_rebalance_time_in_seconds' % line[0], seconds)
                else:
                    time = line[3].split(":")
                    seconds = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])
                    yield Metric('%s_rebalance_time_in_seconds' % line[0], seconds)
                if line.__contains__("completed"):
                    yield Result(
                        state=State.OK,
                        summary=('rebalance of %s completed' % (line[0])),
                    )
                elif line.__contains__("in progress"):
                    yield Result(
                        state=State.OK,
                        summary=('rebalance of %s is in progress' % (line[0])),
                    )
                elif line.__contains__("stopped"):
                    yield Result(
                        state=State.WARN,
                        summary='rebalance of %s stopped' % line[0],
                    )
                else:
                    yield Result(
                        state=State.UNKNOWN,
                        summary='rebalance state of %s is unknown' % line[0],
                    )

        if not (volume_info_section
                or volume_heal_info_section
                or volume_heal_info_sbrain_section
                or volume_rebalance_status_section) \
                and line[0] == "#":
            if line == ['#', 'gluster', 'volume', 'info', '%s' % item]:
                volume_info_section = True
            elif line == ['#', 'gluster', 'volume', 'heal', '%s' % item, 'info']:
                volume_heal_info_section = True
            elif line == ['#', 'gluster', 'volume', 'heal', '%s' % item, 'info', 'split-brain']:
                volume_heal_info_sbrain_section = True
            elif line == ['#', 'gluster', 'volume', 'rebalance', '%s' % item, 'status']:
                volume_rebalance_status_section = True
                skip = 2
    yield Metric("total_num_unhealthy", total_h, levels=(10, 15))
    yield Metric("total_num_sb_error", total_sb, levels=(1, 1))
    yield Metric('rebalanced_files', total_rebalance[0])
    yield Metric('rebalance_size', total_rebalance[1])
    yield Metric('rebalance_scanned', total_rebalance[2])
    yield Metric('rebalance_failures', total_rebalance[3])
    yield Metric('rebalance_skipped', total_rebalance[4])

register.check_plugin(
    name="glusterfs_volume",
    sections=["glusterfs"],
    service_name="GlusterFS volume %s",
    discovery_function=glusterfs_volume_discovery,
    check_function=glusterfs_volume_checks,
)
