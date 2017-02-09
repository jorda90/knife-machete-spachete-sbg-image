#!/bin/bash
#$ -cwd
#$ -j y
#$ -S /bin/bash
#$ -V

#Usage: rnafusion_wrapper.sh <gdc_id> <gdc_filename> <md5> <file_size> <state> <token> <work_dir> <cluster.process_id>
#NOTES: Manifest must be in wkdir, FastQC and cutadapt must be in $PATH
#A directory named 'KNIFE_MACH' must be located in the $wkdir and contain callknife.py, denovo_scripts/, HG19exons/, HG19exons.tar.gz, index/, toyIndelIndices/
#....should detail here the exact structure and content of KNIFE_MACH
id=$1
filename=$2
md5=$3
size=$4
state=$5
token=$6	###When dockerizing, some inputs may need to be adjusted
wkdir=$7
pid=$8

cd $wkdir

#Trim Galore parameters
error=0.1
minimum=20
stringency=1
quality=20

#KNIFE/MACHETE parameters
dockwd=`echo $wkdir | rev | cut -d/ -f1 | rev`
dataname=rnafusion_out
runid=`echo $pid | cut -d. -f2`
#overlap=8	#PE<70bp=8 (default); PE>70=13; SE<70=10; SE>70=15


echo "RNAFUSION PIPELINE INITIATED" > rnafusion_wrapper.$pid.log
if [ ! -f "$wkdir/$id/NO.error.`echo $dataname$runid`.is.error.in.subprocess.txt" ]
then
	#Recreate the manifest required by gdc-client to pull sequence from GDC Data Portal#
	echo "ACQUIRE SEQUENCE BAM FILE" >> rnafusion_wrapper.$pid.log
	if [[ ! -f "$id/$filename" && ! -f "$id/"$id"_1.fq.gz" ]]
	then
		printf "%s\t%s\t%s\t%s\t%s\n" "id" "filename" "md5" "size" "state" "$id" "$filename" "$md5" "$size" "$state" > gdc.manifest.$pid

		echo "	Downloading bam file [ID: $id] from GDC Data Portal: $(date) " >> rnafusion_wrapper.$pid.log
		/opt/installed/gdc-client/bin/gdc-client download -m $wkdir/gdc.manifest.$pid -t $token
		echo "	Download complete: $(date)" >> rnafusion_wrapper.$pid.log
	else
		echo "	BAM already exists" >> rnafusion_wrapper.$pid.log
	fi

	echo "Verifying MD5 sum" >> rnafusion_wrapper.$pid.log
	mdck=`md5sum $id/$filename | cut -d' ' -f1`
	if [ $mdck == $md5 ]
	then
		targets=(callknife.py HG19exons index toyIndelIndices)
		cd $id
		for t in ${targets[@]}; do ln -s ../KNIFE_MACH/$t 2> /dev/null; done		#May need to be changed later depending on what needs to be contained within the docker image
		cd ..
	
		#Convert to FASTQ
		echo "CONVERT BAM TO FASTQ" >> rnafusion_wrapper.$pid.log
		if [ ! -f "$wkdir/$id/"$id"_1.fq.gz" ]
		then
			echo "	Converting $filename to FASTQ: $(date)" >> rnafusion_wrapper.$pid.log
			java -Xmx30g -jar /home/exacloud/lustre1/users/chiotti/tools/picard-tools-1.139/picard.jar SamToFastq VALIDATION_STRINGENCY=SILENT INPUT=$id/$filename FASTQ=$id/"$id"_1.fq SECOND_END_FASTQ=$id/"$id"_2.fq    #All tool paths will be changed to a single location for Docker
			if [ $? == 0 ]
			then
				echo "	BAM to FASTQ conversion complete: $(date)" >> rnafusion_wrapper.$pid.log
			else
				echo "	BAM to FASTQ conversion FAILED: $(date)" >> rnafusion_wrapper.$pid.log
			fi
	
			#Run trim_galore. For now arguments are hard-coded
			echo "	Trimming adapter sequences: $(date)" >> rnafusion_wrapper.$pid.log
			/home/exacloud/lustre1/users/chiotti/tools/trim_galore/trim_galore --suppress_warn --gzip --fastqc --paired $id/"$id"_1.fq $id/"$id"_2.fq --quality $quality --stringency $stringency -e $error --length $minimum -o $id
			if [ $? == 0 ]
			then
				mv $id/"$id"_1_val_1.fq.gz $id/"$id"_1.fq.gz 
				mv $id/"$id"_2_val_2.fq.gz  $id/"$id"_2.fq.gz
				echo "	Adapter trimming complete: $(date)" >> rnafusion_wrapper.$pid.log
				rm -f $id/*fq
			else
				echo "	Adapter trimming FAILED: $(date)" >> rnafusion_wrapper.$pid.log
			fi
		else
			echo "	Trimmed FASTQ already available" >> rnafusion_wrapper.$pid.log
		fi
	
		#Load salzman_rnafusion:v3 image, if necessary, then run
		if [ ! -f "$wkdir/$id/NO.error.`echo $dataname$runid`.is.error.in.subprocess.txt" ]
		then
	                echo "RUN KNIFE_MACHETE PIPELINE" >> rnafusion_wrapper.$pid.log
			echo "	Checking for salzman_rnafusion:v3 image" >> rnafusion_wrapper.$pid.log
			/home/exacloud/lustre1/users/chiotti/tools/scripts/run_program/docker/docker_check_load.sh /home/exacloud/lustre1/users/chiotti/tools/docker_images/salzman_rnafusion/salzman_rnafusion.tar	
	
			echo "	Running pipeline: $(date)" >> rnafusion_wrapper.$pid.log
			docker run -P --rm=true -v $wkdir/$id:/$dockwd -v /mnt/scratch:/tmp  -v $wkdir/KNIFE_MACH:/KNIFE_MACH --workdir /$dockwd salzman_rnafusion:v3 python callknife.py --dataset=$dataname --readidstyle=appended --resources=/KNIFE_MACH --runid=$runid
			exitcode=$?
			if [ ! -f "$wkdir/$id/NO.error.`echo $dataname$runid`.is.error.in.subprocess.txt" ]
			then
				echo "	KNIFE_MACHETE FAILED: $(date)" >> rnafusion_wrapper.$pid.log
			else
				rm -f $id/logofstdoutfromknife $id/$id*bam $id/$id*bai $id/$id*fq.gz
				echo "	KNIFE_MACHETE SUCCESSFUL: $(date)" >> rnafusion_wrapper.$pid.log
				if [ $exitcode != 0 ]
				then
					echo " ERRORS produced by rnafusion_wrapper.sh" >> rnafusion_wrapper.$pid.log
				fi
			fi
		else
			echo "	KNIFE_MACHETE output is already available for $filename" >> rnafusion_wrapper.$pid.log
		fi
	
		for t in ${targets[@]}; do unlink $id/$t 2> /dev/null; done
	
	else
		echo "	Sequence download error. MD5 sums do not match. Run aborted: $(date) " >> rnafusion_wrapper.$pid.log
		echo "	Cleaning up workspace" >> rnafusion_wrapper.$pid.log
		rm -rf $wkdir/$id
		if [ -f *mani*$pid ]
		then
			rm -f *mani*$pid
		fi

		echo "	Workspace clean. Exiting: $(date) " >> rnafusion_wrapper.$pid.log
	fi
	
	mkdir -p $wkdir/$id/logs
	mv $pid.* rnafusion_wrapper.$pid.log $id/log* $wkdir/$id/logs
	if [ -f *mani*$pid ]
	then
		mv *mani*$pid $wkdir/$id/logs
	fi
	echo "RNAFUSION PIPELINE END" >> $wkdir/$id/logs/rnafusion_wrapper.$pid.log

else
	mkdir -p $wkdir/$id/logs
        mv $pid.* rnafusion_wrapper.$pid.log $wkdir/$id/logs
        echo "  EXITING: KNIFE_MACHETE output is already available for $id/$filename" >> $wkdir/$id/logs/rnafusion_wrapper.$pid.log

fi
