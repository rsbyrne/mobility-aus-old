import os
import pickle

import utils
from aggregate import aggregate

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

repoDir = '../..'
dataDir = os.path.join(repoDir, 'data')
outDir = '.'

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
    vicPopTiles = utils.load_population_tiles(
        os.path.join(dataDir, 'test'), #os.path.join(dataDir, 'vic_pop_tiles'), # <--- TEST
        tz = 'Australia/Melbourne',
        )
    quadkeys = sorted(set(vicPopTiles['quadkey']))
    fromPolys = [utils.quadkey_to_point(q) for q in quadkeys]
fromPolys = comm.bcast(fromPolys, root = 0)

matches = aggregate(fromPolys, toPolys)

print("Done!")
if rank == 0:
    matchesDict = dict(zip(quadkeys, [lgas[i] for i in matches]))
    with open(os.path.join(outDir, 'matched.pkl'), 'wb') as f:
        pickle.dump(matchesDict, f)