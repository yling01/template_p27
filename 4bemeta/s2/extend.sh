#!/bin/sh

echo "Enter sequence length:"
read seqLength
numReplica=$((${seqLength} * 2 + 5))

ori_pre=s2
ori_suf=''
dest=${ori_pre}_150ns

ori=${ori_pre}${ori_suf}
cd ../


mkdir ${dest}
cp ${ori}/extend.sh ${dest}
cp ${ori}/COLVAR* ${dest}
cp ${ori}/HILLS* ${dest}
cp ${ori}/*tpr ${dest}
cp ${ori}/bemeta.dat ${dest}
cp ${ori}/submit.job ${dest}
cd ${dest}
for i in `seq 0 $((${numReplica} - 1))`
do
  gmx_mpi convert-tpr -s start${i}.tpr -o temp.tpr -extend 50000 &> convert_tpr${i}.log
  mv temp.tpr start${i}.tpr
done
sed -i '1 i RESTART' bemeta.dat
sed -i '$d' submit.job
echo mpiexec gmx_mpi mdrun -v -resethway -plumed bemeta -multi ${numReplica} -replex 2500 -s start -deffnm prod -cpi ../${ori}/prod -noappend >> submit.job
