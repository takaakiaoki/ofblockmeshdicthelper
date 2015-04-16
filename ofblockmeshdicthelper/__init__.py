# for compatibility to Py2.7
from __future__ import unicode_literals, print_function

import io
from string import Template


class Vertex(object):
    def __init__(self, x, y, z, name, index=None):
        self.x = x
        self.y = y
        self.z = z
        self.name = name  # identical name
        self.alias = set([name])  # aliasname, self.name should be included

        # seqential index which is assigned at final output
        # for blocks, edges, boundaries
        self.index = None

    def format(self):
        com = str(self.index) + ' ' + self.name
        if len(self.alias) > 1:
            com += ' : '
            com += ' '.join(self.alias)
        return '( {0:18.15g} {1:18.15g} {2:18.15g} )  // {3:s}'.format(
            self.x, self.y, self.z, com)

    def __lt__(self, rhs):
        return (self.z, self.y, self.x) < (rhs.z, rhs.y, rhs.z)

    def __eq__(self, rhs):
        return (self.z, self.y, self.x) == (rhs.z, rhs.y, rhs.z)


class Face(object):
    def __init__(self, vnames, name):
        """
        vname is list or tuple of vertex names
        """
        self.vnames = vnames
        self.name = name

    def format(self, vertices):
        """Format instance to dump
        vertices is dict of name to Vertex
        """
        index = ' '.join(str(vertices[vn].index) for vn in self.vnames)
        com = ' '.join(self.vnames)  # for comment
        return '({0:s})  // {1:s} ({2:s})'.format(index, self.name, com)


class HexBlock(object):
    def __init__(self, vnames, cells, name):
        """Initialize HexBlock instance
        vnames is the vertex names in order descrived in
            http://www.openfoam.org/docs/user/mesh-description.php
        cells is number of cells devied into in each direction
        name is the uniq name of the block
        """
        self.vnames = vnames
        self.cells = cells
        self.name = name

    def format(self, vertices):
        """Format instance to dump
        vertices is dict of name to Vertex
        """
        index = ' '.join(str(vertices[vn].index) for vn in self.vnames)
        vcom = ' '.join(self.vnames)  # for comment
        return 'hex ({0:s}) {2:s} ({1[0]:d} {1[1]:d} {1[2]:d}) '\
               'simpleGrading (1 1 1)  // {2:s} ({3:s})'.format(
                    index, self.cells, self.name, vcom)

    def face(self, index, name=None):
        """Generate Face object
        index is number or keyword to identify the face of Hex
            0 = 'w' = 'xm' = '-100' = (0 4 7 3)
            1 = 'e' = 'xp' = '100' = (1 2 5 6)
            2 = 's' = 'ym' = '0-10' = (0 1 5 4)
            3 = 'n' = 'yp' = '010' = (2 3 7 6)
            4 = 'b' = 'zm' = '00-1' = (0 3 2 1)
            5 = 't' = zp' = '001' = (4 5 6 7)
        name is given to Face instance. If omitted, name is automatically
            genaratied like ('f-' + self.name + '-w')
        """
        kw_to_index = {
            'w': 0, 'xm': 0, '-100': 0,
            'e': 1, 'xp': 1, '100': 1,
            's': 2, 'ym': 2, '0-10': 2,
            'n': 3, 'yp': 3, '010': 3,
            'b': 4, 'zm': 4, '00-1': 4,
            't': 5, 'zp': 5, '001': 5}
        index_to_vertex = [
            (0, 4, 7, 3),
            (1, 2, 6, 5),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 3, 2, 1),
            (4, 5, 6, 7)]
        index_to_defaultsuffix = [
            'f-{}-w',
            'f-{}-n',
            'f-{}-s',
            'f-{}-n',
            'f-{}-b',
            'f-{}-t']

        if isinstance(index, str):
            index = kw_to_index[index]

        vnames = tuple([self.vnames[i] for i in index_to_vertex[index]])
        if name is None:
            name = index_to_defaultsuffix[index].format(self.name)
        return Face(vnames, name)


class Boundary(object):
    def __init__(self, type_, name, faces=[]):
        """ initialize boundary
        type_ is type keyword (wall, patch, empty, ..)
        name is nave of boundary emelment
        faces is faces which are applied with this boundary conditions
        """
        self.type_ = type_
        self.name = name
        self.faces = faces

    def add_face(self, face):
        """add face instance
        face is a Face instance (not name) to be added
        """
        self.faces.append(face)

    def format(self, vertices):
        """Format instance to dump
        vertices is dict of name to Vertex
        """
        buf = io.StringIO()

        buf.write(self.name + '\n')
        buf.write('{\n')
        buf.write('    type {};\n'.format(self.type_))
        buf.write('    faces\n')
        buf.write('    (\n')
        for f in self.faces:
            s = f.format(vertices)
            buf.write('        {}\n'.format(s))
        buf.write('    );\n')
        buf.write('}')
        return buf.getvalue()


