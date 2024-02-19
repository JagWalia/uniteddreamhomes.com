


import aws_cdk as core
import os
import json
import yaml


from backend_udh.backend_udh_stack import BackendUdhStack

def loadconfig(fpath):
    """
    Import settings from YAML config
    :return: dict with configuration items
    """
    config_path = fpath
    if not config_path:
        raise RuntimeError(
            "You need to supply config file path with CONFIG_PATH (dev-config/prod-config) variable in cdk.context.json file")

    # We don't verify config content, let fail in case something is missing
    with open(config_path, encoding="utf8") as config_file:
        config = yaml.safe_load(config_file.read())
    return config


app = core.App()
env = json.loads(os.getenv('CDK_CONTEXT_JSON'))
stage = app.node.try_get_context('stage')
print(f'STAGE is {stage}')
if stage not in ('dev', 'prod', 'beta'):
    stage = 'dev'

if stage.lower() == 'dev':
    stage_folder = env['dev-config']
if stage.lower() == 'beta':
    stage_folder = env['beta-config']
if stage.lower() == 'prod':
    stage_folder = env['prod-config']

env['stage'] = stage
stack = env['stack'] + "-" + stage
env['stack'] = stack
env['stage_folder'] = stage_folder

load_config_settings = loadconfig(stage_folder)

print(str(load_config_settings))
env['stage-setting'] = load_config_settings

BackendUdhStack(app, stack, env=core.Environment(
    account=str(env['stage-setting']['aws']['account']),
    region=str(env['stage-setting']['aws']['region'])), config=env
)

app.synth()

# BackendUdhStack(app, "BackendUdhStack",
#     )
