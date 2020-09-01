#!/bin/sh
sequence=SEQUENCETOCHANGE
seq_length=${#sequence}
num_replica=$((${seq_length} * 2 + 5))

for i in 1 2
do
    cd 3em_npt/s${i}
    echo "s${i}: Running em2..."
    gmx_mpi grompp -f em2.mdp -c ion.gro -p cx_rsff2_tip3p.top -o em2.tpr &> grompp_em2.log
    gmx_mpi mdrun -v -s em2.tpr -ntomp 4 -deffnm em2 &> mdrun_em2.log
    python check_trajectory.py --seq ${sequence} --gro em2.gro
    sleep 2

    echo "s${i}: Running nvt1..."
    gmx_mpi grompp -v -f nvt1.mdp -c em2.gro -r em2.gro -p cx_rsff2_tip3p.top -o nvt1.tpr &> grompp_nvt1.log
    gmx_mpi mdrun -v -s nvt1.tpr -ntomp 4 -deffnm nvt1 &> mdrun_nvt1.log
    python check_trajectory.py --seq ${sequence} --gro nvt1.gro
    sleep 2

    echo "s${i}: Running npt1..."
    gmx_mpi grompp -v -f npt1.mdp -c nvt1.gro -r nvt1.gro -p cx_rsff2_tip3p.top -o npt1.tpr &> grompp_npt1.log
    gmx_mpi mdrun -v -s npt1.tpr -ntomp 4 -deffnm npt1 &> mdrun_npt1.log
    python check_trajectory.py --seq ${sequence} --gro npt1.gro
    sleep 2

    echo "s${i}: Running nvt2..."
    gmx_mpi grompp -v -f nvt2.mdp -c npt1.gro -p cx_rsff2_tip3p.top -o nvt2.tpr &> grompp_nvt2.log
    gmx_mpi mdrun -v -s nvt2.tpr -ntomp 4 -deffnm nvt2 &> mdrun_nvt2.log
    python check_trajectory.py --seq ${sequence} --gro nvt2.gro
    sleep 2

    echo "s${i}: Running npt2..."
    gmx_mpi grompp -v -f npt2.mdp -c nvt2.gro -p cx_rsff2_tip3p.top -o npt2.tpr &> grompp_npt2.log
    gmx_mpi mdrun -v -s npt2.tpr -ntomp 4 -deffnm npt2 &> mdrun_npt2.log
    python check_trajectory.py --seq ${sequence} --gro npt2.gro
    sleep 2

    cp npt2.gro ../../4bemeta/s${i}
    cp cx_rsff2_tip3p.top ../../4bemeta/s${i}

    cd ../../4bemeta/s${i}
    sed -i s/SYSTEMNAME/${sequence}/ submit.job
    sed -i s/REPLICANUMBER/${num_replica}/ submit.job
    sed -i s/TASKNUMBER/$((${num_replica} * 5))/ submit.job
    for j in `seq 0 $((${num_replica} - 1))`
    do
        gmx_mpi grompp -v -f mdrun.mdp -p cx_rsff2_tip3p.top -c npt2.gro -o start${j}.tpr &> grompp${j}.log
        gmx_mpi dump -s start${j}.tpr &> dump${j}.log
    done
    grep "fudge" dump*log &> fudge_check.txt

    python writeBemeta.py --gro npt2.gro


    cd ../../

done
