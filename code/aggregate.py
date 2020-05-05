import utils
from scipy import spatial
import shapely
import numpy as np
import os
import pickle
import random

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def message(*args, **kwargs):
    comm.barrier()
    if rank == 0:
        print(*args, **kwargs)

def get_swarm(poly, density):
    xmin, ymin, xmax, ymax = poly.envelope.bounds
    xrange, yrange = xmax - xmin, ymax - ymin
    npoints = int(round(density * xrange * yrange))
    if npoints > 0:
        xs = np.random.rand(npoints) * xrange + xmin
        ys = np.random.rand(npoints) * yrange + ymin
        return np.stack([xs, ys], axis = 1)
    else:
        return np.array([np.array(poly.centroid)])

def get_all_swarms(polys, density):
    polys = comm.scatter(np.array_split(np.array(polys), size), root = 0)
    keyLookup = []
    points = []
    for i, poly in enumerate(polys):
        swarm = get_swarm(poly, density)
        keyLookup.append(np.full(len(swarm), i))
        points.append(swarm)
    keyLookup, points = np.concatenate(keyLookup), np.concatenate(points)
    assert len(keyLookup) == len(points)
    keyLookup = np.concatenate(comm.allgather(keyLookup))
    points = np.concatenate(comm.allgather(points))
    return keyLookup, points

def get_kdTree(polys, density):
    keyLookup, points = get_all_swarms(polys, density)
    kdTree = spatial.cKDTree(points)
    return kdTree, keyLookup

def find_squares(fromCoords, toCoords):
    return np.where(
        (toCoords[:, 0] <= fromCoords[0]) \
        & (toCoords[:, 2] >= fromCoords[0]) \
        & (toCoords[:, 1] <= fromCoords[1]) \
        & (toCoords[:, 3] >= fromCoords[1])
        )[0]

class NoMatchFound(Exception):
    pass

def match_poly(fromPoly, toPolys, matches, medianToArea, toBounds, kdTree, keyLookup, centroidTree):

    # PREVIOUS STRATEGY
    if len(matches):
        candidate = matches[-1]
        if not candidate is None:
            poly = toPolys[candidate]
            if poly.contains(fromPoly):
#                 print("Matched from previous.")
                return candidate

    # SQUARES STRATEGY
    fromCoords = np.array(fromPoly.centroid)
    candidates = find_squares(fromCoords, toBounds)
    for candidate in candidates:
        poly = toPolys[candidate]
        if poly.contains(fromPoly):
#             print("Matched by squares.")
            return candidate

    # BUFFERING STRATEGY
    dists, indices = kdTree.query(fromPoly, k = 30)
    if not len(candidates):
        dists, indices = zip(*sorted(zip(dists, indices), key = lambda x: x[0]))
        candidates = frozenset([keyLookup[index] for index in indices])
    bufferLength = np.sqrt(medianToArea) / 2.
    fineness = 0
    prevStatus = 'neither'
    iterations = 0
    maxIterations = 30
    while len(candidates) and iterations < maxIterations:
        iterations += 1
        polys = [toPolys[c] for c in candidates]
        buffer = fromPoly.buffer(bufferLength)
        subCandidates = [
            c for c, p in zip(candidates, polys) \
                if p.intersects(buffer)
            ]
        if len(subCandidates) < 1:
            if prevStatus == 'too big':
                fineness += 1
            bufferLength *= (1. + 2. ** -fineness)
            prevStatus == 'too small'
        elif len(subCandidates) > 1:
            if prevStatus == 'too small':
                fineness += 1
            bufferLength /= (1. + 2. ** -fineness)
            candidates = subCandidates
            prevStatus == 'too big'
        else:
#             print("Matched by buffering.")
            return subCandidates[0]

    # CENTROID STRATEGY
    dist, index = centroidTree.query(fromPoly)
    candidate = keyLookup[index]
#     print("Matched by centroid")
    return candidate

def match_polys(fromPolys, toPolys, medianToArea, toBounds, kdTree, keyLookup, centroidTree):
    fromPolys = np.array(fromPolys, dtype = 'object')
    fromPolys = np.array_split(fromPolys, size)[rank]
    matches = []
    for fromPoly in fromPolys:
        match = match_poly(
            fromPoly,
            toPolys,
            matches,
            medianToArea,
            toBounds,
            kdTree,
            keyLookup,
            centroidTree
            )
        matches.append(match)
        if len(matches) % 10000 == 0:
            print('...')
        elif len(matches) % 1000 == 0:
            print('..')
        elif len(matches) % 100 == 0:
            print('.')
    matches = np.concatenate(comm.allgather(matches))
    return matches

def prepare(fromPolys, toPolys, zoom = 14):
    fromPolysSamples = [
        utils.point_to_polygon(p, zoom) if type(p) is shapely.geometry.Point else p \
            for p in [random.choice(fromPolys) for i in range(100)]
        ]
    toPolysSamples = [random.choice(toPolys) for i in range(100)]
    medianFromArea = np.median([poly.envelope.area for poly in fromPolysSamples])
    medianToArea = np.median([poly.envelope.area for poly in toPolysSamples])
    density = 10. / medianToArea
    kdTree, keyLookup = get_kdTree(toPolys, density)
    centroidTree = spatial.cKDTree(
        np.array([np.array(toPoly.centroid) for toPoly in toPolys])
        )
    toBounds = np.array([
        p.envelope.buffer(np.sqrt(medianFromArea) / 2.).bounds \
            for p in toPolys
        ])
    return medianToArea, toBounds, kdTree, keyLookup, centroidTree

def aggregate(fromPolys, toPolys):
    medianToArea, toBounds, kdTree, keyLookup, centroidTree = prepare(fromPolys, toPolys)
    matches = match_polys(fromPolys, toPolys, medianToArea, toBounds, kdTree, keyLookup, centroidTree)
    return matches
