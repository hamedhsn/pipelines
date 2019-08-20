import kfp as dsl
from kubernetes.client import V1EnvVar
from kfp import onprem

my_volume = onprem.mount_pvc(pvc_name='research-pvc-silo',
                             volume_name='pipeline',
                             volume_mount_path='/efs')


def standalone_job_op(name,
                      image,
                      working_dir,
                      cmd,
                      # params,
                      gpus=0,
                      cpu_limit='1',
                      memory_limit='1Gi',
                      envs=[],
                      timeout_hours=240):

    """This function submits a standalone training Job

        Args:
          name: the name of standalone_job_op
          image: the docker image name of training job
          mount: specify the datasource to mount to the job, like <name_of_datasource>:<mount_point_on_job>
          command: the command to run
    """
    options = []

    params_str = ''
    # for k, v in params.items():
    #     params_str += '{}={}'.format(k, v)

    ops = dsl.ContainerOp(
          name=name,
          image=image,
          command=["/bin/bash", "-c"],
          arguments=cmd.split(','),
          #               "--name", name,
          #               "--gpus", str(gpus),
          #               "--cpu", str(cpu_limit),
          #               "--step-name", '{{pod.name}}',
          #               "--workflow-name", '{{workflow.name}}',
          #               "--memory", str(memory_limit),
          #               "--timeout-hours", str(timeout_hours),
          #           ] + options + [
          #     "job",
          #     "--", str(command)
          # ],
          # file_outputs={'train': '/output.txt',
          #               'workflow': '/workflow-name.txt',
          #               'step': '/step-name.txt',
          #               'name': '/name.txt'}
      )
    ops.container.set_image_pull_policy('Always')
    ops.container.set_working_dir(working_dir)
    # ops.add_node_selector_constraint(label_name='beta.kubernetes.io/instance-type', value='m5.xlarge')

    if not gpus:
        ops.container.set_memory_limit(memory_limit)
        ops.container.set_cpu_limit(cpu_limit)

    ops.apply(my_volume)
    for e in envs:
        ops.container.add_env_variable(
            V1EnvVar(name=e['name'], value=e['value']))

    return ops
