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
import requests
from kfp import dsl, onprem

from kubernetes.client import V1EnvVar

from samples.basic.mlinfra_pipline import standalone_job_op

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
        image='635083230749.dkr.ecr.eu-west-1.amazonaws.com/ml_notebook:simple-test',
        command=['python', 'test.py'],
        arguments=[]
    )
    ops.container.add_env_variable(V1EnvVar(name='MSG', value='hello world'))
    ops.container.set_image_pull_policy('Always')
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


def main_pipeline():
    params = {'url': 'gs://ml-pipeline-playground/shakespeare1.txt'}
    @dsl.pipeline(
        name='Sequential pipeline CPU test',
        description='A pipeline with two sequential steps.'
    )
    def mlinfra_job(url='gs://ml-pipeline-playground/shakespeare1.txt'):
        """A pipeline with two sequential steps."""
        # 172.20.133.145
    def mlinfra_job(url):
        """A pipeline with two sequential steps."""
        standalone_job_op('test',
                          '635083230749.dkr.ecr.eu-west-1.amazonaws.com/ml_notebook:simple-test',
                          working_dir='/home/app',
                          cmd='python test.py')
    pipeline_name = 'mlinfra_job2'
    kfp.compiler.Compiler().compile(mlinfra_job, f'{pipeline_name}.tar.gz')
    try:
        experiment_id = client.get_experiment(experiment_name='Hamed').id
        print(f'Old exp id: {experiment_id}')
    except:
        experiment_id = client.create_experiment('Hamed').id
        print(f'New exp id: {experiment_id}')

    try:
        pp_id = [a.id for a in client.list_pipelines(page_size=1000000).pipelines if a.name == pipeline_name]
        if pp_id:
            requests.delete(f'http://{KFP_SERVICE}/apis/v1beta1/pipelines/{pp_id[0]}')

        pp_id = client.upload_pipeline(f'{pipeline_name}.tar.gz', pipeline_name=pipeline_name).id
    except Exception as e:
        print(e)

    run = client.run_pipeline(experiment_id, 'job_name_test_1', pipeline_id=pp_id,
                              params=params)
    print(run.id)


def main():
    kfp.compiler.Compiler().compile(sequential_pipeline, __file__ + '1.tar.gz')
    experiment_id = client.get_experiment(experiment_name='hsn-sequential-cpu').id
    if not experiment_id:
        client.upload_pipeline('hsn-sequential-cpu1.tar.gz', pipeline_name='hsn-sequential-cpu1')
    # client.create_run_from_pipeline_package('hsn-sequential-cpu.tar.gz',
    #                                         run_name='test_local_1',
    #                                         experiment_name='hsn-sequential-cpu',
    #                                         arguments={'url': 'gs://ml-pipeline-playground/shakespeare1.txt'})
    run = client.run_pipeline(experiment_id, 'test1_1', 'hsn-sequential-cpu.tar.gz',
                              params={'url': 'gs://ml-pipeline-playground/shakespeare1.txt'})


if __name__ == '__main__':
    KFP_SERVICE = "localhost:8889"  # "ml-pipeline.kubeflow.svc.cluster.local:8888"
    client = kfp.Client(host=KFP_SERVICE)
    main_pipeline()
    # main()
