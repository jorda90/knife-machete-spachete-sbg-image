import re, os, glob, subprocess

 
WORK_DIR = os.getcwd()
#########################################################################
# PARAMETERS, I.E. INPUTS TO KNIFE CALL; need to add these here
#########################################################################

# dataset_name CANNOT HAVE ANY SPACES IN IT
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", help="name of dataset-NO SPACES- will be used for naming files")
parser.add_argument("--readidstyle", help="read_id_style MUST BE either complete or appended")
parser.add_argument("--runid", help="run_id to use for naming runs with the same data set; defaults to aa")
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
    
mode = "skipDenovo"
# read_id_style= "appended"
junction_overlap =  8
report_directory_name = "circReads"
ntrim= 40

# Not really used, just doing so it mimics test Data call
logstdout_from_knife = "logofstdoutfromknife"

##########################
### USAGE
############################

#sh completeRun.sh read_directory read_id_style alignment_parent_directory 
# dataset_name junction_overlap mode report_directory_name ntrim denovoCircMode 
# junction_id_suffix 2>&1 | tee out.log
# https://github.com/lindaszabo/KNIFE/tree/master/circularRNApipeline_Standalone

#########################################################################
# End of parameters
#########################################################################
 
# first have to create directories (if they don't already exist)
#   and change file names and mv them to the right directories

# get current working dir

logfile = WORK_DIR + "/logknifenocomb" + run_id + dataset_name + ".txt"

with open(logfile, 'w') as ff:
    ff.write(WORK_DIR)
    ff.write('\n\n\n')

    
# main directory to be used when running the knife:
# knifedir = "~/gl/circularRNApipeline_Standalone"
#knifedir = "/srv/software/knife/circularRNApipeline_Standalone"
cirpipedir = "/srv/software/knife/circularRNApipeline_Standalone"

copy_tree(cirpipedir, WORK_DIR)

knifedir = WORK_DIR
    
targetdir_list = [knifedir + "/index", knifedir + "/index", knifedir + "/denovo_scripts", knifedir + "/denovo_scripts/index"]
    
# check that there is a directory called circularRNApipeline_Standalone and all the subdirectories; there should be!

if not os.path.isdir(knifedir):
    os.makedirs(knifedir)
    
thisdir = targetdir_list[0]
if not os.path.exists(thisdir):
    os.makedirs(thisdir)

thisdir = targetdir_list[2]
if not os.path.exists(thisdir):
    os.makedirs(thisdir)

thisdir = targetdir_list[3]
if not os.path.exists(thisdir):
    os.makedirs(thisdir)

# Input file names are in an unusual format so they are easy to select when doing a run on
#   seven bridges. They should start in the home directory, as copies, because
#   they are entered as stage inputs.
#   Move them to the directories where KNIFE
#   expects them to be, then change their names.

# make function to do this for each of the four types of files
#  prefix is one of "infilebt1", "infilebt2", "infilefastas", or "infilegtf"
def move_and_rename(prefix, targetdir):
    globpattern = prefix + "*"
    matching_files = glob.glob(globpattern)
    if (len(matching_files)>= 1):
        for thisfile in matching_files:
            fullpatholdfile = WORK_DIR + "/" + thisfile
            fullpathnewfile = targetdir + "/" + re.sub(pattern=prefix, repl="", string= thisfile)
            subprocess.check_call(["mv", fullpatholdfile, fullpathnewfile])
            with open(logfile, 'a') as ff:
                ff.write('mv '+ fullpatholdfile + ' ' + fullpathnewfile + '\n')

#        os.rename(fullpatholdfile, fullpathnewfile)

prefix_list = ["infilebt2", "infilefastas", "infilegtf", "infilebt1"]

for ii in range(4):
    move_and_rename(prefix=prefix_list[ii], targetdir= targetdir_list[ii])

    
# cd into the knife directory
os.chdir(knifedir)

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

# Change to WORK_DIR, then get all files in WORK_DIR/[dataset_name] folder, tar them.


os.chdir(WORK_DIR)
try:
   fullcall = "tar -cvzf " + dataset_name + "knifeoutputdir.tar.gz " + dataset_name 
   with open(logfile, 'a') as ff:
       subprocess.check_call(fullcall, stderr=ff, stdout = ff, shell=True)
except:
   with open(logfile, 'a') as ff:
       ff.write("\nError in tarring the knife output files in the " + dataset_name + " directory\n")

#############################################################################
# Get two report files and tar and zip them
#  Technically looks for all files with names ending in .report.txt
# testData/circReads/combinedReports:
# -rw-r--r--@ 1 awk  staff    12M May 22 00:57 naiveinfSRR1027187_1_report.txt
#
# testData/circReads/reports:
# -rw-r--r--@ 1 awk  staff    12M May 22 00:04 infSRR1027187_1_report.txt
#
# Does not include the directory structure when tarring them
#############################################################################






os.chdir(WORK_DIR)

