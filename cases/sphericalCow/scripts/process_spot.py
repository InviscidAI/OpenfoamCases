#!/usr/bin/env python3
"""Scale Keenan Crane's closed Spot cow once, ground it, orient it into +x wind,
and construct its equal-volume sphere.  The public-domain OBJ is never modified."""
from pathlib import Path
import json, math, shutil
import numpy as np
import pyvista as pv

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'geometry/spot/spot_triangulated.obj'
OUT=ROOT/'geometry'; OUT.mkdir(exist_ok=True)
TARGET_WITHERS=1.411
COW_EMBED=0.040
SPHERE_EMBED=0.075

# OBJ repeats vertices at texture seams. clean() only welds those coincident
# records; it does not fill, smooth, decimate, or otherwise repair Spot.
raw=pv.read(SRC).extract_surface().triangulate().clean(tolerance=1e-9,absolute=True)
if raw.n_open_edges:
    raise RuntimeError(f'Spot unexpectedly has {raw.n_open_edges} open edges')
P=np.asarray(raw.points)
ground_y=float(P[:,1].min())
# Anatomical withers: highest dorsal point in the shoulder/back band immediately
# behind the neck, source z=0.10..0.30 and |x|<0.30.  The selected mesh vertex is
# recorded.  This deliberately excludes Spot's oversized head, ears and horns.
wmask=(P[:,2]>=0.10)&(P[:,2]<=0.30)&(np.abs(P[:,0])<0.30)
wi=np.where(wmask)[0][np.argmax(P[wmask,1])]
wp=P[wi].copy(); raw_withers=float(wp[1]-ground_y)
scale=TARGET_WITHERS/raw_withers
# Source: x across, y up, head toward -z. CFD: x streamwise (head at -x),
# y lateral, z up. Uniform scale only.
Q=np.column_stack((P[:,2],P[:,0],P[:,1]-ground_y))*scale
T=raw.faces.reshape(-1,4)[:,1:]
mesh=pv.PolyData(Q,np.c_[np.full(len(T),3),T].ravel()).compute_normals(
    cell_normals=True,point_normals=False,consistent_normals=True,
    auto_orient_normals=True,non_manifold_traversal=False)
volume=abs(float(mesh.volume)); D=(6*volume/math.pi)**(1/3); R=D/2

# Reproducible landmark measurements on the stylised mesh.  They are readings,
# not targets. Longitudinal landmarks are documented source-z planes chosen on
# the side silhouette; widths are transverse slice bounds.
def slice_at(z):
    return raw.slice(normal=(0,0,1),origin=(0,0,z)).clean()
def perimeter_at(z):
    s=slice_at(z); pts=np.asarray(s.points); lines=s.lines.reshape(-1,3)[:,1:]
    return float(np.linalg.norm(pts[lines[:,0]]-pts[lines[:,1]],axis=1).sum()*scale)
def width_at(z):
    b=slice_at(z).bounds; return float((b.x_max-b.x_min)*scale)
def top_in(zlo,zhi):
    m=(P[:,2]>=zlo)&(P[:,2]<=zhi)&(np.abs(P[:,0])<0.30)
    return float((P[m,1].max()-ground_y)*scale)
# Chest floor: ventral centreline of the torso at z=0.30, excluding legs.
sch=slice_at(0.30); chest_floor=float((sch.bounds.y_min-ground_y)*scale)
rump_height=top_in(0.65,0.85)
shoulder_z=float(wp[2]); pin_z=0.90
trunk_length=(pin_z-shoulder_z)*scale
rump_length=(0.90-0.65)*scale
head_length=(shoulder_z-float(P[:,2].min()))*scale
chest_width=width_at(0.30); hip_width=width_at(0.70)
# Face/muzzle section, excluding the lateral ear/horn maximum.
head_width=width_at(-0.52)
thorax_perimeter=perimeter_at(0.40)
# One fore-shin loop at y=-0.60. Four disconnected leg loops are present;
# identify the positive-x, fore (source-z<0.3) loop and sum its segments.
ss=raw.slice(normal=(0,1,0),origin=(0,-0.60,0)).clean().connectivity()
fore=[]
for rid in np.unique(ss.cell_data['RegionId']):
    q=ss.extract_cells(np.where(ss.cell_data['RegionId']==rid)[0])
    b=q.bounds
    if b.x_min>0 and b.z_max<0.30: fore.append(q)
if len(fore)!=1: raise RuntimeError(f'could not identify one fore-shin loop: {len(fore)}')
q=fore[0]; qp=np.asarray(q.points); shin=0.0
for cell in q.cell:
    a,b=cell.point_ids; shin+=float(np.linalg.norm(qp[a]-qp[b]))
shin_perimeter=shin*scale

means={'withers_height_m':1.411,'rump_height_m':1.442,'chest_floor_height_m':0.763,
       'trunk_length_m':1.708,'rump_length_m':0.543,'head_length_m':0.519,
       'head_width_m':0.213,'chest_width_m':0.483,'hip_width_m':0.559,
       'thorax_perimeter_m':2.068,'shin_perimeter_m':0.193}
