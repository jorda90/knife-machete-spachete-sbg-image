import re, os, glob, subprocess
from distutils.dir_util import copy_tree
from shutil import copyfile

WORK_DIR = os.getcwd()
#########################################################################
# PARAMETERS, I.E. INPUTS TO KNIFE CALL; need to add these here
# NOTE: When run via docker, a volume named KNIFE_MACH must be mounted 
# and contain all required index, annotation, and reference files. FOR
# NOW, this script. KNIFE_MACH must be located on level above WORK_DIR 
# on the host machine.
#########################################################################

use_toy_indel = True

# dataset_name CANNOT HAVE ANY SPACES IN IT
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", help="name of dataset-NO SPACES- will be used for naming files")
parser.add_argument("--readidstyle", help="read_id_style MUST BE either complete or appended")
parser.add_argument("--runid", help="run_id to use for naming runs with the same data set; defaults to aa")
parser.add_argument("--resources", help="path to directory containing references, annotation, and indices; defaults to /KNIFE_MACH")
args = parser.parse_args()
if args.dataset:
    dataset_name = args.dataset
else:
    dataset_name = "noname"

if args.readidstyle:
    read_id_style = args.readidstyle
    if (read_id_style not in ['complete','appended']):
        raise ValueError("Error: readidstyle must be one of complete or appended")
else:
    raise ValueError("Error: readidstyle must be one of complete or appended")
    
if args.runid:
    run_id = args.runid
else:
    run_id ="aa"

if args.resources:
    RESOURCE_DIR = args.resources
else:
    RESOURCE_DIR ="/KNIFE_MACH"
    
mode = "skipDenovo"
junction_overlap =  8
report_directory_name = "circReads"
ntrim = 50

# Not really used, just doing so it mimics test Data call
logstdout_from_knife = "logofstdoutfromknife"

##########################
### USAGE
############################

# sh completeRun.sh read_directory read_id_style alignment_parent_directory 
# dataset_name junction_overlap mode report_directory_name ntrim denovoCircMode 
# junction_id_suffix 2>&1 | tee out.log
# https://github.com/lindaszabo/KNIFE/tree/master/circularRNApipeline_Standalone

#########################################################################
# End of parameters
#########################################################################
 
# first have to create directories (if they don't already exist)
# and change file names and mv them to the right directories

# get current working dir

logfile = WORK_DIR + "/logkmach" + dataset_name + run_id + ".txt"

with open(logfile, 'w') as ff:
    ff.write(WORK_DIR)
    ff.write('\n\n\n')

# main directory to be used when running the knife:
KNIFE_DIR = "/srv/software/knife/circularRNApipeline_Standalone"

# place files in appropriate locations; fix code in future to
# avoid this step

anly_src = (KNIFE_DIR + "/analysis")
anly_dst = (RESOURCE_DIR + "/analysis")
anly_dst2 = (WORK_DIR + "/analysis")
if not os.path.exists(anly_dst):
        copy_tree(anly_src, anly_dst)
if not os.path.exists(anly_dst2):
        os.symlink(anly_dst, anly_dst2)

comprun_src = (KNIFE_DIR + "/completeRun.sh")
comprun_dst = (RESOURCE_DIR + "/completeRun.sh")
comprun_dst2 = (WORK_DIR + "/completeRun.sh")
if not os.path.exists(comprun_dst):
        copyfile(comprun_src, comprun_dst)
if not os.path.exists(comprun_dst2):
        os.symlink(comprun_dst, comprun_dst2)

findcirc_src = (KNIFE_DIR + "/findCircularRNA.sh")
findcirc_dst = (RESOURCE_DIR + "/findCircularRNA.sh")
findcirc_dst2 = (WORK_DIR + "/findCircularRNA.sh")
if not os.path.exists(findcirc_dst):
        copyfile(findcirc_src, findcirc_dst)
if not os.path.exists(findcirc_dst2):
        os.symlink(findcirc_dst, findcirc_dst2)

parfq_src = (KNIFE_DIR + "/ParseFastQ.py")
parfq_dst = (RESOURCE_DIR  + "/ParseFastQ.py")
parfq_dst2 = (WORK_DIR + "/ParseFastQ.py")
if not os.path.exists(parfq_dst):
        copyfile(parfq_src, parfq_dst)
if not os.path.exists(parfq_dst2):
        os.symlink(parfq_dst, parfq_dst2)

qstats_src = (KNIFE_DIR + "/qualityStats")
qstats_dst = (RESOURCE_DIR + "/qualityStats")
qstats_dst2 = (WORK_DIR + "/qualityStats")
if not os.path.exists(qstats_dst):
        copy_tree(qstats_src, qstats_dst)
