# /bin/bash 
# 2025-04-14 - in run_compare_session - changed the 'line' arg to 'sessionName' arg
# 2025-06-12 - 
#	on convert changed 'kdl' to 2. to convert with flPrmOut cmdLine, when the flv is unavailable
#	fixed 'loop' logs generation
#	additional cmdLines logs
#
function run_convert_ffmpeg8
{
local action=$1
local set_name=$2	# setX
local csv_file=$3 	# /tmp/1.csv
local line_idx=$4	#  
local prefix=$5	#
local test_folder=$6 # /web/content/shared/tmp/qualityTest/TestBench.11/ff8tests

local ffm=$7
local ffp=$8

#	if [[ -n "${PREFIX}" ]]; then
#		local PREFIXa"-sessionPrefix ${PREFIX}"
#	fi

local convert_folder=${test_folder}/convert

local output_folder=${convert_folder}/${set_name}
local line=$(cat ${csv_file} | head -${line_idx} | tail -1); 
local log_name=$(awk -F'~' '{print $1 "_" $6}' <<< "$line").conv.log
echo "${FUNCNAME[0]}: ACTION:$action"
echo "${FUNCNAME[0]}: SET:$set_name"
echo "${FUNCNAME[0]}: CSV:$csv_file"
echo "${FUNCNAME[0]}: IDX:$line_idx, LINE:$line"
echo "${FUNCNAME[0]}: TEST_FOLDER:$test_folder"
echo "${FUNCNAME[0]}: FFM:$ffm, FFP:$ffp"
echo "${FUNCNAME[0]}: PREFIX:${prefix}"
#return
echo "${FUNCNAME[0]}: PASSED ARGS:$@"
#
	if [[ -n "${prefix}" ]]; then
		local log_name=${output_folder}/${prefix}_${log_name}
	else 
		local log_name=${output_folder}/${log_name}
	fi
	echo "${FUNCNAME[0]}:" /bin/time php test_ffmpeg8.php -action $action -kdl 2 -ffmpegBin $ffm -ffprobeBin $ffp -vmaf 0 -tmpFolder /web/tmp/anatol -line "${line}" -outputFolder ${output_folder} -concurrent 90 -minConcurrent 90 -shared 1 -sessionPrefix "${prefix}" 
	
	IFS=$'\n'
	/bin/time php test_ffmpeg8.php -action $action -kdl 2 -ffmpegBin $ffm -ffprobeBin $ffp -vmaf 0 -tmpFolder /web/tmp/anatol -line "${line}" -outputFolder ${output_folder} -concurrent 90 -minConcurrent 90 -shared 1 -sessionPrefix "${prefix}" 2>&1 | tee ${log_name}
}


#############
#
#
function run_convert_session()
{
	if [[ -z "${TEST_FOLDER}" ]]; then
		local TEST_FOLDER=/web/content/shared/tmp/qualityTest/TestBench.11/ff8tests
	fi
	if [[ -z "${FFM}" ]]; then
		local FFM=${TEST_FOLDER}/ffmpeg8.sh
	fi
	if [[ -z "${FFP}" ]]; then
		local FFP=${TEST_FOLDER}/ffprobe8.sh
	fi

echo "TEST_FOLDER:$TEST_FOLDER"
echo "FFM:$FFM"
echo "FFP:$FFP"
echo "CSV_FILE:${CSV_FILE}"
echo "SET_NAME:${SET_NAME}"
echo "PATH:${PATH}"
echo "PREFIX:${PREFIX}"

local items_per_loop=$1
local num_loops=$2
local initial_item=$3
	if [[ -z "${initial_item}" ]]; then
		local initial_item=0
	fi
echo "ITEMS_PER_LOOP:$items_per_loop"
echo "NUM_LOOPS:$num_loops"
echo "INITIAL_ITEM:$initial_item"

	read -p "Are you sure? (y/n): " confirm
	# Check the user's response
	if [[ "$confirm" == "y" ]]; then
	  echo "User confirmed. Continuing..."
	  # ... code to execute if confirmed ...
	elif [[ "$confirm" == "n" ]]; then
	  echo "User cancelled. Exiting."
	  return 1 # Exit with an error code, indicating cancellation
	else
	  echo "Invalid input. Please enter 'y' or 'n'."
	  # You might want to loop back to the prompt here, or exit.
	  return 1
	fi

local base_loop_name="loop"
	if [[ -n "${PREFIX}" ]]; then
		local base_loop_name="${PREFIX}_${base_loop_name}"
	fi
	for ((loop_idx=0; loop_idx<num_loops; loop_idx++)); do
	  local start_item=$((loop_idx * items_per_loop + initial_item + 1))
	  local end_item=$((start_item + items_per_loop - 1))
	  echo "Loop $loop_idx" > ${TEST_FOLDER}/convert/${SET_NAME}/${base_loop_name}_${loop_idx}.log
	  (
		for ((item=start_item; item<=end_item; item++)); do
		  echo "Loop $loop_idx: Processing item $item"
		  echo "${FUNCNAME[0]}:" run_convert_ffmpeg8 "convert" "${SET_NAME}" "${CSV_FILE}" "${item}" "${PREFIX}" "${TEST_FOLDER}" "${FFM}" "${FFP}" 2>&1 >> ${TEST_FOLDER}/convert/${SET_NAME}/${base_loop_name}_${loop_idx}.log 
		  run_convert_ffmpeg8 "convert" "${SET_NAME}" "${CSV_FILE}" "${item}" "${PREFIX}" "${TEST_FOLDER}" "${FFM}" "${FFP}"
		done
	  ) 2>&1 > /dev/null  < /dev/null & # Run the inner loop in the backgro{und
	done
}

