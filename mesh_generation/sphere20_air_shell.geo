SetFactory("OpenCASCADE");

// Geometry is in nm. The Python simulation uses size = 1e-9.
r_iron = 20.0;
r_air = 60.0;
r_shell = 120.0;

// Mesh sizes in nm. The background field refines the magnetic sphere and
// coarsens the non-magnetic far-field regions to keep the first run modest.
h_iron = 2.0;
h_air = 5.0;
h_shell = 10.0;

Sphere(1) = {0, 0, 0, r_iron};
Sphere(2) = {0, 0, 0, r_air};
Sphere(3) = {0, 0, 0, r_shell};

// Build non-overlapping regions:
//   1: iron sphere
//   air[]: air shell between r_iron and r_air
//   shell[]: outer transformation shell between r_air and r_shell
shell[] = BooleanDifference{ Volume{3}; Delete; }{ Volume{2}; };
air[] = BooleanDifference{ Volume{2}; Delete; }{ Volume{1}; };

Physical Volume(1) = {1};
Physical Volume(2) = {air[0]};
Physical Volume(3) = {shell[0]};

// Smooth radial mesh-size transition.
Field[1] = MathEval;
Field[1].F = Sprintf(
  "%g + (%g-%g) * Min(1, Sqrt(x*x+y*y+z*z)/%g)",
  h_iron, h_shell, h_iron, r_shell
);
Background Field = 1;

Mesh.CharacteristicLengthMin = h_iron;
Mesh.CharacteristicLengthMax = h_shell;
Mesh.ElementOrder = 1;
Mesh.SaveGroupsOfElements = 1;
Mesh.SaveGroupsOfNodes = 0;
Mesh 3;