if not os.path.exists(qstats_dst2):
        os.symlink(qstats_dst, qstats_dst2)

dns_src = (KNIFE_DIR + "/denovo_scripts")
dns_dst = (RESOURCE_DIR + "/denovo_scripts")
dns_dst2 = (WORK_DIR + "/denovo_scripts")
if not os.path.exists(dns_dst):
	copy_tree(dns_src, dns_dst)
if not os.path.exists(dns_dst2):
	os.symlink(dns_dst, dns_dst2)

subprocess.call(['chmod', '-R', '755', RESOURCE_DIR])


targetdir_list = [WORK_DIR + "/index", WORK_DIR + "/denovo_scripts", WORK_DIR + "/denovo_scripts/index"]
    
# check that all the subdirectories are there, as they should be!
# these should have been made beforehand, and should have appropriate files in them:
# files starting with infilebt2 and infilefastas should be in /index
#   and the prefixes "infilebt2" and "infilefastas" should be removed
# files starting with infilegtf should be in /denovo_scripts
#   and the prefix "infilegtf" should be removed
# files starting with infilebt1 should be in /denovo_scripts/index
#   and the prefix "infilebt1" should be removed

    
thisdir = targetdir_list[0]
if not os.path.exists(thisdir):
    raise ValueError("Error: directory " + thisdir + " does not exist.")

thisdir = targetdir_list[1]
if not os.path.exists(thisdir):
    raise ValueError("Error: directory " + thisdir + " does not exist.")

thisdir = targetdir_list[2]
if not os.path.exists(thisdir):
    raise ValueError("Error: directory " + thisdir + " does not exist.")

    
# cd into the knife directory; should not really be necessary
os.chdir(WORK_DIR)

with open(logfile, 'a') as ff:
    ff.write('\n\n\n')
    subprocess.check_call(["ls", "-R"], stdout=ff)
    ff.write('\n\n\n')
    

# run test of knife
# sh completeRun.sh READ_DIRECTORY complete OUTPUT_DIRECTORY testData 8 phred64 circReads 40 2>&1 | tee out.log

try:
    with open(logfile, 'a') as ff:
        ff.write('\n\n\n')
        # changing so as to remove calls to perl:
        subprocess.check_call("sh completeRun.sh " + WORK_DIR + " " + read_id_style + " " + WORK_DIR + " " + dataset_name + " " + str(junction_overlap) + " " + mode + " " + report_directory_name + " " + str(ntrim) + " 2>&1 | tee " + logstdout_from_knife , stdout = ff, shell=True)
        # original test call:
        # subprocess.check_call("sh completeRun.sh " + WORK_DIR + " complete " + WORK_DIR + " testData 8 phred64 circReads 40 2>&1 | tee outknifelog.txt", stdout = ff, shell=True)
except:
    with open(logfile, 'a') as ff:
        ff.write('Error in running completeRun.sh')


#############################################################################
# tar all files in data set folder (but not Swapped files)  and its
#  subdirectories and tar them
# It WILL output them with the directory structure, e.g. WITH a top level folder
#   with the name of the aata set, e.g. these:
# I.e. it will create a folder with a name
#   of the dataset like testData
# And below this will be subfolders such as
#    circReads  orig  sampleStats
# with a top level folder such as "testData" above them.
# I did it differently before, thus all the explanation.
#############################################################################

datadirlocation = WORK_DIR + "/" + dataset_name  

###Run MACHETE
CIRCPIPE_DIR = os.path.join(WORK_DIR,dataset_name)
if not os.path.isdir(CIRCPIPE_DIR):
    with open(logfile, 'a') as ff:
        ff.write('Problem: no directory\n' + CIRCPIPE_DIR + '\nMaking one.')
    os.mkdir(CIRCPIPE_DIR)
CIRCREF = os.path.join(WORK_DIR,"index")
# CIRCREF = os.path.join(WORK_DIR,dataset_name,report_directory_name,"index")
if not os.path.isdir(CIRCREF):
    with open(logfile, 'a') as ff:
        ff.write('No directory\n' + CIRCREF + '\nNot so surprising.\nMaking one.')
    os.mkdir(CIRCREF)
MACH_OUTPUT_DIR = os.path.join(WORK_DIR,"mach")
os.mkdir(MACH_OUTPUT_DIR)
EXONS = os.path.join(WORK_DIR,"HG19exons")

if use_toy_indel:
    REG_INDEL_INDICES = os.path.join(WORK_DIR,"toyIndelIndices") #test indices for faster runs
else:
    REG_INDEL_INDICES = os.path.join(WORK_DIR,"IndelIndices")

#########################################################################
#
# unpack HG19exons.tar.gz and IndelIndices.tar.gz
#
#########################################################################