#############
#
#
function run_compare_session()
{
	if [[ -z "${COMPARE_FOLDER}" ]]; then
		local COMPARE_FOLDER=/web/content/shared/tmp/qualityTest/TestBench.11/ff8tests/convert/${SET_NAME}
	fi
	if [[ -z "${FFM}" ]]; then
		local FFM=ffmpeg
	fi
	if [[ -z "${FFP}" ]]; then
		local FFP=ffprobe
	fi
local items_per_loop=$1
local num_loops=$2
local initial_item=$3
local vmafOp=$4

	if [[ -z "${initial_item}" ]]; then
		local initial_item=0
	fi
	if [[ -z "${vmafOp}" ]]; then
		local vmafOp=0
	else
		local vmafOp=1
	fi
# Split PREFIX into array if it contains comma
IFS=',' read -ra PREFIXES <<< "${PREFIX}"

echo "*** ${FUNCNAME[0]} ***"
echo -e "\tCOMPARE_FOLDER:$COMPARE_FOLDER"
echo -e "\tFFM:$FFM"
echo -e "\tFFP:$FFP"
echo -e "\tCSV_FILE:${CSV_FILE}"
echo -e "\tSET_NAME:${SET_NAME}"
echo -e "\tPATH:${PATH}"
echo -e "\tPREFIX:${PREFIX}"
echo -e "\tITEMS_PER_LOOP:$items_per_loop"
echo -e "\tNUM_LOOPS:$num_loops"
echo -e "\tINITIAL_ITEM:$initial_item"
echo -e "\tVMAF:$vmafOp"
	read -p "Are you sure? (y/n): " confirm
# Check the user's response
	if [[ "$confirm" == "y" ]]; then
		echo "User confirmed. Continuing..."
	  # ... code to execute if confirmed ...
	elif [[ "$confirm" == "n" ]]; then
	  echo "User cancelled. Exiting."
	  return 1 # Exit with an error code, indicating cancellation
	else
	  echo "Invalid input. Please enter 'y' or 'n'."
	  # You might want to loop back to the prompt here, or exit.
		return 1
	fi

	for ((loop_idx=0; loop_idx<num_loops; loop_idx++)); do
	  local start_item=$((loop_idx * items_per_loop + initial_item + 1))
	  local end_item=$((start_item + items_per_loop - 1))
	  
	  (
		for ((item=start_item; item<=end_item; item++)); do
		  echo "Loop $loop_idx: Processing item $item"
			local line=$(cat ${CSV_FILE} | head -${item} | tail -1); 
			local line="${line//'//'/'/'}"
			local line="${line//'/web'/'/nvp1-kalt-ovp-content'}"
			
			local sourcePath=$(awk -F'~' '{print $5}' <<< "$line")
			local assetPath=$(awk -F'~' '{print $7}' <<< "$line")
			local sessionName="$(awk -F'~' '{print $1}' <<< "$line")_$(awk -F'~' '{print $6}' <<< "$line")"

			# If we have multiple prefixes, compare them against each other
			if [ ${#PREFIXES[@]} -eq 2 ]; then
				local prefix1="${PREFIXES[0]}"
				local prefix2="${PREFIXES[1]}"
				local log_name="${COMPARE_FOLDER}/compare_${prefix1}_vs_${prefix2}_${sessionName}.log"
				local rendition1="${COMPARE_FOLDER}/${prefix1}_${sessionName}"
				local rendition2="${COMPARE_FOLDER}/${prefix2}_${sessionName}"
				local cmd="php test_ffmpeg8.php -action compareRenditions -vmaf \"${vmafOp}\" -samplesCount 15 -sessionName \"${sessionName}\" -sessionPrefix \"${prefix1}_vs_${prefix2}\" -outputFolder \"$COMPARE_FOLDER\" -source \"${sourcePath}\" -file \"${rendition1}\" -file2 \"${rendition2}\""
				echo "DEV MODE - Command to execute:"
				echo "$cmd > ${log_name}"
				# Uncomment next line for production
				#eval "$cmd" 2>&1 > ${log_name}
				php test_ffmpeg8.php -action compareRenditions -vmaf "${vmafOp}" -samplesCount 15 -sessionName "${sessionName}" -sessionPrefix "${prefix1}_vs_${prefix2}" -outputFolder "$COMPARE_FOLDER" -source "${sourcePath}" -file "${rendition1}" -file2 "${rendition2}" 2>&1 > ${log_name}
			else
				local log_name="${COMPARE_FOLDER}/compare_${PREFIX}_${sessionName}.log"
				local rendition="${COMPARE_FOLDER}/${PREFIX}_${sessionName}"
				local cmd="php test_ffmpeg8.php -action compareRenditions -vmaf \"${vmafOp}\" -samplesCount 15 -sessionName  \"${sessionName}\" -vmaf \"${vmafOp}\" -sessionPrefix \"${PREFIX}\" -outputFolder \"$COMPARE_FOLDER\" -source \"${sourcePath}\" -file \"${assetPath}\" -file2 \"${rendition}\""
				echo "DEV MODE - Command to execute:"
				echo "$cmd > ${log_name}"
				# Uncomment next line for production
				#eval "$cmd" 2>&1 > ${log_name}
                php test_ffmpeg8.php -action compareRenditions -vmaf "${vmafOp}" -samplesCount 15 -sessionName "${sessionName}" -sessionPrefix "${PREFIX}" -outputFolder "$COMPARE_FOLDER" -source "${sourcePath}" -file "${assetPath}" -file2 "${rendition}" 2>&1 > ${log_name}
			fi
		done
	  ) < /dev/null & # Run the inner loop in the background
	done
}

#############
#
#
function run_compare_mediadata()
{
	if [[ -z "${FFM}" ]]; then
		local FFM=ffmpeg6,ffmpeg8
	fi
	if [[ -z "${FFP}" ]]; then
		local FFP=ffprobe6,ffprobe8
	fi

echo "*** ${FUNCNAME[0]} ***"
echo -e "\tFFM:$FFM"
echo -e "\tFFP:$FFP"
echo -e "\tCSV_FILE:${CSV_FILE}"

	read -p "Are you sure? (y/n): " confirm
# Check the user's response
	if [[ "$confirm" == "y" ]]; then
		echo "User confirmed. Continuing..."
	  # ... code to execute if confirmed ...
	elif [[ "$confirm" == "n" ]]; then
	  echo "User cancelled. Exiting."
	  return 1 # Exit with an error code, indicating cancellation
	else
	  echo "Invalid input. Please enter 'y' or 'n'."
	  # You might want to loop back to the prompt here, or exit.
		return 1
	fi
local itemCnt=$(wc -l < ${CSV_FILE})
local sourcePrev=
	for ((item=0; item<itemCnt; item++)); do
		local line=$(cat ${CSV_FILE} | head -${item} | tail -1); 
			local line=$(cat ${CSV_FILE} | head -${item} | tail -1); 
			local line="${line//'//'/'/'}"
			local line="${line//'/web'/'/nvp1-kalt-ovp-content'}"
			
			local sourcePath=$(awk -F'~' '{print $5}' <<< "$line")
			if [[ -z "${sourcePath}" ]]; then
				continue
			fi
			if [[ "${sourcePrev}" == "${sourcePath}" ]]; then 
				continue;
			fi
			local sourcePrev="${sourcePath}"
			local cmd="php test_ffmpeg8.php -action extractMedia -source ${sourcePath} -ffmpegBin ${FFM} -ffprobeBin  ${FFP}"
			echo -e "${cmd}"
			IFS=' ' read -r -a converted_cmd_array <<< "$cmd"
#`eval ${cmd}`
			"${converted_cmd_array[@]}"
	done
}


#############
#run_compare_mediadata "$@"
run_convert_session "$@"
#run_convert_ffmpeg8 "$@"