meas={'withers_height_m':TARGET_WITHERS,'rump_height_m':rump_height,
      'chest_floor_height_m':chest_floor,'trunk_length_m':trunk_length,
      'rump_length_m':rump_length,'head_length_m':head_length,
      'head_width_m':head_width,'chest_width_m':chest_width,
      'hip_width_m':hip_width,'thorax_perimeter_m':thorax_perimeter,
      'shin_perimeter_m':shin_perimeter}
# Aref is a documented torso frontal rectangle; force in N is less ambiguous.
Aref=max(chest_width,hip_width)*TARGET_WITHERS
meta={'source':'geometry/spot/spot_triangulated.obj',
 'license':'public domain; see geometry/spot/README.txt',
 'source_axes':'x across, y up, z longitudinal; muzzle toward -z',
 'cfd_axes':'x streamwise with head toward -x, y lateral, z up',
 'source_points_obj':17568,'welded_points':int(raw.n_points),'triangles':int(raw.n_cells),
 'source_open_edges_after_texture_seam_weld':int(raw.n_open_edges),'repair_operations':'none',
 'ground_source_y':ground_y,
 'withers_measurement':{'definition':'highest dorsal mesh vertex in shoulder/back band source z=0.10..0.30, |x|<0.30, relative to lowest hoof plane',
   'source_point':wp.tolist(),'raw_height':raw_withers},
 'uniform_scale_m_per_source_unit':scale,'measurements_m':meas,'holstein_means_m':means,
 'percent_difference':{k:100*(meas[k]/v-1) for k,v in means.items()},
 'measurement_definitions':{'rump_height':'highest dorsal point over source z=0.65..0.85',
  'chest_floor':'ventral bound of transverse slice at source z=0.30',
  'trunk_length':'source-z distance from measured withers to pin landmark z=0.90',
  'rump_length':'source-z distance from hip landmark z=0.65 to pin z=0.90',
  'head_length':'source-z distance from muzzle extreme to measured withers',
  'head_width':'transverse width at source z=-0.52','chest_width':'transverse width at source z=0.30',
  'hip_width':'transverse width at source z=0.70','thorax_perimeter':'slice perimeter at source z=0.40',
  'shin_perimeter':'positive-x fore-shin loop perimeter at source y=-0.60'},
 'volume_m3':volume,'equal_volume_sphere_diameter_m':D,
 'cow_bounds_cfd_m':[[mesh.bounds.x_min,mesh.bounds.y_min,mesh.bounds.z_min],[mesh.bounds.x_max,mesh.bounds.y_max,mesh.bounds.z_max]],
 'overall_length_m':float(mesh.bounds.x_max-mesh.bounds.x_min),
 'maximum_width_m':float(mesh.bounds.y_max-mesh.bounds.y_min),
 'maximum_height_m':float(mesh.bounds.z_max),
 'reference_frontal_area_m2':Aref,'cow_ground_embed_m':COW_EMBED,'sphere_ground_embed_m':SPHERE_EMBED}

# Unembedded scaled record geometry and CFD-grounded STL.
mesh.save(OUT/'spot_scaled_grounded.obj')
mesh.save(OUT/'cow.stl',binary=True)
mg=mesh.copy(); mg.translate((0,0,-COW_EMBED),inplace=True); mg.save(OUT/'cow_grounded.stl',binary=True)
# Floating Spot: place its vertical bounding-box centre at the domain mid-height.
mf=mesh.copy(); mf.translate((0,0,3.0-(mesh.bounds.z_min+mesh.bounds.z_max)/2),inplace=True); mf.save(OUT/'cow_floating.stl',binary=True)
pv.Sphere(radius=R,center=(0,0,R-SPHERE_EMBED),theta_resolution=128,phi_resolution=128).save(OUT/'sphere.stl',binary=True)
pv.Sphere(radius=R,center=(0,0,3.0),theta_resolution=128,phi_resolution=128).save(OUT/'isolated.stl',binary=True)
(OUT/'geometry.json').write_text(json.dumps(meta,indent=2))

# Required record views, showing the actual unembedded, scaled cow on z=0.
pv.OFF_SCREEN=True
ground=pv.Plane(center=(0,0,0),direction=(0,0,1),i_size=4.5,j_size=4.5)
focus=((mesh.bounds.x_min+mesh.bounds.x_max)/2,0,0.85)
views={'spot_side':((0,-6,1.2),focus,(0,0,1)),
       'spot_front':((-6,0,1.2),(mesh.bounds.x_min,0,0.85),(0,0,1)),
       'spot_three_quarter':((-5,-4,2.8),focus,(0,0,1))}
for name,(pos,foc,up) in views.items():
    pl=pv.Plotter(off_screen=True,window_size=(1200,900)); pl.set_background('white')
    pl.add_mesh(ground,color='#DDDDDD',show_edges=False)
    pl.add_mesh(mesh,color='#D9D5CC',smooth_shading=True,show_edges=False)
    pl.camera.position=pos; pl.camera.focal_point=foc; pl.camera.up=up
    pl.camera.parallel_projection=True; pl.reset_camera(); pl.camera.zoom(1.08)
    pl.show(screenshot=ROOT/f'{name}.png')
print(json.dumps(meta,indent=2))
