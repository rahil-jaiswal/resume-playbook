#!/bin/bash
##########################################
# Author: Rahil Jaiswal                  #
# If any issues or suggestions with the  #
# work. Please contact on following      #
# email address.                         #
# Mail - rajaiswal@protonmail.com        #
##########################################


##Exporting Ansible Plugin Variables
export ANSIBLE_LOG_PATH={log_path}
export ANSIBLE_CALLBACK_PLUGINS={directory_path}
export ANSIBLE_STDOUT_CALLBACK=progression

INPROGRESS_FILE=playbook.inprogress
## Remember to store the extra variables into a seperate file for future use
## Create playbook.inprogress file (If already existing rename it.)

executePlaybook() {

rm -f $INPROGRESS_FILE
touch $INPROGRESS_FILE
ansible-playbook -i $INVEN_FILE $PLAYBOOK
return $?

}

resumePlaybook() {
if [ ! -f $INPROGRESS_FILE ]; then
   echo "No INPROGRESS_FILE found... Try fresh execution of playbook!"
   exit 1
fi
#check for any failed task first
LAST_ENTRY=$(cat $INPROGRESS_FILE | grep "failed$")
if [ "x$LAST_ENTRY" == "x" ]; then
	#check for any already started but not finished tasks
	LAST_ENTRY=$(cat $INPROGRESS_FILE | grep "started$")
	if [ "x$LAST_ENTRY" == "x" ]; then
	   #check for the very last task completed, and resume from there.
	   LAST_ENTRY=$(tail -n 1 $INPROGRESS_FILE)
	fi
fi

##NODE and STATUS Variables arent used yet, but could be used in case of addintional enhacements on execution limition to particular nodes or tags##
NODE=$(echo $LAST_ENTRY | awk -F ':' '{print $1}')
TASK=$(echo $LAST_ENTRY | awk -F ':' '{print $2}' | sed 's/{//g' | sed 's/}//g')
STATUS=$(echo $LAST_ENTRY | awk -F ':' '{print $3}')

echo "Resuming from $TASK ..."
ansible-playbook -i $INVEN_FILE $PLAYBOOK --start-at-task="$TASK"

return $?
}

##main##
RESUME=0
while getopts :f:r args
do
  case $args in
    p)
	PLAYBOOk=`readlink -fq $OPTARG`
	;;
    i)
	INVEN_FILE=`readlink -fq $OPTARG`
	;;
    f)
	RESUME=0
	;;
    r)
	RESUME=1
    ;;
    *)
        usage
        exit 0
    ;;
  esac
done

if [ -f $INPROGRESS_FILE ] && [ $RESUME -ne 1 ]; then
    ans=null
    $ECHO "Found INPROGRESS_FILE, You can either resume it from last task executed or rerun all the tasks again!"
    while [ "$ans" != "n" -a "$ans" != "N" -a "$ans" != "y" -a "$ans" != "Y" ]
    do
        $ECHO "Do you wish to resume the execution [y|Y,n|N] ?"
        read ans
    done
    if [ "$ans" = "n" -o "$ans" = "N" ]; then
       rm -f $INPROGRESS_FILE
       RESUME=0
    else
       RESUME=1
    fi
fi

if [ $RESUME -eq 0 ]; then
   echo "Executing PLAYBOOK from beginning..."
   executePlaybook
else
   echo "Resuming PLAYBOOK execution from last failed/executed task..."
   resumePlaybook
fi
