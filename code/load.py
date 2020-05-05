import csv
import os
import ast

def default_proc(val):
    try:
        return ast.literal_eval(val)
    except:
        return val

def load_data(name, path = '.', ext = 'csv', _printSuppress = False, **procFuncs):
    header = []
    data = []
    dataPath = os.path.abspath(os.path.join(path, name))
    if not ext is None:
        dataPath += '.' + ext
    with open(dataPath, 'r') as f:
        r = csv.reader(f, delimiter = ',')
        rawheader = next(r)
        for key in rawheader:
            if key in procFuncs:
                if not procFuncs[key] is None:
                    header.append(key)
            else:
                header.append(key)
        for i, row in enumerate(r):
            outrow = []
            for key, val in zip(rawheader, row):
                try:
                    procFunc = procFuncs[key]
                    if not procFunc is None:
                        outrow.append(procFunc(val))
                except KeyError:
                    outrow.append(default_proc(val))
            data.append(outrow)
    if not _printSuppress:
        sample = list(zip(header, data[0]))
        print("*Printing 0th of {0} records*".format(len(data)))
        for row in sample: print(row[0] + ': ', row[1])
    return header, data

def load_datas(
        path = '.',
        ext = 'csv',
        superkeyName = 'superkey',
        superkeyProc = default_proc,
        _printSuppress = False,
        **procFuncs
        ):
    headers = []
    datas = []
    names = sorted([
        os.path.splitext(name)[0] \
            for name in os.listdir(path) \
                if os.path.splitext(name)[1].lstrip('.') == ext
        ])
    for name in names:
        header, data = load_data(
            name,
            path,
            ext,
            _printSuppress = True,
            **procFuncs
            )
        headers.append(header)
        datas.append(data)
    assert len(set([tuple(header) for header in headers])) == 1
    header = headers[0]
    header.append(superkeyName)
    for dNum, (name, data) in enumerate(zip(names, datas)):
        for rNum, row in enumerate(data):
            datas[dNum][rNum].append(superkeyProc(name))
    data = [item for sublist in datas for item in sublist]
    if not _printSuppress:
        sample = list(zip(header, data[0]))
        print("*Printing 0th of {0} records*".format(len(data)))
        for row in sample: print(row[0] + ': ', row[1])
    return header, data
