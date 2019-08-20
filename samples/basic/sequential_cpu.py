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

from kubernetes.client import V1EnvVar

my_volume = onprem.mount_pvc(pvc_name='research-pvc-silo', volume_name='pipeline', volume_mount_path='/efs')

def gcs_download_op(url):
    ops = dsl.ContainerOp(
        name='GCS - Download',
        image='google/cloud-sdk:216.0.0',
        command=['sh', '-c'],
        arguments=['gsutil cat $0 | tee $1', url, '/efs/Users/Hamed/kfp/results.txt'],
        file_outputs={
            'data': '/efs/Users/Hamed/kfp/results.txt',
        }
    )
    ops.apply(my_volume)

    return ops


def echo_op(text):
    ops = dsl.ContainerOp(
        name='echo',
        image='library/bash:4.4.23',
        command=['python', '-c'],
        arguments=['echo $MSG;echo "$0"', text]
    )
    ops.container.add_env_variable(V1EnvVar(name='MSG', value='hello world'))
    ops.apply(my_volume)

    return ops


@dsl.pipeline(
    name='Sequential pipeline CPU test',
    description='A pipeline with two sequential steps.'
)
def sequential_pipeline(url='gs://ml-pipeline-playground/shakespeare1.txt'):
    """A pipeline with two sequential steps."""

    download_task = gcs_download_op(url)
    echo_task = echo_op(download_task.output)

def main():
    KFP_SERVICE = "localhost:8889" # "ml-pipeline.kubeflow.svc.cluster.local:8888"
    client = kfp.Client(host=KFP_SERVICE)
    kfp.compiler.Compiler().compile(sequential_pipeline, __file__ + '.tar.gz')
    experiment_id = client.get_experiment(experiment_name='hsn-sequential-cpu').id
    print(experiment_id)
    # if not experiment_id:
    client.upload_pipeline('hsn-sequential-cpu.tar.gz', pipeline_name='hsn-sequential-cpu1')
    # client.create_run_from_pipeline_package('hsn-sequential-cpu.tar.gz',
    #                                         run_name='test_local_1',
    #                                         experiment_name='hsn-sequential-cpu',
    #                                         arguments={'url': 'gs://ml-pipeline-playground/shakespeare1.txt'})
    run = client.run_pipeline(experiment_id, 'testttt', 'hsn-sequential-cpu.tar.gz',
                              params={'url': 'gs://ml-pipeline-playground/shakespeare1.txt'})


if __name__ == '__main__':
    main()
