#!/usr/bin/env python
"""
sfire_clip_snapshot:        "Create initial conditions file for FIRE+STARFORGE simulation 
                            with the refinement position placed at a custom position.
                            The custom position is specified by the user. The script will
                            then choose particles within a certain distance of the custom
                            position and clip out everything else.
                            The script will then create an hdf5 file with the ICs."

Usage: sfire_clip_snapshot.py [options]

Options:
    -h, --help                                                      Show this screen
    --snapdir=<snapdir>                                             Are snapshots in a snapdir directory? [default: False]
    --path=<path>                                                   Path to the simulation directory [default: ./]
    --sim=<sim>                                                     Simulation name [default: ]
    --snap_num=<snap_num>                                           Snapshot number to clip [default: 100]
    --ic_path=<ic_path>                                             Path to save the IC file [default: ./] 
    --dist_cut_off=<dist_cut_off>                                   Distance cut off for gas particles to be used in finding COM velocity (in kpc) [default: 0.1]
    --use_refine_center_from_file=<use_refine_center_from_file>     Use the refine center from the file? [default: True]
    --refine_center_coords=<refine_center_coords>                   Refinement center coords (leave empty if using from file) [default: 0,0,0]
"""

from generic_utils.fire_utils import *
from cloud_utils.cloud_quants import *
from cloud_utils.cloud_utils import *
from cloud_utils.cloud_selection import *
from generic_utils.script_utils import *
from docopt import docopt

#import numpy as np
import os




def clip_hdf5_file(snap_num, cut_off_distance, path, ic_path, use_refine_center_from_file, refine_center_coords=None, snapdir=False):
    """
    This is a function to create an hdf5 file with just the particles within a certain distance of the custom position.
    Inputs:
        snap_num: the snapshot number
        refine_center_coords: the coordinates of the center of the refinement region
        params: the Params object
        ic_path: the path to save the IC file
    
    Outputs:
        None
    """

    print ('Reading file....')
    if snapdir:
        file_name = path+'snapdir_{snap_num}/snapshot_{snap_num}.hdf5'.format(snap_num=snap_num)
    else:
        file_name = path+'snapshot_{snap_num}.hdf5'.format(snap_num=snap_num)
    f = h5py.File(file_name, 'r')
    header_data_dict = {}
    gas_data_dict = {}
    star_data_dict = {}
    dm_data_dict = {}
    collisionless_data_dict = {}
    sink_data_dict = {}
    for key in f.keys():
        if key == 'Header':
            for key2 in f[key].attrs.keys():
                header_data_dict[key2] = f[key].attrs[key2]
            print ("Loaded header data")
        
        if key == 'PartType0':
            for key2 in f[key].keys():
                gas_data_dict[key2] = np.array(f[key][key2])
            print ("Loaded gas data")

        if key == 'PartType4':
            for key2 in f[key].keys():
                star_data_dict[key2] = np.array(f[key][key2])
            print ("Loaded star data")

        if key == 'PartType5':
            for key2 in f[key].keys():
                sink_data_dict[key2] = np.array(f[key][key2])
            print ("Loaded sink data")
        
    f.close()

    if use_refine_center_from_file:
        refine_center_coords = header_data_dict['RefinementRegionCenter']
    print ("Refine center coords: ", refine_center_coords)

    # Find the particles that are within a certain distance of the custom position
    gas_dist_from_refine_coords = np.linalg.norm(gas_data_dict['Coordinates'] - refine_center_coords, axis=1)
    gas_inds = np.where(gas_dist_from_refine_coords<cut_off_distance)[0]
    star_dist_from_refine_coords = np.linalg.norm(star_data_dict['Coordinates'] - refine_center_coords, axis=1)
    star_inds = np.where(star_dist_from_refine_coords<cut_off_distance)[0]
    sink_dist_from_refine_coords = np.linalg.norm(sink_data_dict['Coordinates'] - refine_center_coords, axis=1)
    sink_inds = np.where(sink_dist_from_refine_coords<cut_off_distance)[0]
    
    print ("Number of gas particles within cut off distance:", len(gas_inds))
    print ("Number of star particles within cut off distance:", len(star_inds))
    print ("Number of sink particles within cut off distance:", len(sink_inds))


    # Now we can create the new hdf5 file with just the clipped particles
    print ('Writing to file now ....')

    if not os.path.exists(ic_path):
        os.makedirs(ic_path)

    file_name = ic_path+'snapshot_{snap_num}.hdf5'.format(snap_num=snap_num)
    f = h5py.File(file_name, 'w')
    header = f.create_group('Header')
    for key in header_data_dict.keys():
        if key=='NumPart_ThisFile' or key=='NumPart_Total':
            arr = np.zeros(6)
            #header_data_dict['NumPart_ThisFile']
            arr[0] = len(gas_inds)
            arr[4] = len(star_inds)
            arr[5] = len(sink_inds)
            header.attrs.create(key, arr)
        #if key=='BoxSize':
        else:
            header.attrs.create(key, header_data_dict[key])
    
    part0 = f.create_group('PartType0')
    for key in gas_data_dict.keys():
        part0.create_dataset(key, data=gas_data_dict[key][gas_inds])
    
    part4 = f.create_group('PartType4')
    for key in star_data_dict.keys():
        part4.create_dataset(key, data=star_data_dict[key][star_inds])

    part5 = f.create_group('PartType5')
    for key in sink_data_dict.keys():
        part5.create_dataset(key, data=sink_data_dict[key][sink_inds])
    
    f.close()









if __name__ == '__main__':
    args = docopt(__doc__)
    path = args['--path']
    sim = args['--sim']
    snapdir = convert_to_bool(args['--snapdir'])
    snap_num = int(args['--snap_num'])
    ic_path = args['--ic_path']
    dist_cut_off = float(args['--dist_cut_off'])
    use_refine_center_from_file = convert_to_bool(args['--use_refine_center_from_file'])
    refine_center_coords = convert_to_array(args['--refine_center_coords'])


    
    print ("Path = ", path)
    print ("Sim = ", sim)
    print ("Snapdir = ", snapdir)
    print ("Snap num = ", snap_num)
    print ("IC path = ", ic_path)

    if use_refine_center_from_file:
        refine_center_coords = None

    clip_hdf5_file(snap_num, dist_cut_off, path, ic_path, use_refine_center_from_file, refine_center_coords, snapdir)
    print("HDF5 file created successfully")



