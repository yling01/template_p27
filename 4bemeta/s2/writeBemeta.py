import optparse
import numpy as np
import sys
def getPhiPsi(file, cyclic, gro):
    fi= open(file)
    index = {}
    index["N"] = []
    index["CA"] = []
    index["C"] = []
    for line in fi:
        if not gro and line[0:6].strip() != "ATOM":
            continue
        if len(line) < 20:
            continue

        if gro:
            atomName = line[10:15].strip()
            atomID = line[15:20].strip()
        else:
            atomID = line[6:11].strip()
            atomName = line[12:16].strip()

        if atomName in ["C", "N", "CA"]:
            if index[atomName]:
                index[atomName].append(atomID)
            else:
                index[atomName] = [atomID]
    fi.close()

    assert len(index["N"]) == len(index["CA"])
    assert len(index["CA"]) == len(index["C"])

    index_Psi = []
    for i in range(len(index["N"]) -  int(not(cyclic))):
        index_Psi.append(index["N"][i])
        index_Psi.append(index["CA"][i])
        index_Psi.append(index["C"][i])
        index_Psi.append(index["N"][(i + 1) % len(index["N"])])

    index_Phi = []
    for i in range(int(not(cyclic)), len(index["N"])):
        index_Phi.append(index["C"][(i - 1) % len(index["C"])])
        index_Phi.append(index["N"][i])
        index_Phi.append(index["CA"][i])
        index_Phi.append(index["C"][i])

    assert len(index_Phi) == len(index_Psi)

    return np.array(index_Phi).reshape((-1, 4)).tolist(), np.array(index_Psi).reshape((-1, 4)).tolist()

def write_PhiPsi(Phi, Psi):
    with open("PhiPsi.ndx", "w+") as fo:
        fo.write("[ PhiPsi ]\n")
        for i in range(len(Phi)):
            fo.write(" ".join(Phi[i]))
            fo.write("\n")
        for j in range(len(Psi)):
            fo.write(" ".join(Psi[j]))
            fo.write("\n")

def write_bemeta(Phi, Psi, output):
    assert len(Phi) == len(Psi)
    numRes = len(Psi)
    with open(output, "w+") as fo:
        rep_counter = 0
        cv_counter = 0
        fo.write("RANDOM_EXCHANGES\n\n")
        for i in range(numRes):
            fo.write("#Rep%d; Res%d:phi/psi\n" % (rep_counter, i + 1))
            fo.write("cv%d: TORSION ATOMS=%s\n" % (cv_counter, ",".join(Phi[i])))
            cv_counter += 1
            fo.write("cv%d: TORSION ATOMS=%s\n\n" % (cv_counter, ",".join(Psi[i])))
            cv_counter += 1
            rep_counter += 1
        for j in range(numRes):
            fo.write("#Rep%d; Res%d:psi/Res%d:phi\n" % (rep_counter, j + 1, (j + 1) % numRes + 1))
            fo.write("cv%d: TORSION ATOMS=%s\n" % (cv_counter, ",".join(Psi[j])))
            cv_counter += 1
            fo.write("cv%d: TORSION ATOMS=%s\n\n" % (cv_counter, ",".join(Phi[(j + 1) % numRes])))
            cv_counter += 1
            rep_counter += 1
        cv = []
        for k in range(0, cv_counter, 2):
            cv.append("{cv%d,cv%d}" % (k, k + 1))
        cv += ["{cv0,cv1}"] * 5
        fo.write("metad: METAD ...\n    ARG=@replicas:{%s}\n" % ",".join(cv))
        height = ["0.1"] * rep_counter + ["0.0"] * 5
        fo.write("    HEIGHT=@replicas:{%s}" % ",".join(height))
        fo.write("\n    SIGMA=0.31416,0.31416\n    PACE=2000\n    FILE=HILLS\n")
        grid_min = ["{-pi,-pi}"] * (numRes * 2 + 5)
        grid_max = ["{pi,pi}"] * (numRes * 2 + 5)
        fo.write("    GRID_MIN=@replicas:{%s}\n" % ",".join(grid_min))
        fo.write("    GRID_MAX=@replicas:{%s}\n" % ",".join(grid_max))
        fo.write("    GRID_WFILE=BIAS_GRID\n    GRID_WSTRIDE=2000\n...\n")
        fo.write("\nPRINT ARG=@replicas:{%s} FILE=COLVAR STRIDE=500\n\nENDPLUMED" % ",".join(cv))

def getArgument(arg):
    if arg[0].upper() == "T":
        return True
    return False

if __name__ == "__main__":
    print("\n!!!Test Version Use With Causion!!!\n")
    parser = optparse.OptionParser()
    parser.add_option('--gro', dest = 'gro', default = '')
    parser.add_option('--writeNDX', dest = 'writeNDX', default = 'False')
    parser.add_option('--bemetaName', dest = 'output', default = 'bemeta.dat')
    parser.add_option('--cyclic', dest = 'cyclic', default = 'True')
    parser.add_option('--pdb', dest = 'pdb', default = '')
    (options, args) = parser.parse_args()

    gro = options.gro
    pdb = options.pdb

    if gro and pdb:
        sys.exit("\nExiting...Both pdb and gro files declared...\n")

    elif not gro and not pdb:
        sys.exit("\nExiting...No pdb or gro file declared...\n")

    if gro:
        inputFile = gro
    else:
        inputFile = pdb

    output = options.output
    writeNDX = getArgument(options.writeNDX)
    cyclic = getArgument(options.cyclic)

    Phi, Psi = getPhiPsi(inputFile, cyclic, gro)
    write_bemeta(Phi, Psi, output)
    if writeNDX:
        write_PhiPsi(Phi, Psi)
