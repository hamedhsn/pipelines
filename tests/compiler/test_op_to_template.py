import os

import kfp
import yaml
from kfp import dsl
from kubernetes.client import V1Toleration


def _test_op_to_template_yaml(ops, file_base_name):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    target_yaml = os.path.join(test_data_dir, file_base_name + '.yaml')
    print(target_yaml)
    with open(target_yaml, 'r') as f:
        expected = yaml.safe_load(f)['spec']['templates'][0]

    compiled_template = kfp.compiler.Compiler()._op_to_template(ops)

    del compiled_template['name'], expected['name']
    del compiled_template['outputs']['parameters'][0]['name'], expected['outputs']['parameters'][0]['name']
    assert compiled_template == expected


def test_tolerations():
    op1 = dsl.ContainerOp(
        name='download',
        image='busybox',
        command=['sh', '-c'],
        arguments=['sleep 10; wget localhost:5678 -O /tmp/results.txt'],
        file_outputs={'downloaded': '/tmp/results.txt'}) \
        .add_toleration(V1Toleration(
          effect='NoSchedule',
          key='gpu',
          operator='Equal',
          value='run'))
    # import pdb;pdb.set_trace()
    _test_op_to_template_yaml(op1, file_base_name='tolerations')
