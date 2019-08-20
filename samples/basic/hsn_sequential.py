#!/usr/bin/env python3
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import kfp
from kfp import dsl, onprem

my_volume = onprem.mount_pvc(pvc_name='research-pvc-silo', volume_name='pipeline', volume_mount_path='/mnt/workflow')


def gcs_download_op(url):
    ops = dsl.ContainerOp(
        name='GCS - Download',
        image='google/cloud-sdk:216.0.0',
        command=['sh', '-c'],
        arguments=['gsutil cat $0 | tee $1', url, '/mnt/workflow/results.txt'],
        file_outputs={
            'data': '/mnt/workflow/results.txt',
        }
    )
    ops = ops.apply(my_volume)
    return ops


def echo_op(text):
    ops = dsl.ContainerOp(
        name='echo',
        image='library/bash:4.4.23',
        command=['sh', '-c'],
        arguments=['echo "$MSG"']
    ).apply(my_volume)
    # arguments=['echo "$0"', text]

    # ops.container.add_env_variable(V1EnvVar(name='MSG', value='hello world'))

    return ops


@dsl.pipeline(
    name='Sequential pipeline test',
    description='A pipeline with two sequential steps.'
)
def sequential_pipeline(url='gs://ml-pipeline-playground/shakespeare1.txt'):
    """A pipeline with two sequential steps."""

    download_task = gcs_download_op(url)
    echo_task = echo_op(download_task.output)

if __name__ == '__main__':
    kfp.compiler.Compiler().compile(sequential_pipeline, __file__ + '.zip')