os.chdir(WORK_DIR)

MACH_DIR = "/srv/software/machete"
MACH_RUN_SCRIPT = os.path.join(MACH_DIR,"run.py")

cmd = "python {MACH_RUN_SCRIPT} --circpipe-dir {CIRCPIPE_DIR} --output-dir {MACH_OUTPUT_DIR} --hg19Exons {EXONS} --reg-indel-indices {REG_INDEL_INDICES} --circref-dir {CIRCREF}".format(MACH_RUN_SCRIPT=MACH_RUN_SCRIPT,CIRCPIPE_DIR=CIRCPIPE_DIR,MACH_OUTPUT_DIR=MACH_OUTPUT_DIR,EXONS=EXONS,REG_INDEL_INDICES=REG_INDEL_INDICES,CIRCREF=CIRCREF)

with open(logfile, 'a') as ff:
        ff.write('\n\n\nAbout to run run.py\n')
        ff.write('\n\n\n')

with open(logfile, 'a') as ff:
        retcode = subprocess.call(cmd,shell=True, stdout=ff, stderr=ff)
#        popen = subprocess.check_call(cmd,shell=True, stdout=ff, stderr=ff)

## Write either YES*.error.in.subprocess.txt with 1 or
##     NO*.error.in.subprocess.txt with 0
## This allows you to see quickly in the results on Seven Bridges if there is 
##     an error in the subprocess call in run.py
## File ends in error.in.subprocess.txt; the name changes depending on the value.

errorfiles = [os.path.join(WORK_DIR, x + ".error." + dataset_name + run_id + '.is.error.in.subprocess.txt')  for x in ['YES','NO']]

if retcode:
    with open(errorfiles[0], 'w') as ff:
        ff.write('1')
else:
    with open(errorfiles[1], 'w') as ff:
        ff.write('0')

os.chdir(WORK_DIR)



with open(logfile, 'a') as ff:
    ff.write('\n\n\nListing working directory but not recursively.\n\n\n')
    
with open(logfile, 'a') as ff:
    subprocess.check_call("ls -alh", stdout=ff, stderr=ff, shell=True)
    
os.chdir(MACH_OUTPUT_DIR)


with open(logfile, 'a') as ff:
    ff.write('\n\n\nListing machete ouput directory recursively.\n\n\n')
    
with open(logfile, 'a') as ff:
    subprocess.check_call("ls -alRh", stdout=ff, stderr=ff, shell=True)
    
with open(logfile, 'a') as ff:
    ff.write('\n\n\nMasterError.txt should start here.\n\n\n')

os.chdir(WORK_DIR)
    
fullpatholderrorfile = MACH_OUTPUT_DIR + "/MasterError.txt"
if os.path.isfile(fullpatholderrorfile):
    subprocess.check_call("cat " + fullpatholderrorfile + " >> " + logfile, shell=True)
else:
    with open(logfile, 'a') as ff:
        ff.write('\n\n\nNo MasterError.txt file found.\n\n\n')

# tar everything in mach_output_dir/reports 
#   Tar if it exists
os.chdir(WORK_DIR)
mach_output_reports_dir = os.path.join(MACH_OUTPUT_DIR,"reports")
if os.path.isdir(mach_output_reports_dir):
    try:
        fullcall = "tar -cvzf " + dataset_name + run_id + "machreportsout.tar.gz -C " + MACH_OUTPUT_DIR + " reports"  
        with open(logfile, 'a') as ff:
            subprocess.check_call(fullcall, stderr=ff, stdout = ff, shell=True)
    except:
        with open(logfile, 'a') as ff:
            ff.write("\nError in tarring the machete output report files in the " + mach_output_reports_dir + " directory\n")
else:
    with open(logfile, 'a') as ff:
        ff.write("\nNo directory of machete output reports called " + mach_output_reports_dir + ", but expected that there was one.\n")
    

# tar everything in mach_output_dir/err_and_out if the directory exists
os.chdir(WORK_DIR)
mach_err_dir = os.path.join(MACH_OUTPUT_DIR,"err_and_out")
if os.path.isdir(mach_err_dir):
    try:
        fullcall = "tar -cvzf " + dataset_name + run_id + "macherrout.tar.gz -C " + MACH_OUTPUT_DIR + " err_and_out"  
        with open(logfile, 'a') as ff:
            subprocess.check_call(fullcall, stderr=ff, stdout = ff, shell=True)
    except:
        with open(logfile, 'a') as ff:
            ff.write("\nError in tarring the machete err_and_out directory, namely the " + mach_err_dir + " directory\n")
