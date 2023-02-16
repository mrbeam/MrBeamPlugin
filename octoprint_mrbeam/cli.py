# coding=utf-8

import click
import sys
import json
import requests.exceptions
from octoprint.cli.client import create_client
from octoprint_mrbeam.mrbeam_events import MrBeamEvents
from octoprint_mrbeam.mrb_logger import mrb_logger

# this is for the command line interface we're providing
def get_cli_commands(cli_group, pass_octoprint_ctx, *args, **kwargs):
    _logger = mrb_logger("octoprint.plugins.mrbeam.cli")

    # # > octoprint plugins mrbeam:debug_event MrBeamDebugEvent -p 42
    # # remember to activate venv where MrBeamPlugin is installed in
    @click.command("debug_event")
    @click.argument("event", default="MrBeamDebugEvent")
    @click.option("--payload", "-p", default=None, help="optional payload string")
    @click.pass_context
    def debug_event_command(ctx, event, payload):
        _send_to_op(cli_group.settings, event, payload)

    @click.command("analytics")
    @click.argument("component")
    @click.argument("component_version")
    @click.argument("type")
    @click.argument("json_data")
    @click.pass_context
    def analytics(ctx, component, component_version, type, json_data):
        data = None
        try:
            data = json.loads(json_data)
        except:
            click.echo("Invalid JSON: {}".format(json_data))
            sys.exit(1)

        payload = dict(
            type=type,
            component=component,
            component_version=component_version,
            data=data,
        )
        _send_to_op(cli_group.settings, MrBeamEvents.ANALYTICS_DATA, payload)

    return [debug_event_command, analytics]


def _send_to_op(settings, event, payload):
    client = create_client(settings=settings)

    click.echo("client.baseurl {}".format(client.baseurl))
    click.echo("client.apikey {}".format(client.apikey))

    params = dict(command="cli_event", event=event, payload=payload)
    click.echo("Firing event - params: {}".format(params))

    r = client.post_json("/api/plugin/mrbeam", data=params)
    status_code = r.status_code
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        click.echo("Could not fire event, got {}".format(e))
        sys.exit(1)
    click.echo("Event fired:  {}".format(status_code))
    sys.exit(0)
