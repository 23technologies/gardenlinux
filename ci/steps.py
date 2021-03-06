import enum
import os
import typing

import tkn.model

DEFAULT_IMAGE = 'eu.gcr.io/gardener-project/cc/job-image:1.788.0'

own_dir = os.path.abspath(os.path.dirname(__file__))
scripts_dir = os.path.join(own_dir)


def extend_python_path_snippet(param_name: str):
    sd_name = os.path.basename(scripts_dir)
    return f'sys.path.insert(1,os.path.abspath(os.path.join("$(params.{param_name})","{sd_name}")))'


class ScriptType(enum.Enum):
    BOURNE_SHELL = 'sh'
    PYTHON3 = 'python3'


def task_step_script(
    path: str,
    script_type: ScriptType,
    callable: str,
    params: typing.List[tkn.model.NamedParam],
    repo_path_param: typing.Optional[tkn.model.NamedParam]=None,
):
    '''
    renders an inline-step-script, prepending a shebang, and appending an invocation
    of the specified callable (passing the given params).
    '''
    with open(path) as f:
        script = f.read()

    if script_type is ScriptType.PYTHON3:
        shebang = '#!/usr/bin/env python3'
        if repo_path_param:
            preamble = 'import sys,os;' + extend_python_path_snippet(repo_path_param.name)
        else:
            preamble = ''
        args = ','.join((
            f"{param.name.replace('-', '_')}='$(params.{param.name})'" for param in params
        ))
        callable_str = f'{callable}({args})'
    elif script_type is ScriptType.BOURNE_SHELL:
        shebang = '#!/usr/bin/env sh'
        preamble = ''
        args = ' '.join(param.name for param in params)
        callable_str = 'f{callable} {args}'

    return '\n'.join((
        shebang,
        preamble,
        script,
        callable_str,
    ))


def clone_step(
    committish: tkn.model.NamedParam,
    git_url: tkn.model.NamedParam,
    repo_dir: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    step = tkn.model.TaskStep(
        name='clone-repo-step',
        image=DEFAULT_IMAGE,
        script=task_step_script(
            path=os.path.join(scripts_dir, 'clone_repo_step.py'),
            script_type=ScriptType.PYTHON3,
            callable='clone_and_copy',
            params=[
                committish,
                git_url,
                repo_dir,
            ],
            repo_path_param=repo_dir,
        ),
        volumeMounts=volume_mounts,
        env=env_vars,
    )

    return step


def upload_results_step(
    architecture: tkn.model.NamedParam,
    cicd_cfg_name: tkn.model.NamedParam,
    committish: tkn.model.NamedParam,
    gardenlinux_epoch: tkn.model.NamedParam,
    modifiers: tkn.model.NamedParam,
    outfile: tkn.model.NamedParam,
    platform: tkn.model.NamedParam,
    publishing_actions: tkn.model.NamedParam,
    repo_dir: tkn.model.NamedParam,
    version: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    return tkn.model.TaskStep(
        name='upload-results',
        image=DEFAULT_IMAGE,
        script=task_step_script(
            path=os.path.join(scripts_dir, 'upload_results_step.py'),
            script_type=ScriptType.PYTHON3,
            callable='upload_results_step',
            params=[
                architecture,
                cicd_cfg_name,
                committish,
                gardenlinux_epoch,
                modifiers,
                outfile,
                platform,
                publishing_actions,
                version,
            ],
            repo_path_param=repo_dir,
        ),
        volumeMounts=volume_mounts,
        env=env_vars,
    )


def promote_single_step(
    architecture: tkn.model.NamedParam,
    cicd_cfg_name: tkn.model.NamedParam,
    committish: tkn.model.NamedParam,
    gardenlinux_epoch: tkn.model.NamedParam,
    modifiers: tkn.model.NamedParam,
    platform: tkn.model.NamedParam,
    publishing_actions: tkn.model.NamedParam,
    repo_dir: tkn.model.NamedParam,
    version: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    return tkn.model.TaskStep(
        name='promote-step',
        image=DEFAULT_IMAGE,
        script=task_step_script(
            path=os.path.join(scripts_dir, 'promote_step.py'),
            script_type=ScriptType.PYTHON3,
            callable='promote_single_step',
            params=[
                architecture,
                cicd_cfg_name,
                committish,
                gardenlinux_epoch,
                modifiers,
                platform,
                publishing_actions,
                version,
            ],
            repo_path_param=repo_dir,
        ),
        volumeMounts=volume_mounts,
        env=env_vars,
    )


def promote_step(
    cicd_cfg_name: tkn.model.NamedParam,
    committish: tkn.model.NamedParam,
    flavourset: tkn.model.NamedParam,
    gardenlinux_epoch: tkn.model.NamedParam,
    publishing_actions: tkn.model.NamedParam,
    repo_dir: tkn.model.NamedParam,
    version: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    return tkn.model.TaskStep(
        name='finalise-promotion-step',
        image=DEFAULT_IMAGE,
        script=task_step_script(
            path=os.path.join(scripts_dir, 'promote_step.py'),
            script_type=ScriptType.PYTHON3,
            callable='promote_step',
            params=[
                cicd_cfg_name,
                committish,
                flavourset,
                gardenlinux_epoch,
                publishing_actions,
                version,
            ],
            repo_path_param=repo_dir,
        ),
        volumeMounts=volume_mounts,
        env=env_vars,
    )


def pre_build_step(
    architecture: tkn.model.NamedParam,
    cicd_cfg_name: tkn.model.NamedParam,
    committish: tkn.model.NamedParam,
    gardenlinux_epoch: tkn.model.NamedParam,
    modifiers: tkn.model.NamedParam,
    platform: tkn.model.NamedParam,
    publishing_actions: tkn.model.NamedParam,
    repo_dir: tkn.model.NamedParam,
    version: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    return tkn.model.TaskStep(
        name='prebuild-step',
        image=DEFAULT_IMAGE,
        script=task_step_script(
            path=os.path.join(scripts_dir, 'pre_build_step.py'),
            script_type=ScriptType.PYTHON3,
            callable='pre_build_step',
            params=[
                architecture,
                cicd_cfg_name,
                committish,
                gardenlinux_epoch,
                modifiers,
                platform,
                publishing_actions,
                version,
            ],
            repo_path_param=repo_dir,
        ),
        volumeMounts=volume_mounts,
        env=env_vars,
    )


def release_step(
    committish: tkn.model.NamedParam,
    gardenlinux_epoch: tkn.model.NamedParam,
    giturl: tkn.model.NamedParam,
    publishing_actions: tkn.model.NamedParam,
    repo_dir: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    return tkn.model.TaskStep(
        name='release-step',
        image=DEFAULT_IMAGE,
        script=task_step_script(
            path=os.path.join(scripts_dir, 'release_step.py'),
            script_type=ScriptType.PYTHON3,
            callable='release_step',
            params=[
                committish,
                gardenlinux_epoch,
                giturl,
                publishing_actions,
            ],
            repo_path_param=repo_dir,
        ),
        volumeMounts=volume_mounts,
        env=env_vars,
    )


def build_image_step(
    gardenlinux_epoch: tkn.model.NamedParam,
    modifiers: tkn.model.NamedParam,
    outfile: tkn.model.NamedParam,
    platform: tkn.model.NamedParam,
    repodir: tkn.model.NamedParam,
    snapshot_timestamp: tkn.model.NamedParam,
    suite: tkn.model.NamedParam,
    env_vars: typing.List[typing.Dict] = [],
    volume_mounts: typing.List[typing.Dict] = [],
):
    pass