else:
    with open(logfile, 'a') as ff:
        ff.write("\nNo directory of machete errors and output called " + mach_err_dir + ", but expected that there was one.\n")

# tar everything in mach_output_dir/BadFJ_ver2 if the directory exists- changing name on jun 20
os.chdir(WORK_DIR)
mach_err_dir = os.path.join(MACH_OUTPUT_DIR,"BadFJ_ver2")
if os.path.isdir(mach_err_dir):
    try:
        fullcall = "tar -cvzf " + dataset_name + run_id + "machbadfjver2out.tar.gz -C " + MACH_OUTPUT_DIR + " BadFJ_ver2"  
        with open(logfile, 'a') as ff:
            subprocess.check_call(fullcall, stderr=ff, stdout = ff, shell=True)
    except:
        with open(logfile, 'a') as ff:
            ff.write("\nError in tarring the machete BadFJ_ver2 directory, namely the " + mach_err_dir + " directory\n")
else:
    with open(logfile, 'a') as ff:
        ff.write("\nNo directory of machete errors and output called " + mach_err_dir + ", but expected that there was one.\n")


# tar everything in mach_output_dir/x if the directory exists

def tar_subdirectory_of_mach_output_dir(thisdir, text_for_naming, MACH_OUTPUT_DIR, WORK_DIR, dataset_name, run_id, logfile):
    os.chdir(WORK_DIR)
    thisfulldir = os.path.join(MACH_OUTPUT_DIR,thisdir)
    if os.path.isdir(thisfulldir):
        try:
            fullcall = "tar -cvzf " + dataset_name + run_id + "mach" + text_for_naming + "out.tar.gz -C " + MACH_OUTPUT_DIR + " " + thisdir  
            with open(logfile, 'a') as ff:
                subprocess.check_call(fullcall, stderr=ff, stdout = ff, shell=True)
        except:
            with open(logfile, 'a') as ff:
                ff.write("\nError in tarring the machete " + thisdir + " directory, namely the " + thisfulldir + " directory\n")
    else:
        with open(logfile, 'a') as ff:
            ff.write("\nNo directory within machete output directory called " + thisfulldir + ", but expected that there was one.\n")

tar_subdirectory_of_mach_output_dir(thisdir = "GLM_classInput", text_for_naming = "glmclassinput", MACH_OUTPUT_DIR=MACH_OUTPUT_DIR, WORK_DIR=WORK_DIR, dataset_name=dataset_name, run_id=run_id, logfile=logfile)

tar_subdirectory_of_mach_output_dir(thisdir = "reports", text_for_naming = "reports", MACH_OUTPUT_DIR=MACH_OUTPUT_DIR, WORK_DIR=WORK_DIR, dataset_name=dataset_name, run_id=run_id, logfile=logfile)

tar_subdirectory_of_mach_output_dir(thisdir = "BadFJ", text_for_naming = "badfj", MACH_OUTPUT_DIR=MACH_OUTPUT_DIR, WORK_DIR=WORK_DIR, dataset_name=dataset_name, run_id=run_id, logfile=logfile)

# Now also get tar file of glm reports from knife for convenient reading together with
#  machete output.

os.chdir(WORK_DIR)

glmdirlocation = os.path.join(WORK_DIR, dataset_name, "circReads")

knifeglmreportstarfile = dataset_name + run_id + "knifeglmreportfilesout.tar.gz"

fullcall = "tar -cvzf " + knifeglmreportstarfile + " -C " + glmdirlocation + " glmReports"

with open(logfile, 'a') as ff:
    subprocess.check_call(fullcall, stdout=ff, stderr=ff, shell=True)

# Now copy StemList.txt and MasterError.txt to
#  files with better names so that they have unique names for each run
stemoutfile = WORK_DIR + "/StemList" + dataset_name + run_id +".txt"
stemorigfile = os.path.join(MACH_OUTPUT_DIR, "StemList.txt")
fullcall = "cp " + stemorigfile + " " + stemoutfile 
with open(logfile, 'a') as ff:
    subprocess.check_call(fullcall, stdout=ff, stderr=ff, shell=True)

mastererroroutfile = WORK_DIR + "/MasterError" + dataset_name + run_id +".txt"
mastererrororigfile = os.path.join(MACH_OUTPUT_DIR, "MasterError.txt")
fullcall = "cp " + mastererrororigfile + " " + mastererroroutfile
with open(logfile, 'a') as ff:
    subprocess.check_call(fullcall, stdout=ff, stderr=ff, shell=True)

os.unlink(anly_dst2)
os.unlink(comprun_dst2)
os.unlink(findcirc_dst2)
os.unlink(parfq_dst2)
os.unlink(qstats_dst2)
os.unlink(dns_dst2)
