# ***************************************************************************
# *   Copyright (c) 2015 - FreeCAD Developers                               *
# *   Copyright (c) 2018 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************/

import Fem
import FreeCAD
import ObjectsFem
import femsolver.run
import unittest
from . import utilstest as testtools
from .utilstest import fcc_print

from os.path import join


class TestSolverFrameWork(unittest.TestCase):
    fcc_print('import TestSolverFrameWork')

    # ********************************************************************************************
    def setUp(
        self
    ):
        # setUp is executed before every test
        # setting up a document to hold the tests
        self.doc_name = self.__class__.__name__
        if FreeCAD.ActiveDocument:
            if FreeCAD.ActiveDocument.Name != self.doc_name:
                FreeCAD.newDocument(self.doc_name)
        else:
            FreeCAD.newDocument(self.doc_name)
        FreeCAD.setActiveDocument(self.doc_name)
        self.active_doc = FreeCAD.ActiveDocument

        # more inits
        self.mesh_name = 'Mesh'
        self.temp_dir = testtools.get_fem_test_tmp_dir()
        self.test_file_dir = join(testtools.get_fem_test_home_dir(), 'ccx')

    # ********************************************************************************************
    def test_solver_framework(
        self
    ):
        fcc_print('\n--------------- Start of FEM tests  solver frame work ---------------')
        box = self.active_doc.addObject("Part::Box", "Box")
        fcc_print('Checking FEM new analysis...')
        analysis = ObjectsFem.makeAnalysis(
            self.active_doc,
            'Analysis'
        )
        self.assertTrue(analysis, "FemTest of new analysis failed")

        fcc_print('Checking FEM new material...')
        material_object = ObjectsFem.makeMaterialSolid(
            self.active_doc,
            'MechanicalMaterial'
        )
        mat = material_object.Material
        mat['Name'] = "Steel-Generic"
        mat['YoungsModulus'] = "200000 MPa"
        mat['PoissonRatio'] = "0.30"
        mat['Density'] = "7900 kg/m^3"
        material_object.Material = mat
        self.assertTrue(material_object, "FemTest of new material failed")
        analysis.addObject(material_object)

        fcc_print('Checking FEM new fixed constraint...')
        fixed_constraint = self.active_doc.addObject(
            "Fem::ConstraintFixed",
            "FemConstraintFixed"
        )
        fixed_constraint.References = [(box, "Face1")]
        self.assertTrue(fixed_constraint, "FemTest of new fixed constraint failed")
        analysis.addObject(fixed_constraint)

        fcc_print('Checking FEM new force constraint...')
        force_constraint = self.active_doc.addObject(
            "Fem::ConstraintForce",
            "FemConstraintForce"
        )
        force_constraint.References = [(box, "Face6")]
        force_constraint.Force = 40000.0
        force_constraint.Direction = (box, ["Edge5"])
        self.active_doc.recompute()
        force_constraint.Reversed = True
        self.active_doc.recompute()
        self.assertTrue(force_constraint, "FemTest of new force constraint failed")
        analysis.addObject(force_constraint)

        fcc_print('Checking FEM new pressure constraint...')
        pressure_constraint = self.active_doc.addObject(
            "Fem::ConstraintPressure",
            "FemConstraintPressure"
        )
        pressure_constraint.References = [(box, "Face2")]
        pressure_constraint.Pressure = 1000.0
        pressure_constraint.Reversed = False
        self.assertTrue(pressure_constraint, "FemTest of new pressure constraint failed")
        analysis.addObject(pressure_constraint)

        fcc_print('Checking FEM new mesh...')
        from .testfiles.ccx.cube_mesh import create_nodes_cube
        from .testfiles.ccx.cube_mesh import create_elements_cube
        mesh = Fem.FemMesh()
        ret = create_nodes_cube(mesh)
        self.assertTrue(ret, "Import of mesh nodes failed")
        ret = create_elements_cube(mesh)
        self.assertTrue(ret, "Import of mesh volumes failed")
        mesh_object = self.active_doc.addObject(
            'Fem::FemMeshObject',
            self.mesh_name
        )
        mesh_object.FemMesh = mesh
        self.assertTrue(mesh, "FemTest of new mesh failed")
        analysis.addObject(mesh_object)

        self.active_doc.recompute()

        # solver frame work ccx solver
        # calculix solver object
        fcc_print('\nChecking FEM CalculiX solver for solver frame work...')
        solver_ccx_object = ObjectsFem.makeSolverCalculix(
            self.active_doc,
            'SolverCalculiX'
        )
        solver_ccx_object.AnalysisType = 'static'
        solver_ccx_object.GeometricalNonlinearity = 'linear'
        solver_ccx_object.ThermoMechSteadyState = False
        solver_ccx_object.MatrixSolverType = 'default'
        solver_ccx_object.IterationsControlParameterTimeUse = False
        solver_ccx_object.EigenmodesCount = 10
        solver_ccx_object.EigenmodeHighLimit = 1000000.0
        solver_ccx_object.EigenmodeLowLimit = 0.0
        self.assertTrue(solver_ccx_object, "FemTest of new ccx solver failed")
        analysis.addObject(solver_ccx_object)

        static_base_name = 'cube_static'
        solverframework_analysis_dir = testtools.get_unit_test_tmp_dir(
            testtools.get_fem_test_tmp_dir(),
            'FEM_solverframework'
        )

        # write input file
        fcc_print('Checking FEM ccx solver for solver frame work......')
        fcc_print('machine_ccx')
        machine_ccx = solver_ccx_object.Proxy.createMachine(
            solver_ccx_object,
            solverframework_analysis_dir
        )
        machine_ccx.target = femsolver.run.PREPARE
        machine_ccx.start()
        machine_ccx.join()  # wait for the machine to finish.

        infile_given = join(
            testtools.get_fem_test_home_dir(),
            'ccx',
            (static_base_name + '.inp')
        )
        inpfile_totest = join(solverframework_analysis_dir, (self.mesh_name + '.inp'))
        fcc_print('Comparing {} to {}'.format(infile_given, inpfile_totest))
        ret = testtools.compare_inp_files(infile_given, inpfile_totest)
        self.assertFalse(ret, "ccxtools write_inp_file test failed.\n{}".format(ret))

        # use solver frame work elmer solver
        # elmer solver object
        solver_elmer_object = ObjectsFem.makeSolverElmer(
            self.active_doc,
            'SolverElmer'
        )
        self.assertTrue(solver_elmer_object, "FemTest of elmer solver failed")
        analysis.addObject(solver_elmer_object)
        solver_elmer_eqobj = ObjectsFem.makeEquationElasticity(
            self.active_doc,
            solver_elmer_object
        )
        self.assertTrue(solver_elmer_eqobj, "FemTest of elmer elasticity equation failed")

        # set ThermalExpansionCoefficient
        # current elmer seems to need it even on simple elasticity analysis
        mat = material_object.Material
        # FIXME elmer elasticity needs the dictionary key, otherwise it fails
        mat['ThermalExpansionCoefficient'] = "0 um/m/K"
        material_object.Material = mat

        mesh_gmsh = ObjectsFem.makeMeshGmsh(self.active_doc)
        mesh_gmsh.CharacteristicLengthMin = "9 mm"
        # elmer needs a GMHS mesh object
        # FIXME error message on Python solver run
        mesh_gmsh.FemMesh = mesh_object.FemMesh
        mesh_gmsh.Part = box
        analysis.addObject(mesh_gmsh)
        self.active_doc.removeObject(mesh_object.Name)

        # solver frame work Elmer solver
        # write input files
        fcc_print('\nChecking FEM Elmer solver for solver frame work...')
        machine_elmer = solver_elmer_object.Proxy.createMachine(
            solver_elmer_object,
            solverframework_analysis_dir,
            True
        )
        machine_elmer.target = femsolver.run.PREPARE
        machine_elmer.start()
        machine_elmer.join()  # wait for the machine to finish.

        # compare startinfo, case and gmsh input files
        test_file_dir_elmer = join(testtools.get_fem_test_home_dir(), 'elmer')

        fcc_print('Test writing STARTINFO file')
        startinfo_given = join(test_file_dir_elmer, 'ELMERSOLVER_STARTINFO')
        startinfo_totest = join(solverframework_analysis_dir, 'ELMERSOLVER_STARTINFO')
        fcc_print('Comparing {} to {}'.format(startinfo_given, startinfo_totest))
        ret = testtools.compare_files(startinfo_given, startinfo_totest)
        self.assertFalse(ret, "STARTINFO write file test failed.\n{}".format(ret))

        fcc_print('Test writing case file')
        casefile_given = join(test_file_dir_elmer, 'case.sif')
        casefile_totest = join(solverframework_analysis_dir, 'case.sif')
        fcc_print('Comparing {} to {}'.format(casefile_given, casefile_totest))
        ret = testtools.compare_files(casefile_given, casefile_totest)
        self.assertFalse(ret, "case write file test failed.\n{}".format(ret))

        fcc_print('Test writing GMSH geo file')
        gmshgeofile_given = join(test_file_dir_elmer, 'group_mesh.geo')
        gmshgeofile_totest = join(solverframework_analysis_dir, 'group_mesh.geo')
        fcc_print('Comparing {} to {}'.format(gmshgeofile_given, gmshgeofile_totest))
        ret = testtools.compare_files(gmshgeofile_given, gmshgeofile_totest)
        self.assertFalse(ret, "GMSH geo write file test failed.\n{}".format(ret))

        save_fc_file = solverframework_analysis_dir + static_base_name + '.FCStd'
        fcc_print('Save FreeCAD file for static2 analysis to {}...'.format(save_fc_file))
        self.active_doc.saveAs(save_fc_file)
        fcc_print('--------------- End of FEM tests solver frame work ---------------')

    # ********************************************************************************************
    def tearDown(
        self
    ):
        # clearance, is executed after every test
        FreeCAD.closeDocument(self.doc_name)
        pass
