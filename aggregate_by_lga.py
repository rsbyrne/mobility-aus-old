import sys
import os
import pickle

import utils
from aggregate import aggregate

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

repoDir = sys.argv[1]
inName = sys.argv[2]
inType = sys.argv[3]
outDir = sys.argv[4]
outName = sys.argv[5]

dataDir = os.path.join(repoDir, 'data')

def get_lgas_polys(lgaFrame):
    lgas, polys = list(zip(*[
        (lga, poly) \
            for lga, poly in zip(lgaFrame.index, lgaFrame['geometry']) \
                if not poly is None
        ]))
    return lgas, polys

def load_lgas_polys(repoDir):
    lgas, polys = None, None
    if rank == 0:
        lgaFrame = utils.load_lgas(repoDir)
        lgas, polys = get_lgas_polys(lgaFrame)
    lgas, polys = comm.bcast(lgas, root = 0), comm.bcast(polys, root = 0)
    return lgas, polys

lgas, toPolys = load_lgas_polys(repoDir)

fromPolys = None
if rank == 0:
    if inType == 'pop':
        data = utils.load_population_tiles(
            dataDir,
            inName,
            tz = 'Australia/Melbourne',
            )
    elif inType == 'mob':
        data = utils.load_mobility_tiles(
            dataDir,
            inName,
            tz = 'Australia/Melbourne',
            )
    else:
        raise ValueError
    quadkeys = sorted(set(data['quadkey']))
    fromPolys = [utils.quadkey_to_point(q) for q in quadkeys]
fromPolys = comm.bcast(fromPolys, root = 0)

matches = aggregate(fromPolys, toPolys)

if rank == 0:
    matchesDict = dict(zip(quadkeys, [lgas[i] for i in matches]))
    with open(os.path.join(outDir, outName), 'wb') as f:
        pickle.dump(matchesDict, f)
    print("Done.")