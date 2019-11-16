# -*- coding: utf-8 -*-

import json
import tempfile

from vispy import config
from vispy.app import Canvas
from vispy.gloo import glir
from vispy.testing import requires_application, run_tests_if_main


def test_queue():
    q = glir.GlirQueue()
    parser = glir.GlirParser()
    
    # Test adding commands and clear
    N = 5
    for i in range(N):
        q.command('FOO', 'BAR', i)
    cmds = q.clear()
    for i in range(N):
        assert cmds[i] == ('FOO', 'BAR', i)
    
    # Test filter 1
    cmds1 = [('DATA', 1), ('SIZE', 1), ('FOO', 1), ('SIZE', 1), ('FOO', 1), 
             ('DATA', 1), ('DATA', 1)]
    cmds2 = [c[0] for c in q._shared._filter(cmds1, parser)]
    assert cmds2 == ['FOO', 'SIZE', 'FOO', 'DATA', 'DATA']
    
    # Test filter 2
    cmds1 = [('DATA', 1), ('SIZE', 1), ('FOO', 1), ('SIZE', 2), ('SIZE', 2), 
             ('DATA', 2), ('SIZE', 1), ('FOO', 1), ('DATA', 1), ('DATA', 1)]
    cmds2 = q._shared._filter(cmds1, parser)
    assert cmds2 == [('FOO', 1), ('SIZE', 2), ('DATA', 2), ('SIZE', 1), 
                     ('FOO', 1), ('DATA', 1), ('DATA', 1)]

    # Define shader
    shader1 = """
        precision highp float;uniform mediump vec4 u_foo;uniform vec4 u_bar;
        """.strip().replace(';', ';\n')
    # Convert for desktop
    shader2 = glir.convert_shader('desktop', shader1)
    assert 'highp' not in shader2
    assert 'mediump' not in shader2
    assert 'precision' not in shader2
    
    # Convert for es2
    shader3 = glir.convert_shader('es2', shader2)
    # make sure precision float is still in the shader
    # it may not be the first (precision int might be there)
    assert 'precision highp float;' in shader3
    # precisions must come before code
    assert shader3.startswith('precision')

    # Define shader with version number
    shader4 = """
        #version 100; precision highp float;uniform mediump vec4 u_foo;uniform vec4 u_bar;
        """.strip().replace(';', ';\n')
    shader5 = glir.convert_shader('es2', shader4)
    assert 'precision highp float;' in shader5
    # make sure that precision is first (version is removed)
    # precisions must come before code
    assert shader3.startswith('precision')


@requires_application()
def test_log_parser():
    """Test GLIR log parsing
    """
    glir_file = tempfile.TemporaryFile(mode='r+')

    config.update(glir_file=glir_file)
    with Canvas() as c:
        c.context.set_clear_color('white')
        c.context.clear()

    glir_file.seek(0)
    lines = glir_file.read().split(',\n')

    assert lines[0][0] == '['
    lines[0] = lines[0][1:]

    assert lines[-1][-1] == ']'
    lines[-1] = lines[-1][:-1]

    i = 0

    # The FBO argument may be anything based on the backend.
    expected = json.dumps(['CURRENT', 0, 1])
    assert len(lines[i]) >= len(expected)
    expected = expected.split('1')
    assert lines[i].startswith(expected[0])
    assert lines[i].endswith(expected[1])
    assert int(lines[i][len(expected[0]):-len(expected[1])]) is not None
    i += 1

    # The 'CURRENT' command may have been called multiple times
    while lines[i] == lines[i - 1]:
        i += 1
    assert lines[i] == json.dumps(['FUNC', 'clearColor', 1.0, 1.0, 1.0, 1.0])
    i += 1
    assert lines[i] == json.dumps(['FUNC', 'clear', 17664])
    i += 1
    assert lines[i] == json.dumps(['FUNC', 'finish'])
    i += 1

    config.update(glir_file='')
    glir_file.close()


@requires_application()
def test_capabilities():
    """Test GLIR capability reporting
    """
    with Canvas() as c:
        capabilities = c.context.shared.parser.capabilities
        assert capabilities['max_texture_size'] is not None
        assert capabilities['gl_version'] != 'unknown'

# The rest is basically tested via our examples

run_tests_if_main()
