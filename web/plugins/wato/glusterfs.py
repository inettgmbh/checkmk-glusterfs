#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

from cmk.gui.i18n import _
from cmk.gui.plugins.wato import (
    HostRulespec,
    rulespec_registry,
)
from cmk.gui.cee.plugins.wato.agent_bakery.rulespecs.utils import RulespecGroupMonitoringAgentsAgentPlugins
from cmk.gui.valuespec import (
    DropdownChoice,
)


def _valuespec_agent_config_glusterfs():
    return DropdownChoice(
        title=_("Inett glusterfs checks"),
        help=_("This will deploy the agent plugin <tt>glusterfs</tt> to add checks for some glusterfs metrics."),
        choices=[
            (True, _("Deploy plugin for glusterfs checks")),
            (None, _("Do not deploy plugin for glusterfs checks")),
        ]
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupMonitoringAgentsAgentPlugins,
        name="agent_config:glusterfs",
        valuespec=_valuespec_agent_config_glusterfs,
    ))