class BlockMeshDict(object):
    def __init__(self):
        self.convert_to_meters = 1.0
        self.vertices = {}  # mapping of uniq name to Vertex object
        self.blocks = {}
        self.boundaries = {}

    def set_metric(self, metric):
        """set self.comvert_to_meters by word"""
        metricsym_to_conversion = {
            'km': 1000,
            'm': 1,
            'cm': 0.01,
            'mm': 0.001,
            'um': 1e-6,
            'nm': 1e-9,
            'A': 1e-10,
            'Angstrom': 1e-10}
        self.convert_to_meters = metricsym_to_conversion[metric]

    def add_vertex(self, x, y, z, name):
        """add vertex by coordinate and uniq name
        x y z is coordinates of vertex
        name is uniq name to refer the vertex
        returns Vertex object whici is added.
        """
        self.vertices[name] = Vertex(x, y, z, name)
        return self.vertices[name]

    def del_vertex(self, name):
        """del name key from self.vertices"""
        del self.vertices[name]

    def reduce_vertex(self, name1, *names):
        """treat name1, name2, ... as same point.

        name2.alias, name3.alias, ... are merged with name1.alias
        the key name2, name3, ... in self.vertices are kept and mapped to
        same Vertex instance as name1
        """
        v = self.vertices[name1]
        for n in names:
            w = self.vertices[n]
            v.alias.update(w.alias)
            # replace mapping from n w by to v
            self.vertices[n] = v

    def add_hexblock(self, vnames, cells, name):
        b = HexBlock(vnames, cells, name)
        self.blocks[name] = b
        return b

    def add_boundary(self, type_, name, faces=[]):
        b = Boundary(type_, name, faces)
        self.boundaries[name] = b
        return b

    def assign_vertexid(self):
        """1. create list of Vertex which are referred by blocks only.
        2. sort vertex according to (x, y, z)
        3. assign sequence number for each Vertex
        4. sorted list is saved as self.valid_vertices
        """

        # gather 'uniq' names which are refferred by blocks
        validvnames = set()
        self.valid_vertices = []
        for b in self.blocks.values():
            for n in b.vnames:
                v = self.vertices[n]
                if v.name not in validvnames:
                    validvnames.update([v.name])
                    self.valid_vertices.append(v)

        self.valid_vertices = sorted(self.valid_vertices)
        for i, v in enumerate(self.valid_vertices):
            v.index = i

    def format_vertices_section(self):
        """format vertices section.
        assign_vertexid() should be called before this method, because
        self.valid_vetices should be available and member self.valid_vertices
        should have valid index.
        """
        buf = io.StringIO()
        buf.write('vertices\n')
        buf.write('(\n')
        for v in self.valid_vertices:
            buf.write('    ' + v.format() + '\n')
        buf.write(');')
        return buf.getvalue()

    def format_edges_section(self):
        return '''\
edges
(
);'''

    def format_blocks_section(self):
        """format bloks section.
        assign_vertexid() should be called before this method, because
        vertices reffered by blocks should have valid index.
        """
        buf = io.StringIO()
        buf.write('blocks\n')
        buf.write('(\n')
        for b in self.blocks.values():
            buf.write('    ' + b.format(self.vertices) + '\n')
        buf.write(');')
        return buf.getvalue()

    def format_boundary_section(self):
        """format boundary section.
        assign_vertexid() should be called before this method, because
        vertices reffered by faces should have valid index.
        """
        buf = io.StringIO()
        buf.write('boundary\n')
        buf.write('(\n')
        for b in self.boundaries.values():
            # format Boundary instance and add indent
            indent = ' ' * 4
            s = b.format(self.vertices).replace('\n', '\n'+indent)
            buf.write(indent + s + '\n')
        buf.write(');')
        return buf.getvalue()

    def format_mergepatchpairs_section(self):
        return '''\
mergePatchPairs
(
);'''

    def format(self):
        template = Template(r'''/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  2.3.0                                 |
|   \\  /    A nd           | Web:      www.OpenFOAM.org                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters $metricconvert;

$vertices

$edges

$blocks

$boundary

$mergepatchpairs

// ************************************************************************* //
''')

        return template.substitute(
            metricconvert=str(self.convert_to_meters),
            vertices=self.format_vertices_section(),
            edges=self.format_edges_section(),
            blocks=self.format_blocks_section(),
            boundary=self.format_boundary_section(),
            mergepatchpairs=self.format_mergepatchpairs_section())