file_list = []
for root, subFolders, files in os.walk("."):
    for file in files:
        file_list.append(os.path.join(root,file))
        
try:
    text_file_list = filter(lambda x:re.search('report.txt$', x), file_list)
except:
    with open(logfile, 'a') as ff:
        ff.write("\nError in matching report.txt for the two text files\n")

try:
    text_file_list_without_paths = [os.path.basename(x) for x in text_file_list]
    text_file_dirs = [os.path.dirname(x) for x in text_file_list]
except:
    with open(logfile, 'a') as ff:
        ff.write("\nError in getting basenames or dirnames for the two text files\n")

try:
    for ii, thisfilename in enumerate(text_file_list_without_paths):
        if ii==0:
            fullcall = "tar -cvf " + dataset_name + "knifetextfiles" + run_id + ".tar -C "+ text_file_dirs[ii] + " " +  thisfilename
        elif ii>0:
            fullcall = "tar -rvf " + dataset_name + "knifetextfiles" + run_id + ".tar  -C " + text_file_dirs[ii]  +  " " + thisfilename
        subprocess.check_call(fullcall, shell=True)
except:
    with open(logfile, 'a') as ff:
        ff.write("\nError in tarring the two knife text output files in the " + dataset_name + " directory\n")

try:
    subprocess.check_call("gzip " + dataset_name + "knifetextfiles" + run_id + ".tar", shell=True)
except:
    with open(logfile, 'a') as ff:
        ff.write("\nProblem with gzipping.\n")
        
os.chdir(WORK_DIR)




#############################################################################
# Get all files in either circReads/glmReport or circReads/reports or sampleStats/
# zzxx
# tar should unpack files as relative to the output directory
#  so, e.g. at the top level, it will create directories like circReads/glmReports, ...
#############################################################################

wdir = WORK_DIR
datadir = wdir + "/" + dataset_name
os.chdir(datadir)

with open(logfile, 'a') as ff:
    ff.write("\nRecursively listing files in data dir before tarring files in\n")
    ff.write("circReads/glmReport or circReads/reports or sampleStats \n")
    ff.write("datadir is\n" + datadir)
    ff.write('\n\n\n')

with open(logfile, 'a') as ff:
    subprocess.check_call(["ls", "-R"], stdout=ff)

os.chdir(wdir)
    
        
dirs_to_get_files = ['circReads/glmReports','circReads/reports','sampleStats']
full_path_dirs_to_get_files = [datadir + '/' + x for x in dirs_to_get_files]


tempfilename = datadir + "/tempfilelist"


# get names of all files in these directories with paths relative to datadir:
try:
    txtfilelist =[]
    for thisdir in dirs_to_get_files:
        os.chdir(datadir)
        if os.path.isdir(thisdir):
            txtfilelist.extend([os.path.join(thisdir,x) for x in [f for f in os.listdir(thisdir) if os.path.isfile(os.path.join(thisdir,f))] ])
        else:
            os.chdir(datadir)
            with open(logfile, 'a') as ff:
                ff.write("\nNo directory\n" + thisdir + "\n")
                ff.write('\n\n\n')
                subprocess.check_call(["ls", "-R"], stdout=ff)
                ff.write('\n\n\n')
except:
    os.chdir(datadir)
    with open(logfile, 'a') as ff:
        ff.write("\nError when getting the names of the txt files in circReads/glmReport or circReads/reports or sampleStats \n")

# append list of files to log file
with open(logfile, 'a') as ff:
    ff.write('\nList of files that will be tarred:\n')
    ff.write('\n'.join([str(x) for x in txtfilelist]))


os.chdir(wdir)

tarfile = dataset_name + "knifereportfiles.tar"

for ii, thisfile in enumerate(txtfilelist):
    try:
        if ii==0:
            fullcall = "tar -cvf " +  tarfile + " -C " + datadir + " " + thisfile 
        else:
            fullcall = "tar -rvf " +  tarfile + " -C " + datadir + " " + thisfile 
        with open(logfile, 'a') as ff:
            ff.write('\nCall to use for tar:\n')
            ff.write(fullcall)
        subprocess.check_call(fullcall, shell=True)
    except:
        with open(logfile, 'a') as ff:
            ff.write("\nError when tarring the reports output files for call:\n")
            ff.write(fullcall)

os.chdir(wdir)

subprocess.check_call("gzip " + tarfile, shell=True)
            
        
os.chdir(wdir)

#############################################################################
# List some files
#############################################################################



with open(logfile, 'a') as ff:
    ff.write('\n\n\nWriting recursive list of entire working directory.\n\n')

    
with open(logfile, 'a') as ff:
    subprocess.check_call(["ls", "-R"], stdout=ff)
    ff.write('\n\n\n')
    
os.chdir(knifedir)
    
with open(logfile, 'a') as ff:
    ff.write('\n\n\nWriting recursive list of knife directory.\n\n')

    
with open(logfile, 'a') as ff:
    subprocess.check_call(["ls", "-R"], stdout=ff)
    ff.write('\n\n\n')





        
